# .claude/skills/security-scan/tests/test_render_report.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from assemble_verdict import render_report  # noqa: E402

META = {"app_name": "example-app", "date": "2026-05-27", "verdict": "FAIL",
        "counts": {"critical": 1, "high": 0, "medium": 1, "low": 0},
        "base_sha": None, "codex": False}


def test_report_has_header_and_verdict():
    out = render_report([], {**META, "verdict": "PASS",
                              "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}})
    assert "# Security Scan - example-app" in out
    assert "PASS" in out
    assert "No findings" in out  # empty-case clean message


def test_report_renders_findings_table():
    findings = [{
        "severity": "critical", "confidence": "high", "category": "hardcoded-secret",
        "file": "app/config.ts", "start_line": 42, "end_line": 42,
        "description": "Live key in source", "suggestion": "Move to edge env",
    }]
    out = render_report(findings, META)
    assert "| critical |" in out
    assert "app/config.ts:42" in out
    assert "Live key in source" in out


def test_report_no_dashes_glyphs():
    out = render_report([], {**META, "verdict": "PASS",
                              "counts": {"critical": 0, "high": 0, "medium": 0, "low": 0}})
    assert "\u2014" not in out and "\u2013" not in out  # Law 1 (no em/en-dash glyphs)
