# TK-MIA Super Tool Upgrade Roadmap

## Gate Before This Work Starts

Do not start this upgrade until the initial NC parser has a positive, reliable return on real shop programs.

The gate is met only when:

- The NC parser correctly extracts tools, offsets, operations, feeds, speeds, cycles, and setup comments from representative NC files.
- `manufacturing-data.json` is dependable enough for setup sheets and downstream modules.
- Known sample programs and at least a small golden-program set pass regression checks.
- The generated setup sheet reflects parser output accurately.
- Original NC files are never overwritten.

Until that gate is met, all development stays focused on NC parser reliability.

## Core Mission

Build TK-MIA, the ThyssenKrupp Manufacturing Intelligence Agent, as a local-first manufacturing intelligence platform for engineering and shop-floor support.

TK-MIA should behave like a practical AI employee for:

- senior manufacturing engineering support
- CNC programming support
- CAM review support
- tooling coordination
- manufacturing documentation
- setup knowledge capture

The platform must be modular, extensible, local-first, human-in-the-loop, auditable, version controlled, safe for production environments, and useful to machinists.

## MVP After Parser Reliability

After the NC parser is dependable, expand into:

1. NC Program Parser
2. Setup Sheet Generator
3. Tooling and Fixture Photo Library

The system should ingest:

- `.nc`
- `.tap`
- `.eia`
- `.txt`
- other machine-specific NC/G-code text files

It should extract:

- tool numbers
- tool comments
- work offsets such as `G54`, `G55`, and `G56`
- operation sequence
- feeds
- speeds
- drill cycles
- tap cycles
- probing cycles
- rotary moves
- estimated cycle time
- safety/risk flags
- setup notes

It should generate:

- setup sheet draft
- tool list
- operator notes
- inspection notes
- JSON report
- Excel report
- PDF setup sheet

## Setup Photo Reference System

Setup sheets should support photo references instead of requiring CAD-rendered setup graphics.

Default photo labels:

- Photo A - Raw stock
- Photo B - Fixture assembly
- Photo C - Vise stop location
- Photo D - G54 location
- Photo E - Tool layout
- Photo F - Clamp locations
- Photo G - Inspection points
- Photo H - Overall setup

The photo library should link real shop-floor photos to:

- job number
- NC program
- machine
- fixture
- tooling
- work offset
- setup sheet
- operator notes

Actual shop-floor photos are preferred. Manufacturer catalog images may be secondary references. AI-generated tool images may only be placeholders and must never be treated as proof of real inventory.

## Tooling Numbering System

Reserve **L-Series exclusively for lathe tooling**.

Lathe categories:

- `L10000-L19999` - Rough Turning
- `L20000-L29999` - Finish Turning
- `L30000-L39999` - Boring Bars
- `L40000-L49999` - Grooving and Parting
- `L50000-L59999` - Threading
- `L60000-L69999` - Drills
- `L70000-L79999` - Reamers
- `L80000-L89999` - Taps
- `L90000-L99999` - Live Tooling / Milling / Specialty Attachments

Create a separate expanded **M-Series** for milling tools.

Milling categories:

- `M10000-M19999` - Roughing End Mills
- `M20000-M29999` - Finishing End Mills
- `M30000-M39999` - Ball End Mills / 3D Profiling
- `M40000-M49999` - Chamfer / Deburr / Spotting
- `M50000-M59999` - Drilling Tools
- `M60000-M69999` - Tapping and Threading
- `M70000-M79999` - Reaming / Boring / Hole Finishing
- `M80000-M89999` - Face Milling / Shell Milling
- `M90000-M99999` - Specialty Milling Tools

Additional prefixes:

- `H-Series` - Holders
- `F-Series` - Fixtures
- `V-Series` - Vises, jaws, stops, clamps
- `P-Series` - Probes and inspection tools
- `R-Series` - Router tools

## Photo-Based Inventory Vision

Later, the software should help users document:

- tool drawers
- toolboxes
- tool carts
- holders
- fixture carts
- vises
- soft jaws
- stops
- inspection setups
- full machine setups

Inventory records should include:

- internal ID
- description
- tool family
- vendor
- manufacturer part number
- serial number if applicable
- holder ID
- holder storage location
- actual tool stick-out
- minimum required projection
- projection pass/fail or review status
- machine compatibility
- location
- cabinet
- drawer
- quantity on hand
- quantity in machines
- minimum reorder quantity
- programs used on
- jobs used on
- setup photos
- catalog image
- replacement source or reorder location
- notes
- revision history
- jaws, stops, clamps, and fixture storage links when the tool is tied to a setup

## Manufacturing Knowledge Graph

Long term, TK-MIA should answer:

- What tools do I need to run this job?
- Where is the fixture stored?
- Which drawer has the tap?
- What holder was used last time?
- What photo shows the G54 location?
- Which programs use this fixture?
- Which tools are duplicated across the shop?
- Which tools should be standardized?
- What should be reordered?
- What setup should the machinist use for this program?

## Safety Requirements

Production files must never be overwritten.

Required behavior:

- Original files stay untouched.
- AI-created files receive revision names.
- Suggested changes require engineer approval.
- Every recommendation is auditable.
- Read-only mode is available.
- Program posting requires approval.
- Tooling and fixture records keep revision history.

Example revision names:

- `part123_v01`
- `part123_v02`
- `part123_AI_REVIEW`
- `part123_ENGINEER_APPROVED`

## Future Architecture

Backend options:

- Python
- FastAPI
- Postgres
- SQLAlchemy
- Pydantic
- local file storage
- ChromaDB or FAISS for searchable knowledge
- OpenAI API for review and documentation assistance

Frontend options:

- React
- Electron desktop app
- shop-floor-friendly UI
- large buttons
- simple search
- photo upload workflow
- barcode / QR support later

Plugin families:

- `plugin_nc_parser`
- `plugin_haas`
- `plugin_router`
- `plugin_lathe`
- `plugin_mastercam`
- `plugin_alphacam`
- `plugin_inventory`
- `plugin_setupsheet`
- `plugin_photo_library`

## Shop-Floor Adoption Plan

The software must give machinists immediate value. It should not feel like paperwork for engineering.

Benefits to highlight:

- less time searching for fixtures
- less time searching for tools
- fewer unclear setups
- easier repeat jobs
- faster first-piece setup
- better photos for G54 and fixture locations
- less tribal knowledge trapped in one person
- easier training for newer machinists
- better night-shift and weekend support
- fewer interruptions asking where tools are
- reduced setup mistakes
- easier reordering of common tools

Recommended rollout:

1. Start with one machine or one department.
2. Pick repeat jobs with known setup pain.
3. Generate setup sheets from existing NC files.
4. Add photo references A-H.
5. Label only the most-used tools and fixtures first.
6. Show machinists how the system saves setup/search time.
7. Collect feedback from actual users.
8. Improve templates before expanding.
9. Roll out department by department.

## Future Planning Package To Build

After the parser gate is met, create a full planning package with:

1. product requirements document
2. MVP scope
3. technical architecture
4. database schema
5. plugin architecture
6. NC parser design
7. setup sheet generator design
8. photo library design
9. tooling inventory design
10. fixture inventory design
11. milling tool numbering system
12. lathe tool numbering integration
13. shop-floor adoption strategy
14. safety and approval workflow
15. development roadmap
16. suggested folder structure
17. recommended GitHub repository structure
18. example data models
19. example API endpoints
20. example UI screens

## Reminder

This is the future expansion path, not the current implementation priority.

Current priority remains:

1. NC parser
2. NC parser tests
3. trustworthy structured JSON
4. setup sheet as parser validation output
