---
name: mcam-assistant
description: Ingest Mastercam files, NC programs, and engineering instructions; extract tooling and holder data; parse operations; create revisioned NC programs with enriched comments; generate setup sheets; and expose structured manufacturing JSON for downstream plugins.
---

# MCAM Assistant

Use this skill when the user asks to analyze Mastercam/MCAM files, NC programs, tooling lists, holder assemblies, projection lengths, machining operations, setup sheets, or CNC revision workflows.

Prefer the NC-only simple package for first deployments. It produces value from a single program file and optional plain-English notes/photos without requiring CAM extraction.

## First Priority

The NC parser is the first and only implementation priority until it is reliable.

When working on this project:

1. Start with NC parsing behavior.
2. Improve tool, offset, operation, feed, speed, cycle, and comment extraction.
3. Keep `manufacturing-data.json` stable and useful for downstream modules.
4. Add or update tests with real or representative NC programs.
5. Treat setup sheets as a way to verify parser output, not as the main feature.

Do not spend implementation effort on CAM extraction, inventory integrations, report editors, CAD graphics, photo-library automation, minimum projection policies, or other future modules until the NC parser is dependable.

## Workflow

1. Never overwrite the source NC program. Always create a new revision folder or output file.
2. Treat `manufacturing-data.json` as the handoff contract for downstream plugins.
3. Use the CLI when files are available:

```powershell
python C:\Users\tylor\plugins\mcam-assistant\scripts\mcam_assistant_cli.py --mcam <path> --nc <path> --instructions "<plain English>" --out <output-dir>
```

For the simplest NC-only package:

```powershell
python C:\Users\tylor\plugins\mcam-assistant\scripts\mcam_assistant_cli.py --nc <program.nc> --out <package-dir> --part <part-number> --machine "<machine>" --fixture "<fixture>"
```

4. If a Mastercam file is proprietary or binary and cannot be inspected locally, report that limitation clearly. Preserve file metadata and parse any readable companion data rather than inventing tooling details.
5. Prefer structured extraction from JSON, XML, ZIP-contained XML/JSON/TXT, or NC comments before using heuristics.

## Output Contract

The pipeline emits JSON with:

- `job`: source files, timestamps, units, and warnings.
- `job.visual_references`: photo references A-H with description, file path, and status.
- `job` and setup reports include ASCII-style setup visualization when fixture/comment context supports it, including OP1/OP2 side-by-side Y-axis flip views for vise jobs.
- `tooling`: tools, holders, assemblies, projection lengths, sources, and confidence.
- `operations`: parsed NC operations with tool, work offset, spindle, feed, comments, and block ranges.
- `instructions`: plain-English instructions converted to structured notes/actions/constraints.
- `revisions`: immutable revision records and output artifacts.
- `extension_points`: available adapter families for future plugins.

## Extension Points

Future modules should register adapters through `PluginRegistry` rather than changing `ManufacturingPipeline`. Planned adapter families include Alphacam, routers, lathes, waterjets, PR160P4 trunnions, Haas controls, inventory systems, and report editors.
