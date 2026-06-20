************TODO*************

1. DASHBOARD (VISUAL MANGEMENT OF THE TOOL)
2. SHAREPOINT INTEGRATION (ROBUST FUNCTIONALITY)



# MCAM Assistant v0.1

MCAM Assistant is a local Codex plugin scaffold for CNC manufacturing workflows. It ingests Mastercam-adjacent files, NC programs, and engineering instructions, then produces structured JSON, a revisioned NC program with enriched comments, and setup sheets in HTML, PDF, and Excel-compatible XLSX formats.

The best v0.1 path is the simple NC-only setup package: parse the program, extract tools/offsets/operations, add plain-English setup notes, and organize real shop photos by reference label.

## Project Priority

The first and only core priority is a reliable NC parsing tool.

Every development session should start with the NC parser and ask:

- Can it correctly read real NC programs?
- Can it identify tools, offsets, operations, feeds, speeds, comments, cycles, and revisions?
- Can it produce dependable structured JSON that downstream features can trust?
- Can the parser pass tests against known sample and golden programs?

Do not prioritize CAM extraction, inventory systems, report editors, CAD renders, photo databases, tool-projection policy, or other future modules until the NC parser is solid, repeatable, and well tested. Setup sheets are useful now, but they should be treated as parser validation output first.

The larger TK-MIA platform vision is captured in [docs/TK-MIA_Super_Tool_Upgrade_Roadmap.md](docs/TK-MIA_Super_Tool_Upgrade_Roadmap.md). That roadmap is intentionally gated until the NC parser returns reliable positive results on real programs.

A browser-friendly plan for sharing the vision with machinists, programmers, engineering, and leadership is available at [docs/TK-MIA_Project_Plan.html](docs/TK-MIA_Project_Plan.html).

## What v0.1 does

- Extracts tooling, holder assemblies, projection lengths, work offsets, stock, and setup notes from JSON, XML, text, ZIP, and inspectable Mastercam-adjacent files.
- Preserves proprietary or binary MCAM inputs as source evidence and emits warnings instead of pretending full extraction succeeded.
- Parses NC code into operations, tools, work offsets, spindle/feed events, comments, and motion blocks.
- Runs with only an NC file. CAM/MCAM files are optional.
- Creates practical photo-reference setup packages with `Photos/` and references A-H.
- Adds ASCII setup visualizations for fixture/part orientation, including vise-style sketches when NC comments mention a vise.
- Shows OP1 and OP2 side by side for flip jobs, including Y-axis flip/G55 right-side datum callouts when applicable.
- Applies simple shop-floor corrections for known tap-drill cases, such as 5/16 `.3125` for `3/8-16`.
- Accepts plain-English engineering instructions and maps them into structured constraints, notes, actions, and revision intent.
- Creates a new revision every run. Original NC programs are never overwritten.
- Generates `manufacturing-data.json`, updated NC output, revision history, and setup sheets in HTML, PDF, and XLSX.
- Uses adapter interfaces so future modules can add Alphacam, routers, lathes, waterjets, PR160P4 trunnions, Haas controls, inventory systems, and report editors without changing the core pipeline.

## Quick start

NC-only simple package:

```powershell
python C:\Users\tylor\plugins\mcam-assistant\scripts\mcam_assistant_cli.py `
  --nc C:\path\to\123456-A_OP10.nc `
  --out C:\path\to\123456-A `
  --part 123456-A `
  --machine "Haas VF4" `
  --fixture "6 inch Kurt Vise" `
  --fixture-reference "Photo H" `
  --setup-note "Set G54 from top center of stock" `
  --setup-note "Check stock protrusion 1.250" `
  --photo "H|Overall Setup|C:\path\to\overall_setup.jpg"
```

This creates a revision folder containing the revised NC file, `setup-sheet.html`, `setup-sheet.pdf`, `setup-sheet.xlsx`, `manufacturing-data.json`, and a `Photos/` folder when photo files are supplied.

CAM plus NC package:

```powershell
python C:\Users\tylor\plugins\mcam-assistant\scripts\mcam_assistant_cli.py `
  --mcam C:\path\to\job.json `
  --nc C:\path\to\program.nc `
  --instructions "Add setup notes for PR160P4 trunnion and verify tool projections." `
  --out C:\path\to\mcam-output
```

The command writes a timestamped revision folder under the output directory.

## Architecture

The core pipeline only depends on abstract adapters:

- `CamExtractor`: CAM file extraction.
- `NcParser`: NC operation parsing.
- `InstructionParser`: natural-language manufacturing instruction extraction.
- `NcEmitter`: revisioned NC creation.
- `ReportGenerator`: setup sheet generation.
- `RevisionStore`: immutable revision history.

New manufacturing domains register adapters through `PluginRegistry` without editing the pipeline.
