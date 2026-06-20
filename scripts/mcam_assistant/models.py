from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SourceFile:
    role: str
    path: str
    size_bytes: int
    sha256: str
    detected_format: str


@dataclass
class Tool:
    number: int | None = None
    name: str | None = None
    diameter: float | None = None
    corner_radius: float | None = None
    flute_length: float | None = None
    overall_length: float | None = None
    units: str | None = None
    source: str | None = None
    confidence: float = 0.5


@dataclass
class HolderAssembly:
    tool_number: int | None = None
    holder_id: str | None = None
    components: list[str] = field(default_factory=list)
    projection_length: float | None = None
    projection_units: str | None = None
    source: str | None = None
    confidence: float = 0.5


@dataclass
class Operation:
    sequence: int
    name: str
    tool_number: int | None = None
    work_offset: str | None = None
    spindle_rpm: int | None = None
    feed_rate: float | None = None
    comments: list[str] = field(default_factory=list)
    start_line: int | None = None
    end_line: int | None = None
    motion_blocks: int = 0


@dataclass
class ParsedInstructions:
    raw: str
    notes: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    machines: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)


@dataclass
class RevisionRecord:
    revision_id: str
    created_at: str
    parent_program: str
    output_program: str
    summary: str
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass
class ManufacturingData:
    schema_version: str
    created_at: str
    job: dict[str, Any]
    tooling: dict[str, Any]
    operations: list[Operation]
    instructions: ParsedInstructions
    revisions: list[RevisionRecord]
    extension_points: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def path_metadata(path: Path, role: str, sha256: str, detected_format: str) -> SourceFile:
    stat = path.stat()
    return SourceFile(
        role=role,
        path=str(path),
        size_bytes=stat.st_size,
        sha256=sha256,
        detected_format=detected_format,
    )
