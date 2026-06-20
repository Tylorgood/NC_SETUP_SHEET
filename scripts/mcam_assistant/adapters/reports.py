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
        rows = []
        for op in data.get("operations", []):
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
        tool_rows = []
        for tool in data.get("tooling", {}).get("tools", []):
            tool_rows.append(
                "<tr>"
                f"<td>{html.escape(str(tool.get('number', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('name', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('diameter', '') or ''))}</td>"
                f"<td>{html.escape(str(tool.get('source', '') or ''))}</td>"
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
  <h2>Operations</h2>
  <table><thead><tr><th>#</th><th>Name</th><th>Tool</th><th>WCS</th><th>RPM</th><th>Feed</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
  <h2>Tooling</h2>
  <table><thead><tr><th>Tool</th><th>Name</th><th>Diameter</th><th>Source</th></tr></thead><tbody>{''.join(tool_rows)}</tbody></table>
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
        operations = data.get("operations", [])
        tools = data.get("tooling", {}).get("tools", [])
        photos = job.get("visual_references", [])
        setup = [
            ["Part", job.get("part")],
            ["Machine", job.get("machine")],
            ["Program", job.get("program")],
            ["Work Offsets", ", ".join(job.get("work_offsets", []))],
            ["Fixture", job.get("fixture")],
            ["Fixture Reference", job.get("fixture_reference")],
            ["ASCII Setup Visualization", ascii_visual],
        ]
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", CONTENT_TYPES)
            zf.writestr("_rels/.rels", RELS)
            zf.writestr("xl/workbook.xml", WORKBOOK)
            zf.writestr("xl/_rels/workbook.xml.rels", WORKBOOK_RELS)
            zf.writestr("xl/worksheets/sheet1.xml", _sheet_xml(setup))
            zf.writestr("xl/worksheets/sheet2.xml", _sheet_xml([["Seq", "Name", "Tool", "WCS", "RPM", "Feed"]] + [[op.get("sequence"), op.get("name"), op.get("tool_number"), op.get("work_offset"), op.get("spindle_rpm"), op.get("feed_rate")] for op in operations]))
            zf.writestr("xl/worksheets/sheet3.xml", _sheet_xml([["Tool", "Name", "Diameter", "Projection"]] + [[tool.get("number"), tool.get("name"), tool.get("diameter"), ""] for tool in tools]))
            zf.writestr("xl/worksheets/sheet4.xml", _sheet_xml([["Reference", "Description", "File", "Status"]] + [[f"Photo {ref.get('label')}", ref.get("description"), ref.get("file"), ref.get("status")] for ref in photos]))


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
</Types>"""
RELS = """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>"""
WORKBOOK = """<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Setup" sheetId="1" r:id="rId1"/><sheet name="Operations" sheetId="2" r:id="rId2"/><sheet name="Tooling" sheetId="3" r:id="rId3"/><sheet name="Photos" sheetId="4" r:id="rId4"/></sheets></workbook>"""
WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/><Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/></Relationships>"""
