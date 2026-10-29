# .claude/skills/security-scan/tests/test_integration.py
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "lib"
FIXTURE = ROOT / "tests" / "fixtures" / "seeded_app"
sys.path.insert(0, str(LIB))
from pre_pass import run_pre_pass  # noqa: E402


def test_pre_pass_catches_seeded_secret(tmp_path: Path):
    root = tmp_path / "seeded"
    shutil.copytree(FIXTURE, root)
    marker = "sk-" + "ant-" + "seeded" + "value"
    (root / "app" / "config.ts").write_text(
        f'export const KEY = "{marker}";\n', encoding="utf-8"
    )
    patterns = json.loads((root / ".claude" / "security-patterns.json").read_text())
    findings = run_pre_pass(root, patterns)
    cats = {f["category"] for f in findings}
    assert "hardcoded_secret_prefix" in cats
    secret = next(f for f in findings if f["category"] == "hardcoded_secret_prefix")
    assert secret["severity"] == "critical"
    assert secret["file"] == "app/config.ts"


def test_assemble_fail_verdict(tmp_path: Path):
    # Synthesized findings = pre-pass secret (critical) + an IDOR the agent would add (high).
    findings = [
        {"severity": "critical", "confidence": "high", "category": "hardcoded_secret_prefix",
         "file": "app/config.ts", "start_line": 1, "end_line": 1,
         "description": "Live key in source", "suggestion": "Move to edge env"},
        {"severity": "high", "confidence": "medium", "category": "idor",
         "file": "supabase/functions/notes.ts", "start_line": 3, "end_line": 3,
         "description": "note_id read without ownership check", "suggestion": "Verify user_id"},
    ]
    fpath = tmp_path / "findings.json"
    fpath.write_text(json.dumps(findings))
    secdir = tmp_path / "security"
    r = subprocess.run(
        [sys.executable, str(LIB / "assemble_verdict.py"), str(fpath),
         "--security-dir", str(secdir), "--app-name", "seeded_app", "--date", "2026-05-27"],
        capture_output=True, text=True, cwd=str(LIB),
    )
    assert r.returncode == 0, r.stderr
    latest = json.loads((secdir / "latest.json").read_text())
    assert latest["verdict"] == "FAIL"
    assert latest["counts"] == {"critical": 1, "high": 1, "medium": 0, "low": 0}
    report = (secdir / "2026-05-27-security-scan.md").read_text()
    assert "app/config.ts:1" in report and "supabase/functions/notes.ts:3" in report
    assert "\u2014" not in report and "\u2013" not in report
