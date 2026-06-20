from __future__ import annotations

import re
from pathlib import Path

from ..models import Operation


class GenericFanucNcParser:
    name = "generic-fanuc-v0"
    family = "nc_parser"

    def parse(self, path: Path) -> tuple[list[Operation], list[str]]:
        operations: list[Operation] = []
        warnings: list[str] = []
        current: Operation | None = None
        sequence = 0
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

        for idx, line in enumerate(lines, start=1):
            comment_texts = re.findall(r"\((.*?)\)", line)
            tool_change = re.search(r"\bT\s*(\d+)\s*M0?6\b|\bT\s*(\d+)\b.*\bM0?6\b", line, re.I)
            op_hint = self._operation_hint(comment_texts)

            if tool_change and current and current.tool_number is None and current.motion_blocks == 0:
                current.tool_number = _first_int(tool_change.groups())
                current.comments.extend(comment_texts)
            elif tool_change or op_hint:
                if current:
                    current.end_line = idx - 1
                    operations.append(current)
                sequence += 1
                tool_number = _first_int(tool_change.groups()) if tool_change else None
                current = Operation(
                    sequence=sequence,
                    name=op_hint or f"Operation {sequence}",
                    tool_number=tool_number,
                    comments=comment_texts,
                    start_line=idx,
                )
            elif current:
                current.comments.extend(comment_texts)

            if current:
                tool_ref = re.search(r"\bT\s*(\d+)\b", line, re.I)
                work_offset = re.search(r"\bG5[4-9]\b|\bG54\.1\s*P\d+\b", line, re.I)
                spindle = re.search(r"\bS\s*(\d+)\b", line, re.I)
                feed = re.search(r"\bF\s*([0-9.]+)\b", line, re.I)
                motion = re.search(r"\bG0?[0123]\b", line, re.I)
                current.tool_number = current.tool_number or (_first_int(tool_ref.groups()) if tool_ref else None)
                current.work_offset = current.work_offset or (work_offset.group(0).upper().replace(" ", "") if work_offset else None)
                current.spindle_rpm = current.spindle_rpm or (_first_int(spindle.groups()) if spindle else None)
                current.feed_rate = current.feed_rate or (_float(feed.group(1)) if feed else None)
                current.motion_blocks += 1 if motion else 0

        if current:
            current.end_line = len(lines)
            operations.append(current)

        if not operations:
            warnings.append("No tool-change operations found; NC file may use a non-Fanuc dialect or subprogram-only format.")
        return operations, warnings

    def _operation_hint(self, comments: list[str]) -> str | None:
        for comment in comments:
            cleaned = comment.strip()
            if not cleaned or cleaned.startswith("=") or re.match(r"^T\s*\d+\s*-", cleaned, re.I):
                continue
            if re.search(r"\b(OP|OPERATION|FACE|DRILL|POCKET|CONTOUR|FINISH|ROUGH)\b", cleaned, re.I):
                return cleaned
        return None


class RevisionedNcEmitter:
    name = "revisioned-nc-v0"
    family = "nc_emitter"

    def emit(self, source_path: Path, output_path: Path, operations: list[Operation], instruction_summary: str, revision_id: str) -> None:
        original = source_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        header = [
            f"(MCAM ASSISTANT REVISION {revision_id})",
            f"(SOURCE PROGRAM: {source_path.name})",
            f"(REVISION NOTE: {instruction_summary or 'Structured manufacturing data enriched.'})",
            "(ORIGINAL FILE WAS NOT OVERWRITTEN)",
        ]
        op_comments = []
        for op in operations:
            tool = f"T{op.tool_number}" if op.tool_number is not None else "T?"
            offset = op.work_offset or "WCS?"
            op_comments.append(f"(MCAM OP {op.sequence}: {op.name} | {tool} | {offset} | LINES {op.start_line}-{op.end_line})")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(header + op_comments + original) + "\n", encoding="utf-8")


def _first_int(values: tuple[str | None, ...]) -> int | None:
    for value in values:
        if value:
            return int(value)
    return None


def _float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
