import yaml
from pathlib import Path
from append_regression import append_regression_checks


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _write_workflows(path: Path, workflows: list[dict]):
    path.write_text(yaml.safe_dump({
        "app": "example-app", "last_scaffold": "2026-05-10",
        "workflows": workflows,
    }, sort_keys=False))


def test_bug_appends_one_regression_check(tmp_path):
    wf_path = tmp_path / "workflows.yaml"
    _write_workflows(wf_path, [{
        "id": "dealer-offer-accept",
        "name": "X", "persona": "dealer", "entry_route": "/x",
        "test_data": {}, "definition_of_done": "..", "do_not_change": "..",
        "regression_checks": [],
    }])

    finding = {
        "workflow_id": "dealer-offer-accept",
        "verdict": "BUG",
        "suggested_regression_check": "Accept button POST must succeed when offer is pending",
    }
    appended = append_regression_checks(wf_path, [finding], run_ts="2026-05-10-1430")
    assert appended == 1
    out = _load(wf_path)
    assert out["workflows"][0]["regression_checks"] == [
        "Accept button POST must succeed when offer is pending (bug from run 2026-05-10-1430)",
    ]


def test_pass_does_not_change_file(tmp_path):
    wf_path = tmp_path / "workflows.yaml"
    _write_workflows(wf_path, [{
        "id": "x", "name": "X", "persona": "p", "entry_route": "/x",
        "test_data": {}, "definition_of_done": "..", "do_not_change": "..",
        "regression_checks": [],
    }])
    before = wf_path.read_text()
    appended = append_regression_checks(wf_path, [{"workflow_id": "x", "verdict": "PASS"}], run_ts="2026-05-10-1430")
    assert appended == 0
    assert wf_path.read_text() == before


def test_idempotent_does_not_duplicate(tmp_path):
    wf_path = tmp_path / "workflows.yaml"
    _write_workflows(wf_path, [{
        "id": "x", "name": "X", "persona": "p", "entry_route": "/x",
        "test_data": {}, "definition_of_done": "..", "do_not_change": "..",
        "regression_checks": [],
    }])
    finding = {
        "workflow_id": "x",
        "verdict": "BUG",
        "suggested_regression_check": "X must Y",
    }
    append_regression_checks(wf_path, [finding], run_ts="2026-05-10-1430")
    append_regression_checks(wf_path, [finding], run_ts="2026-05-10-1430")
    out = _load(wf_path)
    assert len(out["workflows"][0]["regression_checks"]) == 1


def test_existing_checks_preserved(tmp_path):
    wf_path = tmp_path / "workflows.yaml"
    _write_workflows(wf_path, [{
        "id": "x", "name": "X", "persona": "p", "entry_route": "/x",
        "test_data": {}, "definition_of_done": "..", "do_not_change": "..",
        "regression_checks": ["Old check from prior run"],
    }])
    finding = {
        "workflow_id": "x",
        "verdict": "BUG",
        "suggested_regression_check": "New thing",
    }
    append_regression_checks(wf_path, [finding], run_ts="2026-05-10-1430")
    out = _load(wf_path)
    assert out["workflows"][0]["regression_checks"] == [
        "Old check from prior run",
        "New thing (bug from run 2026-05-10-1430)",
    ]
