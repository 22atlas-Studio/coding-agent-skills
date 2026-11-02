import pytest
from preflight import (
    preflight,
    PreflightError,
    DEV_SERVER_PROBE_BODY_MARKER,
)


def test_missing_workflows_yaml_raises_with_template_hint(tmp_qa_dir):
    (tmp_qa_dir / "auth.yaml").write_text("personas: {}\n")
    with pytest.raises(PreflightError, match="workflows.yaml"):
        preflight(qa_dir=tmp_qa_dir, app="x", runner="claude", probe_url=None)


def test_missing_auth_yaml_raises_with_template_hint(tmp_qa_dir):
    with pytest.raises(PreflightError, match="auth.yaml"):
        preflight(qa_dir=tmp_qa_dir, app="x", runner="claude", probe_url=None)


def test_dev_server_must_serve_body_marker(tmp_qa_dir, monkeypatch):
    # auth.yaml + workflows.yaml present and minimal-valid
    monkeypatch.setenv("QA_CUSTOMER_PASSWORD", "x")
    (tmp_qa_dir / "auth.yaml").write_text(
        "personas:\n"
        "  customer:\n"
        "    email: a@b\n"
        "    password_env: QA_CUSTOMER_PASSWORD\n"
        "    login: { type: email_password, route: /login, success_marker: hi }\n"
    )
    (tmp_qa_dir / "workflows.yaml").write_text(
        "app: x\nworkflows:\n"
        "  - { id: a, name: A, persona: customer, entry_route: /, test_data: {}, "
        "definition_of_done: ., do_not_change: ., regression_checks: [] }\n"
    )

    class FakeResp:
        def __init__(self, status, body): self.status_code, self.text = status, body
    def fake_get(url, **_):
        return FakeResp(200, "<html>nothing useful</html>")
    monkeypatch.setattr("preflight._http_get", fake_get)

    with pytest.raises(PreflightError, match="body marker"):
        preflight(qa_dir=tmp_qa_dir, app="x", runner="claude",
                  probe_url="http://localhost:3000", probe_marker=DEV_SERVER_PROBE_BODY_MARKER)


def test_codex_runner_requires_codex_on_path(tmp_qa_dir, monkeypatch):
    monkeypatch.setenv("QA_CUSTOMER_PASSWORD", "x")
    (tmp_qa_dir / "auth.yaml").write_text(
        "personas:\n"
        "  customer:\n"
        "    email: a@b\n"
        "    password_env: QA_CUSTOMER_PASSWORD\n"
        "    login: { type: email_password, route: /login, success_marker: hi }\n"
    )
    (tmp_qa_dir / "workflows.yaml").write_text(
        "app: x\nworkflows:\n"
        "  - { id: a, name: A, persona: customer, entry_route: /, test_data: {}, "
        "definition_of_done: ., do_not_change: ., regression_checks: [] }\n"
    )
    monkeypatch.setattr("preflight.shutil.which", lambda _: None)
    with pytest.raises(PreflightError, match="codex"):
        preflight(qa_dir=tmp_qa_dir, app="x", runner="codex", probe_url=None)
