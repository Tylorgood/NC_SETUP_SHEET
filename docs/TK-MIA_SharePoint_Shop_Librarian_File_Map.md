# TK-MIA SharePoint Shop Librarian File Map

## Purpose

This SharePoint structure is the human-readable shop library for TK-MIA.

It should help machinists, programmers, engineering, and tooling support quickly answer:

- Where is the current NC program?
- Where is the setup sheet?
- Where are the setup photos?
- Where is the fixture stored?
- Where are the jaws, stops, parallels, and clamps?
- Which tools and holders are needed?
- What drawer or cabinet has the replacement tool?
- What changed since last time?

SharePoint is the shared shop library. TK-MIA-generated JSON is the machine-readable index.

## Top-Level SharePoint Site

```text
TK-MIA Shop Library/
|
|-- 00_READ_ME_AND_STANDARDS/
|-- 01_JOBS/
|-- 02_NC_PROGRAM_LIBRARY/
|-- 03_SETUP_SHEETS/
|-- 04_SETUP_PHOTOS/
|-- 05_TOOL_LIBRARY/
|-- 06_HOLDER_LIBRARY/
|-- 07_FIXTURE_LIBRARY/
|-- 08_VISE_JAWS_STOPS_CLAMPS/
|-- 09_MACHINE_LIBRARY/
|-- 10_INSPECTION_AND_FIRST_ARTICLE/
|-- 11_REPORTS_AND_EXPORTS/
|-- 12_ARCHIVE_READ_ONLY/
```

## 00 READ ME AND STANDARDS

```text
00_READ_ME_AND_STANDARDS/
|
|-- TK-MIA_Overview.pdf
|-- Naming_Standards.md
|-- Storage_Location_Code_Standard.md
|-- Photo_A-H_Reference_Standard.md
|-- Tool_Numbering_Standard.md
|-- Setup_Sheet_Template.html
|-- Approval_Workflow.md
```

This folder explains how the library works.

## Storage Location Code Standard

Use this format:

```text
AREA-CAB##-D##-R##-C##-B##
```

Area prefixes:

```text
R = Router area
L = Lathe area
M = Mill area
C = Tool crib / shared storage
```

Fields:

```text
CAB## = Cabinet number
D##   = Drawer number
R##   = Row inside drawer
C##   = Column inside drawer
B##   = Bin, cup, pocket, or slot
```

Example:

```text
C-CAB02-D04-R01-C03-B02
```

Meaning:

```text
Tool crib, cabinet 2, drawer 4, row 1, column 3, bin 2.
```

## 01 Jobs

Each job gets one folder. This is the main place a machinist or engineer should look.

```text
01_JOBS/
|
|-- 123456-A/
|   |
|   |-- 00_CURRENT/
|   |   |-- 123456-A_OP10.nc
|   |   |-- Setup_Sheet.html
|   |   |-- Setup_Sheet.pdf
|   |   |-- Setup_Sheet.xlsx
|   |   |-- manufacturing-data.json
|   |
|   |-- 01_NC_PROGRAMS/
|   |   |-- original/
|   |   |-- revisions/
|   |
|   |-- 02_SETUP_SHEETS/
|   |   |-- rev-001/
|   |   |-- rev-002/
|   |
|   |-- 03_PHOTOS/
|   |   |-- A_Raw_Stock/
|   |   |-- B_Fixture_Assembly/
|   |   |-- C_Vise_Stop_Location/
|   |   |-- D_G54_Location/
|   |   |-- E_Tool_Layout/
|   |   |-- F_Clamp_Locations/
|   |   |-- G_Inspection_Points/
|   |   |-- H_Overall_Setup/
|   |
|   |-- 04_TOOLING_USED/
|   |-- 05_FIXTURES_USED/
|   |-- 06_INSPECTION/
|   |-- 07_APPROVALS/
|   |-- 99_ARCHIVE/
```

### Job Folder Rule

`00_CURRENT` contains the current approved package for the floor.

Older generated packages stay in revision folders. Never overwrite original NC files.

## 02 NC Program Library

```text
02_NC_PROGRAM_LIBRARY/
|
|-- by_machine/
|   |-- Haas_VF4/
|   |-- Haas_UMC750/
|   |-- Router/
|   |-- Lathe/
|
|-- by_part_number/
|-- golden_programs/
|-- parser_test_programs/
|-- templates/
```

Use `golden_programs` for known-good programs that parser changes must keep passing.

## 03 Setup Sheets

```text
03_SETUP_SHEETS/
|
|-- current_by_job/
|-- revision_history/
|-- html/
|-- pdf/
|-- excel/
|-- examples/
```

This is a cross-job view for setup sheets. Job folders remain the main source.

## 04 Setup Photos

```text
04_SETUP_PHOTOS/
|
|-- by_job/
|-- by_fixture/
|-- by_machine/
|-- by_work_offset/
|-- reusable_reference_sets/
```

Default photo reference standard:

```text
Photo A - Raw stock
Photo B - Fixture assembly
Photo C - Vise stop location
Photo D - G54 location
Photo E - Tool layout
Photo F - Clamp locations
Photo G - Inspection points
Photo H - Overall setup
```

Reusable photo package example:

```text
04_SETUP_PHOTOS/reusable_reference_sets/VF4_KURT_VISE_STOP_01/
|
|-- A_Raw_Stock.jpg
|-- B_Fixture_Assembly.jpg
|-- C_Vise_Stop_Location.jpg
|-- D_G54_Location.jpg
|-- H_Overall_Setup.jpg
|-- photo_set.json
```

## 05 Tool Library

```text
05_TOOL_LIBRARY/
|
|-- M-Series_Milling/
|   |-- M10000_Roughing_End_Mills/
|   |-- M20000_Finishing_End_Mills/
|   |-- M30000_Ball_End_Mills/
|   |-- M40000_Chamfer_Deburr_Spotting/
|   |-- M50000_Drills/
|   |-- M60000_Taps_Threading/
|   |-- M70000_Reaming_Boring/
|   |-- M80000_Face_Mills/
|   |-- M90000_Specialty/
|
|-- L-Series_Lathe/
|-- R-Series_Router/
|-- tool_index.xlsx
|-- tool_index.json
```

Each tool record folder should look like:

```text
M50003_5-16_Drill_Tap_Drill/
|
|-- tool_record.json
|-- photos/
|-- catalog/
|-- programs_used/
|-- setup_history/
```

Suggested `tool_record.json` shape:

```json
{
  "tool_id": "M50003",
  "description": "5/16 Drill (.3125) - Tap Drill for 3/8-16",
  "serial_number": "TOOL SERIAL NEEDED",
  "vendor": "VENDOR NEEDED",
  "vendor_part_number": "PART NUMBER NEEDED",
  "holder_id": "H10003",
  "tool_location": "C-CAB??-D??-R??-C??-B??",
  "replacement_location": "C-CAB??-D??-R??-C??-B??",
  "minimum_projection_in": 1.5,
  "actual_stickout_in": "MEASURE AT SETUP",
  "programs_used": ["4x4_box_drill_tap"],
  "machines": ["MACHINE NEEDED"]
}
```

## 06 Holder Library

```text
06_HOLDER_LIBRARY/
|
|-- H10000_CAT40_End_Mill_Holders/
|-- H20000_CAT40_Collet_Chucks/
|-- H30000_CAT40_Face_Mill_Arbors/
|-- H40000_CAT40_Drill_Chucks/
|-- H90000_Specialty_Holders/
|-- holder_index.xlsx
|-- holder_index.json
```

Each holder record should track:

- holder ID
- serial number
- taper/type
- collet/nut requirements
- storage location
- tool currently loaded
- photos
- programs used
- inspection/condition notes

## 07 Fixture Library

```text
07_FIXTURE_LIBRARY/
|
|-- F-Series_Fixtures/
|-- V-Series_Vises_Jaws_Stops/
|-- fixture_index.xlsx
|-- fixture_index.json
```

Fixture records should track:

- fixture ID
- description
- machine compatibility
- storage location
- setup photos
- jobs used on
- required jaws/stops/clamps
- approval/revision history

## 08 Vise Jaws Stops Clamps

```text
08_VISE_JAWS_STOPS_CLAMPS/
|
|-- Kurt_Vise_Jaws/
|-- Soft_Jaws/
|-- Vise_Stops/
|-- Parallels/
|-- Clamps/
|-- jaw_stop_clamp_index.xlsx
|-- jaw_stop_clamp_index.json
```

Example item record:

```json
{
  "item_id": "V-STOP-0001",
  "description": "VF4 Kurt vise stop",
  "storage_location": "M-CAB??-D??-R??-C??-B??",
  "photo": "PHOTO NEEDED",
  "used_on_jobs": ["4x4_box_drill_tap"],
  "notes": "Verify stop location matches G54/G55 sketch."
}
```

## 09 Machine Library

```text
09_MACHINE_LIBRARY/
|
|-- Haas_VF4/
|-- Haas_UMC750/
|-- Router/
|-- Lathe/
|-- machine_index.xlsx
|-- machine_index.json
```

Machine records should track:

- machine ID
- control type
- post type
- tool capacity
- fixture compatibility
- probing availability
- preferred setup sheet notes

## 10 Inspection And First Article

```text
10_INSPECTION_AND_FIRST_ARTICLE/
|
|-- by_job/
|-- by_part/
|-- inspection_photos/
|-- first_article_reports/
```

## 11 Reports And Exports

```text
11_REPORTS_AND_EXPORTS/
|
|-- parser_reports/
|-- missing_data_reports/
|-- tooling_usage_reports/
|-- fixture_usage_reports/
|-- setup_sheet_exports/
```

## 12 Archive Read Only

```text
12_ARCHIVE_READ_ONLY/
|
|-- retired_jobs/
|-- old_programs/
|-- replaced_setups/
|-- obsolete_tools/
|-- obsolete_fixtures/
```

Archive content is read-only unless engineering intentionally restores it.

## File Naming Rules

Use stable names that sort well:

```text
PART_OPERATION_DESCRIPTION_REV.ext
```

Examples:

```text
123456-A_OP10_Setup_Sheet_rev-003.pdf
123456-A_OP10_manufacturing-data_rev-003.json
M50003_5-16_Drill_tool_record.json
VF4_KURT_VISE_STOP_01_photo_set.json
```

## SharePoint Metadata Columns

Recommended SharePoint columns:

- Part Number
- Operation
- Machine
- Program Name
- Work Offset
- Tool ID
- Holder ID
- Fixture ID
- Storage Location
- Revision
- Approved By
- Approval Status
- Last Verified Date
- Photo Reference
- Parser Confidence
- Needs Review

## Permissions

Recommended starting permissions:

- Machinists: read current setup packages, add photos to approved upload areas.
- Programmers: add/update NC parser candidates and setup packages.
- Engineering: approve setup packages and revisions.
- Tool crib: update tool, holder, and storage location records.
- Admins: archive, restore, and manage library standards.

## How TK-MIA Should Use This Library

TK-MIA should:

1. Parse the NC file.
2. Generate `manufacturing-data.json`.
3. Place setup package files in the correct job revision folder.
4. Link tools to tool records.
5. Link holders to holder records.
6. Link fixture/jaw/stop needs to fixture records.
7. Mark unknown locations as `LOCATION NEEDED`.
8. Produce missing-data reports so people know what to label next.

## Adoption Rule

Start small.

Use one machine, one repeat job, and one shared folder before expanding. The system becomes valuable when the shop trusts the data.
