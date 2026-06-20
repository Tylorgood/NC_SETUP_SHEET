# TK-MIA Monday Codex Handoff

## Purpose

Use this repository to bring TK-MIA / MCAM Assistant onto the Monday workstation without relying on local TeamUp access, chat history, or files stored only on this home machine.

## Project

**TK-MIA - ThyssenKrupp Manufacturing Intelligence Agent**

TK-MIA is a local-first manufacturing assistant for NC program review, tooling extraction, work-offset detection, setup-sheet generation, revision history, and eventually fixture/photo/tooling library integration.

## Current Working Tool

The current working implementation lives in this repo as the `mcam-assistant` Codex plugin and CLI.

It can:

- Run from only an NC file.
- Parse tool changes, operations, spindle/feed values, and work offsets.
- Generate setup sheets in HTML, PDF, and XLSX.
- Emit structured `manufacturing-data.json`.
- Preserve original NC files and create new revisions.
- Generate ASCII setup visuals for vise jobs.
- Show OP1 and OP2 side-by-side for flip jobs.
- Correct the known 3/8-16 tap-drill case to `5/16 DRILL (.3125)`.

## Monday Workstation Goals

1. Clone this repo.
2. Run the CLI against a known NC file.
3. Confirm the setup package outputs correctly.
4. Install the Codex plugin locally if Codex is available.
5. Start adding real shop photos, fixture labels, and tooling projection rules.

## Quick Test

```powershell
python .\scripts\mcam_assistant_cli.py `
  --nc "C:\path\to\program.nc" `
  --out "C:\path\to\setup_package" `
  --part "PART-NUMBER" `
  --machine "Haas VF4" `
  --fixture "6 inch Kurt Vise"
```

Expected outputs:

- revisioned NC program
- `setup-sheet.html`
- `setup-sheet.pdf`
- `setup-sheet.xlsx`
- `manufacturing-data.json`

## Codex Plugin Install

From the repo root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
codex plugin add mcam-assistant@personal
```

Start a new Codex thread after installing so Codex sees the plugin skill.

## Setup Sheet Direction

The practical setup-sheet maturity path is:

- Level 1: NC file only, tool list, work offsets, operations, cycle/setup notes.
- Level 2: NC file plus photo references, fixture photos, G54/G55 photos, tool layout photos, inspection photos.
- Level 3: future CAD/CAM integrated setup renders and simulations.

TK-MIA should prioritize Level 2 because machinists trust real shop-floor photos and simple visual references.

## Photo Reference Standard

Default photo slots:

- Photo A - Raw Stock
- Photo B - Fixture Assembly
- Photo C - Vise Stop Location
- Photo D - G54 Location
- Photo E - Tool Layout
- Photo F - Critical Clamp Locations
- Photo G - First Article Inspection Points
- Photo H - Overall Setup

## Next Feature: Minimum Tool Projections

Add configurable minimum projection rules instead of hard-coding them forever.

Suggested future file:

```text
shop_rules/tool_projection_rules.json
```

Example shape:

```json
{
  "minimum_projection_rules": [
    {"tool_type": "face_mill", "min_projection_in": 1.25},
    {"tool_type": "end_mill", "min_projection_in": 1.75},
    {"tool_type": "drill", "min_projection_in": 1.5},
    {"tool_type": "tap", "min_projection_in": 1.25}
  ]
}
```

Setup sheets should eventually show:

- actual projection
- minimum projection
- pass/fail or review flag
- source of the rule

## Future Repo Structure

As the project grows, split into:

```text
docs/
reference_programs/
golden_programs/
shop_rules/
fixture_database/
tooling_database/
prompts/
scripts/
skills/
tests/
```

## Important Safety Rule

Never overwrite original NC files. Every generated NC output must be a new revision.
