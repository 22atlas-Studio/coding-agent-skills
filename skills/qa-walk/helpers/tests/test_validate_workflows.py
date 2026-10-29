import pytest
from validate_workflows import validate_workflows_file, WorkflowValidationError


def test_valid_workflows_pass(fixtures_dir):
    known_personas = {"dealer", "customer"}
    result = validate_workflows_file(fixtures_dir / "valid_workflows.yaml", known_personas)
    assert result.app == "example-app"
    assert len(result.workflows) == 1


def test_duplicate_ids_rejected(fixtures_dir):
    known_personas = {"dealer", "customer"}
    with pytest.raises(WorkflowValidationError, match="duplicate"):
        validate_workflows_file(fixtures_dir / "invalid_workflows_duplicate_id.yaml", known_personas)


def test_unknown_persona_rejected(fixtures_dir):
    known_personas = {"dealer", "customer"}
    with pytest.raises(WorkflowValidationError, match="ghost"):
        validate_workflows_file(fixtures_dir / "invalid_workflows_persona_mismatch.yaml", known_personas)
