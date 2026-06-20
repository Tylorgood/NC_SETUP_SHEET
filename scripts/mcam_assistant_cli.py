from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mcam_assistant import ManufacturingPipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MCAM Assistant v0.1")
    parser.add_argument("--mcam", action="append", default=[], help="Mastercam/CAM source file. Repeat for companion files.")
    parser.add_argument("--nc", required=True, help="NC program to parse. This file is never overwritten.")
    parser.add_argument("--instructions", default="", help="Plain-English engineering instructions.")
    parser.add_argument("--instructions-file", help="Text file containing engineering instructions.")
    parser.add_argument("--out", required=True, help="Output directory for immutable revisions.")
    parser.add_argument("--simple", action="store_true", help="Create a super-simple NC-only setup package.")
    parser.add_argument("--part", help="Part number/name for the setup sheet.")
    parser.add_argument("--machine", help="Machine name, such as Haas VF4.")
    parser.add_argument("--fixture", help="Fixture description, such as 6 inch Kurt vise.")
    parser.add_argument("--fixture-reference", help="Visual reference label for the fixture, such as Photo H.")
    parser.add_argument("--setup-note", action="append", default=[], help="Setup note. Repeat for multiple notes.")
    parser.add_argument("--photo", action="append", default=[], help="Photo reference as LABEL|Description|optional-path.")
    args = parser.parse_args(argv)

    nc_path = Path(args.nc).expanduser().resolve()
    mcam_paths = [Path(item).expanduser().resolve() for item in args.mcam]
    output_root = Path(args.out).expanduser().resolve()

    if not nc_path.exists():
        parser.error(f"NC program not found: {nc_path}")
    for path in mcam_paths:
        if not path.exists():
            parser.error(f"CAM source not found: {path}")

    instructions = args.instructions
    if args.instructions_file:
        instructions += "\n" + Path(args.instructions_file).read_text(encoding="utf-8")

    metadata = {
        "part": args.part,
        "machine": args.machine,
        "fixture": args.fixture,
        "fixture_reference": args.fixture_reference,
        "setup_notes": args.setup_note,
    }
    photo_refs = [_parse_photo_ref(item) for item in args.photo]
    pipeline = ManufacturingPipeline()
    if args.simple or not mcam_paths:
        result = pipeline.run_nc_only(nc_path, output_root, instructions.strip(), metadata, photo_refs)
    else:
        result = pipeline.run(mcam_paths, nc_path, instructions.strip(), output_root, metadata, photo_refs)
    print(json.dumps({"revision_id": result["revision_id"], "revision_dir": result["revision_dir"], "artifacts": result["artifacts"]}, indent=2))
    return 0


def _parse_photo_ref(value: str) -> dict:
    parts = [part.strip() for part in value.split("|", 2)]
    return {
        "label": parts[0] if len(parts) > 0 else "",
        "description": parts[1] if len(parts) > 1 else "",
        "path": parts[2] if len(parts) > 2 else "",
    }


if __name__ == "__main__":
    sys.exit(main())
