from __future__ import annotations

import html
import zipfile
from pathlib import Path
from typing import Any


class SetupSheetReportGenerator:
    name = "setup-sheet-v0"
    family = "report_generator"

    def generate(self, data: dict[str, Any], output_dir: Path) -> dict[str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / "setup-sheet.html"
        pdf_path = output_dir / "setup-sheet.pdf"
        xlsx_path = output_dir / "setup-sheet.xlsx"
        html_path.write_text(self._html(data), encoding="utf-8")
        self._minimal_pdf(pdf_path, "MCAM Assistant setup sheet generated. Open setup-sheet.html for formatted details.")
        self._xlsx(xlsx_path, data)
        return {"html": str(html_path), "pdf": str(pdf_path), "xlsx": str(xlsx_path)}

    def _html(self, data: dict[str, Any]) -> str:
        job = data.get("job", {})
        ascii_visual = _ascii_setup_visual(data)
        location_system = _location_system_html(job.get("location_serial_system", {}))
        tool_drawer_visual = _ascii_tool_drawer_visual(data)
        holder_build_visual = _ascii_holder_build_visual(data)
        operation_sections = _operation_sections_html(data.get("operations", []))
        tool_rows = []
        for tool in data.get("tooling", {}).get("tools", []):
            tool_rows.append(
                "<tr>"
                f"<td>T{html.escape(str(tool.get('number', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('internal_id', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('name', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('diameter', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('holder_id', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('serial_number', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('tool_location', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('holder_location', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('stickout_actual_in', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('minimum_projection_in', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('projection_status', '') or ''))}</td>"
                "</tr>"
            )
        inventory_rows = []
        for item in job.get("required_items", []):
            inventory_rows.append(
                "<tr>"
                f"<td>{html.escape(str(item.get('item', '')))}</td>"
                f"<td>{html.escape(str(item.get('asset_id', '')))}</td>"
                f"<td>{html.escape(str(item.get('location', '')))}</td>"
                f"<td>{html.escape(str(item.get('photo', '')))}</td>"
                f"<td>{html.escape(str(item.get('notes', '')))}</td>"
                "</tr>"
            )
        photo_rows = []
        for ref in job.get("visual_references", []):
            file_value = ref.get("file") or ""
            if file_value:
                file_cell = f'<code>{html.escape(str(file_value))}</code>'
            else:
                file_cell = html.escape(str(ref.get("status", "")))
            photo_rows.append(
                "<tr>"
                f"<td>Photo {html.escape(str(ref.get('label', '')))}</td>"
                f"<td>{html.escape(str(ref.get('description', '')))}</td>"
                f"<td>{file_cell}</td>"
                "</tr>"
            )
        setup_notes = "".join(f"<li>{html.escape(str(note))}</li>" for note in job.get("setup_notes", []))
        work_offsets = ", ".join(job.get("work_offsets", []))
        return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>MCAM Assistant Setup Sheet</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; }}
    h1, h2 {{ margin-bottom: 8px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 12px 0 28px; }}
    th, td {{ border: 1px solid #ccd3df; padding: 8px; text-align: left; }}
    th {{ background: #edf2f7; }}
    code {{ background: #edf2f7; padding: 2px 4px; }}
    pre.ascii {{ background: #f8fafc; border: 1px solid #ccd3df; padding: 16px; line-height: 1.25; overflow-x: auto; }}
    .op-block {{ margin: 14px 0 24px; border: 2px solid #94a3b8; border-radius: 8px; overflow: hidden; }}
    .op-title {{ margin: 0; padding: 10px 12px; background: #1f2937; color: #ffffff; font-size: 16px; }}
    .op-block table {{ margin: 0; }}
    .tracking-note {{ padding: 10px 12px; background: #fff7ed; border: 1px solid #fed7aa; }}
  </style>
</head>
<body>
  <h1>MCAM Assistant Setup Sheet</h1>
  <p><strong>Revision:</strong> {html.escape(str(data.get("revisions", [{}])[-1].get("revision_id", "n/a") if data.get("revisions") else "n/a"))}</p>
  <h2>Job</h2>
  <table><tbody>
    <tr><th>Part</th><td>{html.escape(str(job.get("part", "")))}</td></tr>
    <tr><th>Machine</th><td>{html.escape(str(job.get("machine", "")))}</td></tr>
    <tr><th>Program</th><td>{html.escape(str(job.get("program", "")))}</td></tr>
    <tr><th>Work Offset</th><td>{html.escape(work_offsets)}</td></tr>
    <tr><th>Fixture</th><td>{html.escape(str(job.get("fixture", "")))}</td></tr>
    <tr><th>Fixture Reference</th><td>{html.escape(str(job.get("fixture_reference", "")))}</td></tr>
  </tbody></table>
  <h2>ASCII Setup Visualization</h2>
  <pre class="ascii">{html.escape(ascii_visual)}</pre>
  <h2>Storage Location Serial Number System</h2>
  {location_system}
  <h2>ASCII Tool Drawer Map</h2>
  <pre class="ascii">{html.escape(tool_drawer_visual)}</pre>
  <h2>ASCII CAT40 Holder Assembly Guide</h2>
  <pre class="ascii">{html.escape(holder_build_visual)}</pre>
  <h2>Operations</h2>
  {operation_sections}
  <h2>Tool Tracking, Holders, Locations, and Stick-Out</h2>
  <p class="tracking-note">Fill these fields as tools, holders, jaws, drawers, and photos are labeled. Unknown values are intentionally shown as needed instead of guessed.</p>
  <table><thead><tr><th>Tool</th><th>Asset ID</th><th>Description</th><th>Dia.</th><th>Holder</th><th>Serial</th><th>Tool Location</th><th>Holder Location</th><th>Actual Stick-Out</th><th>Minimum Projection</th><th>Status</th></tr></thead><tbody>{''.join(tool_rows)}</tbody></table>
  <h2>Fixture, Jaws, Stops, and Required Setup Items</h2>
  <table><thead><tr><th>Item</th><th>Asset / Serial</th><th>Storage Location</th><th>Photo</th><th>Notes</th></tr></thead><tbody>{''.join(inventory_rows)}</tbody></table>
  <h2>Setup Notes</h2>
  <ul>{setup_notes}</ul>
  <h2>Visual References</h2>
  <table><thead><tr><th>Reference</th><th>Description</th><th>File</th></tr></thead><tbody>{''.join(photo_rows)}</tbody></table>
  <h2>Instructions</h2>
  <pre>{html.escape(str(data.get("instructions", {}).get("raw", "")))}</pre>
</body>
</html>
"""

    def _minimal_pdf(self, path: Path, text: str) -> None:
        stream = f"BT /F1 12 Tf 72 720 Td ({_pdf_escape(text)}) Tj ET"
        objects = [
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
            "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
            f"5 0 obj << /Length {len(stream.encode('latin-1'))} >> stream\n{stream}\nendstream endobj",
        ]
        pdf = "%PDF-1.4\n"
        offsets = [0]
        for obj in objects:
            offsets.append(len(pdf.encode("latin-1")))
            pdf += obj + "\n"
        xref_at = len(pdf.encode("latin-1"))
        pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        for offset in offsets[1:]:
            pdf += f"{offset:010d} 00000 n \n"
        pdf += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
        path.write_bytes(pdf.encode("latin-1"))

    def _xlsx(self, path: Path, data: dict[str, Any]) -> None:
        job = data.get("job", {})
        ascii_visual = _ascii_setup_visual(data)
        tool_drawer_visual = _ascii_tool_drawer_visual(data)
        holder_build_visual = _ascii_holder_build_visual(data)
        operations = data.get("operations", [])
        tools = data.get("tooling", {}).get("tools", [])
        photos = job.get("visual_references", [])
        required_items = job.get("required_items", [])
        setup = [
            ["Part", job.get("part")],
            ["Machine", job.get("machine")],
            ["Program", job.get("program")],
            ["Work Offsets", ", ".join(job.get("work_offsets", []))],
            ["Fixture", job.get("fixture")],
            ["Fixture Reference", job.get("fixture_reference")],
            ["ASCII Setup Visualization", ascii_visual],
            ["Location Code Format", job.get("location_serial_system", {}).get("format")],
            ["Location Code Example", job.get("location_serial_system", {}).get("example")],
            ["ASCII Tool Drawer Map", tool_drawer_visual],
            ["ASCII CAT40 Holder Assembly", holder_build_visual],
        ]
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", CONTENT_TYPES)
            zf.writestr("_rels/.rels", RELS)
            zf.writestr("xl/workbook.xml", WORKBOOK)
            zf.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
            zf.writestr("xl/worksheets/sheet1.xml", _sheet_xml(setup))
            zf.writestr("xl/worksheets/sheet2.xml", _sheet_xml([["Section", "Seq", "Name", "Tool", "WCS", "RPM", "Feed"]] + [[_operation_section_name(op), op.get("sequence"), op.get("name"), op.get("tool_number"), op.get("work_offset"), op.get("spindle_rpm"), op.get("feed_rate")] for op in operations]))
            zf.writestr("xl/worksheets/sheet3.xml", _sheet_xml([["Tool", "Asset ID", "Name", "Diameter", "Holder", "Serial", "Tool Location", "Holder Location", "Actual Stick-Out", "Minimum Projection", "Status"]] + [[tool.get("number"), tool.get("internal_id"), tool.get("name"), tool.get("diameter"), tool.get("holder_id"), tool.get("serial_number"), tool.get("tool_location"), tool.get("holder_location"), tool.get("stickout_actual_in"), tool.get("minimum_projection_in"), tool.get("projection_status")] for tool in tools]))
            zf.writestr("xl/worksheets/sheet4.xml", _sheet_xml([["Reference", "Description", "File", "Status"]] + [[f"Photo {ref.get('label')}", ref.get("description"), ref.get("file"), ref.get("status")] for ref in photos]))
            zf.writestr("xl/worksheets/sheet5.xml", _sheet_xml([["Item", "Asset / Serial", "Storage Location", "Photo", "Notes"]] + [[item.get("item"), item.get("asset_id"), item.get("location"), item.get("photo"), item.get("notes")] for item in required_items]))


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _cell(value: Any, col: int, row: int) -> str:
    ref = f"{chr(65 + col)}{row}"
    return f'<c r="{ref}" t="inlineStr"><is><t>{html.escape("" if value is None else str(value))}</t></is></c>'


def _sheet_xml(rows: list[list[Any]]) -> str:
    body = []
    for row_idx, row in enumerate(rows, start=1):
        cells = "".join(_cell(value, col_idx, row_idx) for col_idx, value in enumerate(row))
        body.append(f'<row r="{row_idx}">{cells}</row>')
    return f'<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(body)}</sheetData></worksheet>'


def _operation_sections_html(operations: list[dict[str, Any]]) -> str:
    sections = [
        ("OP1 / G54 - Top Side", [op for op in operations if _operation_section_name(op).startswith("OP1")]),
        ("OP2 / G55 - Flip Side", [op for op in operations if _operation_section_name(op).startswith("OP2")]),
        ("Other / Header / Review", [op for op in operations if _operation_section_name(op).startswith("Other")]),
    ]
    blocks = []
    for title, ops in sections:
        if not ops:
            continue
        rows = []
        for op in ops:
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(op.get('sequence', '')))}</td>"
                f"<td>{html.escape(str(op.get('name', '')))}</td>"
                f"<td>{html.escape(str(op.get('tool_number', '') or ''))}</td>"
                f"<td>{html.escape(str(op.get('work_offset', '') or ''))}</td>"
                f"<td>{html.escape(str(op.get('spindle_rpm', '') or ''))}</td>"
                f"<td>{html.escape(str(op.get('feed_rate', '') or ''))}</td>"
                "</tr>"
            )
        blocks.append(
            f'<div class="op-block"><h3 class="op-title">{html.escape(title)}</h3>'
            f'<table><thead><tr><th>#</th><th>Name</th><th>Tool</th><th>WCS</th><th>RPM</th><th>Feed</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
        )
    return "".join(blocks)


def _location_system_html(system: dict[str, Any]) -> str:
    if not system:
        return "<p>No location system defined.</p>"
    area_rows = []
    for area in system.get("areas", []):
        area_rows.append(
            "<tr>"
            f"<td>{html.escape(str(area.get('prefix', '')))}</td>"
            f"<td>{html.escape(str(area.get('name', '')))}</td>"
            "</tr>"
        )
    field_rows = []
    for field in system.get("fields", []):
        field_rows.append(
            "<tr>"
            f"<td>{html.escape(str(field.get('code', '')))}</td>"
            f"<td>{html.escape(str(field.get('name', '')))}</td>"
            "</tr>"
        )
    return (
        f"<p><strong>Format:</strong> <code>{html.escape(str(system.get('format', '')))}</code> "
        f"<strong>Example:</strong> <code>{html.escape(str(system.get('example', '')))}</code></p>"
        f"<table><thead><tr><th>Area Prefix</th><th>Meaning</th></tr></thead><tbody>{''.join(area_rows)}</tbody></table>"
        f"<table><thead><tr><th>Code</th><th>Meaning</th></tr></thead><tbody>{''.join(field_rows)}</tbody></table>"
    )


def _operation_section_name(op: dict[str, Any]) -> str:
    work_offset = str(op.get("work_offset") or "")
    name = str(op.get("name") or "").upper()
    sequence = int(op.get("sequence") or 0)
    if work_offset == "G55" or "OPERATION 200" in name or sequence >= 11:
        return "OP2 / G55"
    if work_offset == "G54" or 2 <= sequence <= 10:
        return "OP1 / G54"
    return "Other"


def _ascii_setup_visual(data: dict[str, Any]) -> str:
    job = data.get("job", {})
    operations = data.get("operations", [])
    comments = " ".join(comment for op in operations for comment in op.get("comments", []))
    comments = comments + " " + str(job.get("setup_context") or "")
    fixture = str(job.get("fixture") or "")
    work_offsets = ", ".join(job.get("work_offsets", [])) or "G54"
    is_vise = "VISE" in (fixture + comments).upper() or "VICE" in (fixture + comments).upper()
    stock = _find_comment_value(comments, "STOCK") or "4.5 x 4.5 x 1.0 stock"
    part = job.get("part") or "PART"
    if is_vise:
        return "\n".join(
            [
                f"PART: {part}",
                f"WORK OFFSETS: {work_offsets}",
                f"STOCK: {stock}",
                "",
                "WHOLE JOB - SIDE BY SIDE VISE SETUP",
                "",
                *_side_by_side(_op1_vise_lines(), _op2_vise_lines()),
                "",
                "NOTES:",
                "- OP1 uses G54 with X0 Y0 at the back-left corner against the fixed jaw.",
                "- OP2 flips the part along the Y axis and uses G55 on the right side of the flipped setup.",
                "- Keep the fixed jaw/back jaw as Y0 reference unless the traveler says otherwise.",
                "- Four tapped holes are shown approximately 0.5 from part edges.",
                "- Verify actual stop, parallels, protrusion, and clamp clearance at machine.",
            ]
        )
    return "\n".join(
        [
            f"PART: {part}",
            f"WORK OFFSETS: {work_offsets}",
            "",
            "SETUP SKETCH",
            "",
            "        X0,Y0  +----------------------------+  X+",
            "              |                            |",
            "              |            PART            |",
            "              |                            |",
            "              +----------------------------+",
            "                 Y-",
            "",
            "NOTES:",
            "- Confirm fixture and datum from traveler, setup photos, or programmer notes.",
            "- Add fixture details to improve this ASCII visualization.",
        ]
    )


def _ascii_tool_drawer_visual(data: dict[str, Any]) -> str:
    tools = data.get("tooling", {}).get("tools", [])
    drawer_cells = []
    for index in range(8):
        tool = tools[index] if index < len(tools) else None
        if tool:
            label = f"T{tool.get('number')} {tool.get('internal_id', '')}"
        else:
            label = "OPEN"
        drawer_cells.append(label[:16])
    return "\n".join(
        [
            "TOOL CRIB DRAWER EXAMPLE - USE LOCATION CODE ON EACH BIN",
            "LOCATION FORMAT: AREA-CAB##-D##-R##-C##-B##",
            "AREAS: R=ROUTER  L=LATHE  M=MILL  C=CRIB",
            "",
            "Example drawer: C-CAB01-D01",
            "",
            "        COLUMN 01          COLUMN 02          COLUMN 03          COLUMN 04",
            "      +----------------+----------------+----------------+----------------+",
            f"R01   | {drawer_cells[0]:<14} | {drawer_cells[1]:<14} | {drawer_cells[2]:<14} | {drawer_cells[3]:<14} |",
            "      +----------------+----------------+----------------+----------------+",
            f"R02   | {drawer_cells[4]:<14} | {drawer_cells[5]:<14} | {drawer_cells[6]:<14} | {drawer_cells[7]:<14} |",
            "      +----------------+----------------+----------------+----------------+",
            "        B01              B02              B03              B04",
            "",
            "LABEL EACH BIN LIKE: C-CAB01-D01-R01-C03-B03",
            "WRITE THE SAME CODE ON THE SETUP SHEET AND TOOL RECORD.",
        ]
    )


def _ascii_holder_build_visual(data: dict[str, Any]) -> str:
    tools = data.get("tooling", {}).get("tools", [])
    lines = [
        "STANDARD CAT40 TOOL ASSEMBLY EXPECTATION",
        "",
        "        MACHINE SPINDLE",
        "             ||",
        "        _____||_____",
        "       /            \\",
        "      /   CAT40      \\        Holder ID: H#####",
        "     /    HOLDER      \\       Holder serial/location required",
        "     ------------------",
        "            ||",
        "            ||  COLLET / END MILL HOLDER / FACE MILL ARBOR",
        "            ||",
        "        [ TOOL BODY ]          Tool asset ID: M#####",
        "            ||                 Tool serial required",
        "            ||<---- STICK-OUT / PROJECTION ---->",
        "            ||                 Measure actual stick-out at setup",
        "            \\/",
        "        CUTTING END",
        "",
        "TOOLS FOR THIS JOB:",
    ]
    for tool in tools:
        lines.append(
            f"- T{tool.get('number')}: {tool.get('internal_id')} in {tool.get('holder_id')} | "
            f"actual {tool.get('stickout_actual_in')} | min {tool.get('minimum_projection_in')}"
        )
    lines.extend(
        [
            "",
            "CHECKS:",
            "- Verify holder matches setup sheet.",
            "- Verify pull stud, collet, nut, and cutter are correct.",
            "- Record actual stick-out before first article.",
            "- If actual stick-out is below minimum projection, stop and review.",
        ]
    )
    return "\n".join(lines)


def _find_comment_value(comments: str, label: str) -> str | None:
    import re

    match = re.search(rf"{label}\s*:\s*([^()]+?)(?:\s{2,}|$)", comments, re.I)
    if match:
        return " ".join(match.group(1).strip().split())
    return None


def _op1_vise_lines() -> list[str]:
    return [
        "OP1 / G54 - TOP SIDE",
        "MACHINE +Y / BACK JAW",
        "--------------------------------------",
        "| FIXED JAW / Y0 DATUM               |",
        "--------------------------------------",
        "      ^ G54 X0 Y0",
        "      |",
        "X0,Y0 +--------------------------+ X+",
        "      | O                    O   |",
        "      |                          |",
        "      |       TOP SIDE UP        |",
        "      |                          |",
        "      | O                    O   |",
        "      +--------------------------+",
        "          Y- / INTO VISE",
        "--------------------------------------",
        "| MOVABLE JAW / CLAMP PRESSURE       |",
        "--------------------------------------",
        "OPS: face, profile, drill, tap",
    ]


def _op2_vise_lines() -> list[str]:
    return [
        "OP2 / G55 - Y-AXIS FLIP SIDE",
        "MACHINE +Y / BACK JAW",
        "--------------------------------------",
        "| FIXED JAW / Y0 DATUM               |",
        "--------------------------------------",
        "                     G55 X0 Y0 ^",
        "                RIGHT-SIDE DATUM |",
        "      +--------------------------+ G55",
        "      |                          | X0,Y0",
        "      |                          |",
        "      |       PART FLIPPED       |",
        "      |   MIRROR ABOUT Y AXIS    |",
        "      |    BOTTOM SIDE UP        |",
        "      |                          |",
        "      |                          |",
        "      +--------------------------+",
        "          Y- / INTO VISE",
        "--------------------------------------",
        "| MOVABLE JAW / CLAMP PRESSURE       |",
        "--------------------------------------",
        "OPS: face bottom, finish side walls",
        "RIGHT EDGE AFTER Y-FLIP = G55 PICKUP",
    ]


def _side_by_side(left: list[str], right: list[str], width: int = 44, gap: str = "    ") -> list[str]:
    row_count = max(len(left), len(right))
    rows = []
    for index in range(row_count):
        left_text = left[index] if index < len(left) else ""
        right_text = right[index] if index < len(right) else ""
        rows.append(f"{left_text:<{width}}{gap}{right_text}")
    return rows


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet4.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet5.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
RELS = """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>"""
WORKBOOK = """<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Setup" sheetId="1" r:id="rId1"/><sheet name="Operations" sheetId="2" r:id="rId2"/><sheet name="Tool Tracking" sheetId="3" r:id="rId3"/><sheet name="Photos" sheetId="4" r:id="rId4"/><sheet name="Setup Items" sheetId="5" r:id="rId5"/></sheets></workbook>"""
WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/><Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/><Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet5.xml"/></Relationships>"""
