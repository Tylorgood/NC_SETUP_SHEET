from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from ..models import HolderAssembly, Tool
from ..utils import read_text_lossy


class MastercamExtractor:
    name = "mastercam-v0"
    family = "cam_extractor"

    def extract(self, paths: list[Path]) -> dict[str, Any]:
        tools: list[Tool] = []
        holders: list[HolderAssembly] = []
        warnings: list[str] = []
        raw: dict[str, Any] = {}

        for path in paths:
            suffix = path.suffix.lower()
            try:
                if suffix == ".json":
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    raw[str(path)] = payload
                    self._from_mapping(payload, str(path), tools, holders)
                elif suffix in {".xml", ".mcam-content"}:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    raw[str(path)] = {"text_preview": text[:4000]}
                    self._from_xml(text, str(path), tools, holders)
                elif suffix == ".zip":
                    self._from_zip(path, tools, holders, raw, warnings)
                else:
                    text = read_text_lossy(path, limit=250000)
                    raw[str(path)] = {"text_preview": text[:4000]}
                    self._from_text(text, str(path), tools, holders)
                    if self._looks_binary(path, text):
                        warnings.append(
                            f"{path.name} appears proprietary or binary; v0.1 captured metadata and readable strings only."
                        )
            except Exception as exc:
                warnings.append(f"Could not extract {path}: {exc}")

        return {
            "tools": [tool.__dict__ for tool in tools],
            "holder_assemblies": [holder.__dict__ for holder in holders],
            "warnings": warnings,
            "raw_sources": raw,
        }

    def _from_mapping(self, payload: dict[str, Any], source: str, tools: list[Tool], holders: list[HolderAssembly]) -> None:
        for item in payload.get("tools", payload.get("tooling", [])):
            tools.append(
                Tool(
                    number=_int(item.get("number") or item.get("tool_number") or item.get("t")),
                    name=item.get("name") or item.get("description"),
                    diameter=_float(item.get("diameter") or item.get("dia")),
                    corner_radius=_float(item.get("corner_radius") or item.get("cr")),
                    flute_length=_float(item.get("flute_length")),
                    overall_length=_float(item.get("overall_length")),
                    units=item.get("units"),
                    source=source,
                    confidence=0.95,
                )
            )
        for item in payload.get("holders", payload.get("holder_assemblies", [])):
            holders.append(
                HolderAssembly(
                    tool_number=_int(item.get("tool_number") or item.get("tool")),
                    holder_id=item.get("holder_id") or item.get("id") or item.get("name"),
                    components=list(item.get("components", [])),
                    projection_length=_float(item.get("projection_length") or item.get("projection")),
                    projection_units=item.get("projection_units") or item.get("units"),
                    source=source,
                    confidence=0.95,
                )
            )

    def _from_xml(self, text: str, source: str, tools: list[Tool], holders: list[HolderAssembly]) -> None:
        root = ET.fromstring(text)
        for node in root.iter():
            tag = node.tag.lower()
            attrs = {key.lower(): value for key, value in node.attrib.items()}
            if "tool" in tag:
                tools.append(
                    Tool(
                        number=_int(attrs.get("number") or attrs.get("id") or attrs.get("t")),
                        name=attrs.get("name") or (node.text or "").strip() or None,
                        diameter=_float(attrs.get("diameter") or attrs.get("dia")),
                        units=attrs.get("units"),
                        source=source,
                        confidence=0.85,
                    )
                )
            if "holder" in tag or "assembly" in tag:
                holders.append(
                    HolderAssembly(
                        tool_number=_int(attrs.get("tool") or attrs.get("tool_number")),
                        holder_id=attrs.get("id") or attrs.get("name"),
                        projection_length=_float(attrs.get("projection") or attrs.get("projection_length")),
                        projection_units=attrs.get("units"),
                        source=source,
                        confidence=0.85,
                    )
                )

    def _from_text(self, text: str, source: str, tools: list[Tool], holders: list[HolderAssembly]) -> None:
        for match in re.finditer(r"\bT(?:OOL)?\s*#?\s*(\d+)\b[^\n\r]*(?:DIA(?:METER)?\s*[:=]?\s*([0-9.]+))?", text, re.I):
            tools.append(Tool(number=int(match.group(1)), diameter=_float(match.group(2)), source=source, confidence=0.55))
        for match in re.finditer(r"\b(?:HOLDER|ASSEMBLY)\s*[:=]?\s*([A-Z0-9_.-]+).*?(?:PROJ(?:ECTION)?\s*[:=]?\s*([0-9.]+))?", text, re.I):
            holders.append(
                HolderAssembly(
                    holder_id=match.group(1),
                    projection_length=_float(match.group(2)),
                    source=source,
                    confidence=0.55,
                )
            )

    def _from_zip(self, path: Path, tools: list[Tool], holders: list[HolderAssembly], raw: dict[str, Any], warnings: list[str]) -> None:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.lower().endswith((".json", ".xml", ".txt", ".nc")):
                    continue
                text = archive.read(name).decode("utf-8", errors="ignore")
                raw[f"{path}!{name}"] = {"text_preview": text[:4000]}
                if name.lower().endswith(".json"):
                    self._from_mapping(json.loads(text), f"{path}!{name}", tools, holders)
                elif name.lower().endswith(".xml"):
                    self._from_xml(text, f"{path}!{name}", tools, holders)
                else:
                    self._from_text(text, f"{path}!{name}", tools, holders)

    def _looks_binary(self, path: Path, text: str) -> bool:
        return path.suffix.lower() in {".mcam", ".mcamx", ".mcx", ".mcx-5", ".mcx-6", ".mcx-7", ".mcx-8", ".mcx-9"} or "\x00" in text[:1000]


def _int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None


def _float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None
