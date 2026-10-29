# .claude/skills/security-scan/tests/test_assemble_verdict.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from assemble_verdict import compute_counts, decide_verdict  # noqa: E402


def _f(sev):
    return {"severity": sev, "confidence": "high", "category": "x",
            "file": "a.ts", "start_line": 1, "end_line": 1,
            "description": "d", "suggestion": None}


def test_counts():
    findings = [_f("critical"), _f("medium"), _f("medium"), _f("low")]
    assert compute_counts(findings) == {"critical": 1, "high": 0, "medium": 2, "low": 1}


def test_verdict_fail_on_critical():
    assert decide_verdict({"critical": 1, "high": 0, "medium": 0, "low": 0}, {"critical", "high"}) == "FAIL"


def test_verdict_fail_on_high():
    assert decide_verdict({"critical": 0, "high": 2, "medium": 0, "low": 0}, {"critical", "high"}) == "FAIL"


def test_verdict_warnings_on_medium_only():
    assert decide_verdict({"critical": 0, "high": 0, "medium": 3, "low": 1}, {"critical", "high"}) == "PASS_WITH_WARNINGS"


def test_verdict_pass_clean():
    assert decide_verdict({"critical": 0, "high": 0, "medium": 0, "low": 0}, {"critical", "high"}) == "PASS"


def test_fail_on_override_critical_only():
    # high no longer fails when threshold is critical-only
    assert decide_verdict({"critical": 0, "high": 5, "medium": 0, "low": 0}, {"critical"}) == "PASS_WITH_WARNINGS"
