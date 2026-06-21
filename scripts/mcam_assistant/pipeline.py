from __future__ import annotations

import shutil
from pathlib import Path

from .adapters.instructions import PlainEnglishInstructionParser
from .adapters.mcam import MastercamExtractor
from .adapters.nc import GenericFanucNcParser, RevisionedNcEmitter
from .adapters.reports import SetupSheetReportGenerator
from .models import ManufacturingData, Tool, path_metadata, utc_now
from .registry import PluginRegistry
from .revisions import FileRevisionStore
from .utils import detect_format, sha256_file, write_json


class ManufacturingPipeline:
    def __init__(self, registry: PluginRegistry | None = None) -> None:
        self.registry = registry or default_registry()

    def run(
        self,
        mcam_paths: list[Path],
        nc_path: Path,
        instructions: str,
        output_root: Path,
        job_metadata: dict | None = None,
        photo_refs: list[dict] | None = None,
        simple_package: bool = False,
    ) -> dict:
        cam_extractor: MastercamExtractor = self.registry.first("cam_extractor")  # type: ignore[assignment]
        nc_parser: GenericFanucNcParser = self.registry.first("nc_parser")  # type: ignore[assignment]
        instruction_parser: PlainEnglishInstructionParser = self.registry.first("instruction_parser")  # type: ignore[assignment]
        emitter: RevisionedNcEmitter = self.registry.first("nc_emitter")  # type: ignore[assignment]
        reporter: SetupSheetReportGenerator = self.registry.first("report_generator")  # type: ignore[assignment]
        revision_store: FileRevisionStore = self.registry.first("revision_store")  # type: ignore[assignment]

        source_files = [
            path_metadata(nc_path, "nc_program", sha256_file(nc_path), detect_format(nc_path)).__dict__
        ]
        for path in mcam_paths:
            source_files.append(path_metadata(path, "cam_source", sha256_file(path), detect_format(path)).__dict__)

        tooling = cam_extractor.extract(mcam_paths) if mcam_paths else {"tools": [], "holder_assemblies": [], "warnings": [], "raw_sources": {}}
        nc_text = nc_path.read_text(encoding="utf-8", errors="ignore")
        operations, nc_warnings = nc_parser.parse(nc_path)
        if not tooling.get("tools"):
            tooling["tools"] = [tool.__dict__ for tool in _derive_tools_from_nc_operations(operations)]
        tooling_warnings = tooling.get("warnings", [])
        _apply_tap_drill_corrections(tooling["tools"], operations, nc_text, tooling_warnings)
        _add_tool_tracking_placeholders(tooling["tools"], operations, nc_path.stem)
        parsed_instructions = instruction_parser.parse(instructions)
        revision_id, revision_dir = revision_store.next_revision_dir(output_root)
        revised_nc = revision_dir / f"{nc_path.stem}.{revision_id}{nc_path.suffix or '.nc'}"
        summary = "; ".join(parsed_instructions.actions[:3] or parsed_instructions.notes[:1])[:240]
        emitter.emit(nc_path, revised_nc, operations, summary, revision_id)
        photos_dir = revision_dir / "Photos"
        visual_references = _prepare_visual_references(photo_refs or [], photos_dir, simple_package)
        metadata = _build_job_metadata(nc_path, operations, job_metadata or {}, simple_package, nc_text)

        provisional = ManufacturingData(
            schema_version="mcam-assistant.manufacturing-data.v0.1",
            created_at=utc_now(),
            job={
                **metadata,
                "source_files": source_files,
                "warnings": tooling.get("warnings", []) + nc_warnings,
                "never_overwrite_originals": True,
                "visual_references": visual_references,
            },
            tooling={key: value for key, value in tooling.items() if key != "raw_sources"},
            operations=operations,
            instructions=parsed_instructions,
            revisions=[],
            extension_points={
                "registered_adapters": self.registry.describe(),
                "future_modules": [
                    "alphacam",
                    "routers",
                    "lathes",
                    "waterjets",
                    "pr160p4-trunnion",
                    "haas-controls",
                    "inventory-systems",
                    "report-editors",
                ],
            },
        )
        report_artifacts: dict[str, str] = {}
        artifacts = {"nc": str(revised_nc)}
        record = revision_store.create_record(revision_id, nc_path, revised_nc, summary or "MCAM Assistant enriched comments.", artifacts)
        history = revision_store.append(output_root, record)
        provisional.revisions = history
        report_artifacts = reporter.generate(provisional.to_dict(), revision_dir)
        artifacts.update(report_artifacts)
        record.artifacts = artifacts
        revision_store.append(output_root, record, replace=True)
        provisional.revisions = revision_store.load_history(output_root)

        data_path = revision_dir / "manufacturing-data.json"
        payload = provisional.to_dict()
        payload["tooling"]["raw_sources"] = tooling.get("raw_sources", {})
        write_json(data_path, payload)
        return {"revision_id": revision_id, "revision_dir": str(revision_dir), "data": payload, "artifacts": {**artifacts, "json": str(data_path)}}

    def run_nc_only(
        self,
        nc_path: Path,
        output_root: Path,
        instructions: str = "",
        job_metadata: dict | None = None,
        photo_refs: list[dict] | None = None,
    ) -> dict:
        return self.run(
            [],
            nc_path,
            instructions,
            output_root,
            job_metadata=job_metadata,
            photo_refs=photo_refs,
            simple_package=True,
        )


def _derive_tools_from_nc_operations(operations: list) -> list[Tool]:
    tools: dict[int, Tool] = {}
    for op in operations:
        for comment in op.comments:
            parsed = _parse_tool_list_comment(comment)
            if parsed and parsed[0] not in tools:
                number, name, diameter = parsed
                tools[number] = Tool(
                    number=number,
                    name=name,
                    diameter=diameter,
                    source="nc_program_tool_list",
                    confidence=0.8,
                )
        if op.tool_number is None or op.tool_number in tools:
            continue
        name = _best_tool_name(op)
        tools[op.tool_number] = Tool(
            number=op.tool_number,
            name=name,
            source="nc_program",
            confidence=0.65 if name else 0.45,
        )
    return [tools[key] for key in sorted(tools)]


def _apply_tap_drill_corrections(tools: list[dict], operations: list, nc_text: str, warnings: list[str]) -> None:
    comments = (" ".join(comment for op in operations for comment in op.comments) + " " + nc_text).upper()
    has_3_8_16_tap = "3/8\"-16" in comments or "3/8-16" in comments
    if not has_3_8_16_tap:
        return
    drill_tool = next((tool for tool in tools if tool.get("number") == 3), None)
    if not drill_tool:
        return
    name = str(drill_tool.get("name") or "")
    original_name = name
    original_diameter = drill_tool.get("diameter")
    drill_tool["diameter"] = 0.3125
    drill_tool["name"] = "5/16 DRILL (.3125) - TAP DRILL FOR 3/8-16"
    drill_tool["source"] = "nc_program_tap_drill_correction"
    drill_tool["confidence"] = 0.9
    for op in operations:
        op.name = _correct_3_8_16_drill_text(op.name)
        op.comments = [_correct_3_8_16_drill_text(comment) for comment in op.comments]
    warnings.append(
        f"Corrected T3 tap drill for 3/8-16 from '{original_name}' diameter {original_diameter} to 0.3125."
    )


def _add_tool_tracking_placeholders(tools: list[dict], operations: list, program_name: str) -> None:
    op_tools = {op.tool_number for op in operations if op.tool_number is not None}
    for tool in tools:
        number = tool.get("number")
        if number is None:
            continue
        family = _tool_family(str(tool.get("name") or ""))
        tool.setdefault("internal_id", _tool_internal_id(number, family))
        tool.setdefault("serial_number", "TOOL SERIAL NEEDED")
        tool.setdefault("vendor", "VENDOR NEEDED")
        tool.setdefault("vendor_part_number", "PART NUMBER NEEDED")
        tool.setdefault("holder_id", f"H{10000 + int(number):05d}")
        tool.setdefault("holder_location", _location_placeholder("C", "holder"))
        tool.setdefault("tool_location", _location_placeholder("C", "tool"))
        tool.setdefault("replacement_location", _location_placeholder("C", "replacement"))
        tool.setdefault("photo", "PHOTO NEEDED")
        tool.setdefault("catalog_image", "CATALOG IMAGE NEEDED")
        tool.setdefault("programs_used", [program_name] if number in op_tools else [])
        tool.setdefault("machines", ["MACHINE NEEDED"])
        min_projection = _minimum_projection_for_family(family)
        tool.setdefault("tool_family", family)
        tool.setdefault("stickout_actual_in", "MEASURE AT SETUP")
        tool.setdefault("minimum_projection_in", min_projection)
        tool.setdefault("projection_status", "REVIEW - ACTUAL STICKOUT NEEDED")


def _location_placeholder(area: str, label: str) -> str:
    return f"{area}-CAB??-D??-R??-C??-B?? ({label.upper()} LOCATION NEEDED)"


def _tool_family(name: str) -> str:
    upper = name.upper()
    if "FACE MILL" in upper:
        return "face_mill"
    if "END MILL" in upper:
        return "end_mill"
    if "DRILL" in upper:
        return "drill"
    if "TAP" in upper:
        return "tap"
    return "unknown"


def _tool_internal_id(number: int, family: str) -> str:
    family_base = {
        "end_mill": 20000,
        "drill": 50000,
        "tap": 60000,
        "face_mill": 80000,
    }.get(family, 90000)
    return f"M{family_base + int(number):05d}"


def _minimum_projection_for_family(family: str) -> float | str:
    rules = {
        "face_mill": 1.25,
        "end_mill": 1.75,
        "drill": 1.5,
        "tap": 1.25,
    }
    return rules.get(family, "RULE NEEDED")


def _correct_3_8_16_drill_text(value: str) -> str:
    import re

    corrected = re.sub(r"#29\s+DRILL\s*\(\s*\.376\"?\s*DIA\s*\)?", "5/16 DRILL (.3125 DIA)", value, flags=re.I)
    corrected = re.sub(r"#29\s+DRILL\s*-\s*PREP\s+DRILL\s+\.376\"?", "5/16 DRILL (.3125) - TAP DRILL", corrected, flags=re.I)
    corrected = re.sub(r"#29\s+DRILL", "5/16 DRILL (.3125)", corrected, flags=re.I)
    corrected = re.sub(r"\.376\"?\s*DIA", ".3125 DIA", corrected, flags=re.I)
    corrected = re.sub(r"PREP DRILL\s+\.376\"?", "TAP DRILL .3125", corrected, flags=re.I)
    return " ".join(corrected.split())


def _parse_tool_list_comment(comment: str) -> tuple[int, str, float | None] | None:
    import re

    cleaned = " ".join(comment.strip().split())
    match = re.match(r"^T\s*(\d+)\s*-\s*(.+)$", cleaned, re.I)
    if not match:
        return None
    name = match.group(2).strip(" -")
    diameter = _parse_tool_diameter(name)
    return int(match.group(1)), name, diameter


def _parse_tool_diameter(name: str) -> float | None:
    import re

    decimal = re.search(r"(?<![#A-Za-z0-9])([0-9]*\.[0-9]+)\s*(?:\"|IN)?", name, re.I)
    if decimal:
        return float(decimal.group(1))
    fraction = re.search(r"\b([0-9]+)\s*/\s*([0-9]+)\s*(?:\"|IN)?", name, re.I)
    if fraction and int(fraction.group(2)) != 0:
        return int(fraction.group(1)) / int(fraction.group(2))
    whole = re.search(r"\b([0-9]+)\s*(?:\"|IN)\s*(?:FACE MILL|END MILL|MILL|CUTTER)", name, re.I)
    if whole:
        return float(whole.group(1))
    return None


def _best_tool_name(op) -> str | None:
    for comment in op.comments:
        cleaned = " ".join(comment.replace(":", " ").split())
        if cleaned and not cleaned.upper().startswith(("OP", "OPERATION")):
            return cleaned
    if op.name and not op.name.lower().startswith("operation "):
        return op.name
    return None


def _build_job_metadata(nc_path: Path, operations: list, supplied: dict, simple_package: bool, nc_text: str) -> dict:
    work_offsets = sorted({op.work_offset for op in operations if op.work_offset})
    fixture = supplied.get("fixture") or _infer_fixture(nc_text)
    return {
        "package_mode": "nc-only-simple" if simple_package else "cam-plus-nc",
        "part": supplied.get("part") or nc_path.stem,
        "program": supplied.get("program") or nc_path.name,
        "machine": supplied.get("machine") or "",
        "fixture": fixture,
        "fixture_reference": supplied.get("fixture_reference") or "",
        "work_offsets": work_offsets,
        "estimated_cycle_time": supplied.get("cycle_time") or "",
        "setup_notes": supplied.get("setup_notes", []),
        "setup_context": _extract_setup_context(nc_text),
        "required_items": _required_setup_items(fixture),
        "location_serial_system": _location_serial_system(),
    }


def _location_serial_system() -> dict:
    return {
        "format": "AREA-CAB##-D##-R##-C##-B##",
        "example": "C-CAB02-D04-R01-C03-B02",
        "areas": [
            {"prefix": "R", "name": "Router area"},
            {"prefix": "L", "name": "Lathe area"},
            {"prefix": "M", "name": "Mill area"},
            {"prefix": "C", "name": "Tool crib / shared storage"},
        ],
        "fields": [
            {"code": "CAB##", "name": "Cabinet number"},
            {"code": "D##", "name": "Drawer number"},
            {"code": "R##", "name": "Row inside drawer"},
            {"code": "C##", "name": "Column inside drawer"},
            {"code": "B##", "name": "Bin, cup, slot, or pocket"},
        ],
    }


def _required_setup_items(fixture: str) -> list[dict]:
    items = []
    if "VISE" in fixture.upper() or "VICE" in fixture.upper():
        items.extend(
            [
                {
                    "item": "Kurt vise jaws",
                    "asset_id": "V-SERIAL NEEDED",
                    "location": _location_placeholder("M", "jaw storage"),
                    "photo": "PHOTO NEEDED",
                    "notes": "Confirm correct jaws, stop, and parallels before setup.",
                },
                {
                    "item": "Vise stop",
                    "asset_id": "V-STOP ID NEEDED",
                    "location": _location_placeholder("M", "stop storage"),
                    "photo": "PHOTO NEEDED",
                    "notes": "Verify stop location matches G54/G55 sketch.",
                },
                {
                    "item": "Parallels / support",
                    "asset_id": "SUPPORT ID NEEDED",
                    "location": _location_placeholder("M", "parallel storage"),
                    "photo": "PHOTO NEEDED",
                    "notes": "Verify stock protrusion and clamp clearance.",
                },
            ]
        )
    return items


def _infer_fixture(nc_text: str) -> str:
    import re

    fixture = re.search(r"FIXTURE\s*:\s*([^)\r\n]+)", nc_text, re.I)
    if fixture:
        return " ".join(fixture.group(1).strip().split())
    if "VISE" in nc_text.upper():
        return "Vise"
    if "VICE" in nc_text.upper():
        return "Vice"
    return ""


def _extract_setup_context(nc_text: str) -> str:
    lines = []
    for line in nc_text.splitlines()[:80]:
        upper = line.upper()
        if any(key in upper for key in ["FIXTURE", "VISE", "VICE", "G54", "G55", "STOCK", "ORIENTATION", "BACK JAW", "HOLE"]):
            lines.append(line.strip())
    return "\n".join(lines[:20])


def _prepare_visual_references(photo_refs: list[dict], photos_dir: Path, include_defaults: bool) -> list[dict]:
    defaults = [
        ("A", "Raw Stock"),
        ("B", "Fixture Assembly"),
        ("C", "Vise Stop Location"),
        ("D", "G54 Location"),
        ("E", "Tool Layout"),
        ("F", "Critical Clamp Locations"),
        ("G", "First Article Inspection Points"),
        ("H", "Overall Setup"),
    ]
    refs = {label: {"label": label, "description": description, "file": "", "status": "needed"} for label, description in defaults} if include_defaults else {}
    for item in photo_refs:
        label = str(item.get("label") or "").strip().upper()
        if not label:
            continue
        description = str(item.get("description") or refs.get(label, {}).get("description") or "").strip()
        source = Path(str(item.get("path") or "")).expanduser() if item.get("path") else None
        file_value = ""
        status = "referenced"
        if source and source.exists():
            photos_dir.mkdir(parents=True, exist_ok=True)
            target = photos_dir / f"{label}_{_safe_name(description or source.stem)}{source.suffix}"
            shutil.copy2(source, target)
            file_value = str(target)
            status = "attached"
        elif source:
            file_value = str(source)
            status = "missing"
        refs[label] = {"label": label, "description": description, "file": file_value, "status": status}
    return [refs[key] for key in sorted(refs)]


def _safe_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.strip())
    return "_".join(part for part in cleaned.split("_") if part) or "Photo"


def default_registry() -> PluginRegistry:
    registry = PluginRegistry()
    registry.register(MastercamExtractor())
    registry.register(GenericFanucNcParser())
    registry.register(PlainEnglishInstructionParser())
    registry.register(RevisionedNcEmitter())
    registry.register(SetupSheetReportGenerator())
    registry.register(FileRevisionStore())
    return registry
