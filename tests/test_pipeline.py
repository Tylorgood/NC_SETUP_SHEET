from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mcam_assistant import ManufacturingPipeline


def test_pipeline_creates_revision_and_reports() -> None:
    out = ROOT / "tmp-test-output"
    if out.exists():
        shutil.rmtree(out)
    result = ManufacturingPipeline().run(
        [ROOT / "examples" / "sample_job.json"],
        ROOT / "examples" / "sample_program.nc",
        "Add PR160P4 trunnion setup note. Never overwrite the original program. Verify projection lengths.",
        out,
    )
    artifacts = result["artifacts"]
    assert Path(artifacts["nc"]).exists()
    assert Path(artifacts["html"]).exists()
    assert Path(artifacts["pdf"]).exists()
    assert Path(artifacts["xlsx"]).exists()
    payload = json.loads(Path(artifacts["json"]).read_text(encoding="utf-8"))
    assert payload["job"]["never_overwrite_originals"] is True
    assert payload["tooling"]["tools"][0]["number"] == 1
    assert payload["operations"][0]["tool_number"] == 1
    assert "pr160p4-trunnion" in payload["extension_points"]["future_modules"]


def test_nc_only_simple_package() -> None:
    out = ROOT / "tmp-simple-output"
    if out.exists():
        shutil.rmtree(out)
    result = ManufacturingPipeline().run_nc_only(
        ROOT / "examples" / "sample_program.nc",
        out,
        "Set G54 from top center of stock. Check stock protrusion 1.250.",
        {
            "part": "123456-A",
            "machine": "Haas VF4",
            "fixture": "6 inch Kurt Vise",
            "fixture_reference": "Photo H",
            "setup_notes": ["Verify vise stop location"],
        },
    )
    payload = json.loads(Path(result["artifacts"]["json"]).read_text(encoding="utf-8"))
    assert payload["job"]["package_mode"] == "nc-only-simple"
    assert payload["job"]["part"] == "123456-A"
    assert payload["tooling"]["tools"][0]["source"] == "nc_program"
    assert len(payload["job"]["visual_references"]) == 8
    html = Path(result["artifacts"]["html"]).read_text(encoding="utf-8")
    assert "Photo H" in html
    assert "<strong>Revision:</strong> rev-001" in html
    assert "ASCII Setup Visualization" in html
    assert "SETUP SKETCH" in html or "WHOLE JOB - SIDE BY SIDE VISE SETUP" in html


def test_3_8_16_tap_drill_correction() -> None:
    out = ROOT / "tmp-tap-output"
    if out.exists():
        shutil.rmtree(out)
    nc = out / "tap.nc"
    out.mkdir(parents=True)
    nc.write_text(
        "\n".join(
            [
                "O1 (TAP TEST)",
                "( T3 - #29 DRILL - PREP DRILL .376 )",
                "( T4 - 3/8\"-16 TAP - CUT THREADS )",
                "( FIXTURE: KURT VISE )",
                "( OPERATION 120: DRILL )",
                "T3 M06",
                "G00 G90 G54 X0 Y0 S2000 M03",
                "G01 Z-.5 F8.",
                "( OPERATION 130: TAP )",
                "T4 M06",
                "G84 Z-.375 F.0625",
                "M30",
            ]
        ),
        encoding="utf-8",
    )
    result = ManufacturingPipeline().run_nc_only(nc, out / "pkg")
    payload = json.loads(Path(result["artifacts"]["json"]).read_text(encoding="utf-8"))
    t3 = next(tool for tool in payload["tooling"]["tools"] if tool["number"] == 3)
    assert t3["diameter"] == 0.3125
    assert "3/8-16" in t3["name"]
    html = Path(result["artifacts"]["html"]).read_text(encoding="utf-8")
    assert "WHOLE JOB - SIDE BY SIDE VISE SETUP" in html
    assert "OP1 / G54 - TOP SIDE" in html
    assert "OP2 / G55 - Y-AXIS FLIP SIDE" in html
    assert "G55 X0 Y0 ^" in html
    assert "RIGHT-SIDE DATUM" in html
    assert "RIGHT EDGE AFTER Y-FLIP = G55 PICKUP" in html
    assert "MIRROR ABOUT Y AXIS" in html
