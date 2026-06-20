from __future__ import annotations

import json
from pathlib import Path

from .models import RevisionRecord, utc_now


class FileRevisionStore:
    name = "file-revision-store-v0"
    family = "revision_store"

    def next_revision_dir(self, output_root: Path) -> tuple[str, Path]:
        output_root.mkdir(parents=True, exist_ok=True)
        existing = sorted(path.name for path in output_root.glob("rev-*") if path.is_dir())
        next_num = len(existing) + 1
        revision_id = f"rev-{next_num:03d}"
        revision_dir = output_root / revision_id
        while revision_dir.exists():
            next_num += 1
            revision_id = f"rev-{next_num:03d}"
            revision_dir = output_root / revision_id
        revision_dir.mkdir(parents=True)
        return revision_id, revision_dir

    def load_history(self, output_root: Path) -> list[RevisionRecord]:
        history_path = output_root / "revision-history.json"
        if not history_path.exists():
            return []
        payload = json.loads(history_path.read_text(encoding="utf-8"))
        return [RevisionRecord(**item) for item in payload]

    def append(self, output_root: Path, record: RevisionRecord, replace: bool = False) -> list[RevisionRecord]:
        history = self.load_history(output_root)
        if replace:
            history = [item for item in history if item.revision_id != record.revision_id]
        history.append(record)
        history_path = output_root / "revision-history.json"
        history_path.write_text(json.dumps([item.__dict__ for item in history], indent=2), encoding="utf-8")
        return history

    def create_record(self, revision_id: str, parent_program: Path, output_program: Path, summary: str, artifacts: dict[str, str]) -> RevisionRecord:
        return RevisionRecord(
            revision_id=revision_id,
            created_at=utc_now(),
            parent_program=str(parent_program),
            output_program=str(output_program),
            summary=summary,
            artifacts=artifacts,
        )
