# MCAM Assistant Transfer Guide

This bundle is meant to move MCAM Assistant to a Windows workstation with the least drama possible.

## What You Need

- Windows workstation.
- Python 3.11 or newer available as `python`.
- Optional: Codex app/CLI if you want it installed as a Codex plugin.

The NC-only setup sheet generator uses only Python standard-library modules. It does not need `pip install`.

## Fastest Test Without Installing As A Plugin

Unzip this folder anywhere, then run:

```powershell
python .\scripts\mcam_assistant_cli.py `
  --nc "C:\path\to\program.nc" `
  --out "C:\path\to\setup_package" `
  --part "PART-NUMBER" `
  --machine "Haas VF4" `
  --fixture "6 inch Kurt Vise"
```

The tool creates a new revision folder every run and never overwrites the original NC program.

## Install As A Local Codex Plugin

From inside the unzipped `mcam-assistant` folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
```

Then install from the personal marketplace:

```powershell
codex plugin add mcam-assistant@personal
```

Start a new Codex thread after reinstalling so Codex sees the updated skill.

## Expected Output

Each generated revision includes:

- revisioned NC program
- `setup-sheet.html`
- `setup-sheet.pdf`
- `setup-sheet.xlsx`
- `manufacturing-data.json`
- `revision-history.json` at the package root

## Current Shop Logic

- NC-only mode is first-class.
- Vise jobs generate side-by-side ASCII setup views.
- OP1 keeps `G54` on the left datum.
- OP2 Y-axis flip shows `G55` on the right-side pickup.
- Known `3/8-16` tap setup corrects T3 to `5/16 DRILL (.3125)` when the NC header says stale `#29/.376`.

## Next Shop Feature

Minimum tool projections should be added as a tooling rules table, for example:

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

That should become a configurable shop file, not hard-coded forever.
