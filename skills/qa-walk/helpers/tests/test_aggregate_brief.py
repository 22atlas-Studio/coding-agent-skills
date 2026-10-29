import json
from pathlib import Path
from aggregate_brief import aggregate_brief
from findings_schema import WorkflowFinding


def _load(path: Path) -> WorkflowFinding:
    return WorkflowFinding.model_validate(json.loads(path.read_text()))


def test_brief_severity_sorts_bugs(fixtures_dir):
    findings = [
        _load(fixtures_dir / "findings_bug_high.json"),
        _load(fixtures_dir / "findings_bug_critical.json"),
        _load(fixtures_dir / "findings_pass.json"),
    ]
    brief = aggregate_brief(
        app="example-app", run_ts="2026-05-10-1430", runner="codex",
        budget_usd=30.0, findings=findings, appended_count=0,
    )
    crit_pos = brief.find("BUG-001")
    high_pos = brief.find("BUG-002")
    assert crit_pos < high_pos, "critical must appear before high"
    assert "[critical]" in brief
    assert "[high]" in brief


def test_brief_with_no_bugs_omits_bugs_section(fixtures_dir):
    findings = [_load(fixtures_dir / "findings_pass.json")]
    brief = aggregate_brief(
        app="example-app", run_ts="2026-05-10-1430", runner="codex",
        budget_usd=30.0, findings=findings, appended_count=0,
    )
    assert "## Bugs" not in brief


def test_brief_blocked_budget_in_blocked_section(fixtures_dir):
    findings = [_load(fixtures_dir / "findings_blocked_budget.json")]
    brief = aggregate_brief(
        app="example-app", run_ts="2026-05-10-1430", runner="codex",
        budget_usd=30.0, findings=findings, appended_count=0,
    )
    assert "## Blocked" in brief
    assert "BLOCKED-BUDGET" in brief


def test_brief_appended_count_message(fixtures_dir):
    findings = [_load(fixtures_dir / "findings_bug_critical.json")]
    brief = aggregate_brief(
        app="example-app", run_ts="2026-05-10-1430", runner="codex",
        budget_usd=30.0, findings=findings, appended_count=1,
    )
    assert "1 check(s) appended" in brief
