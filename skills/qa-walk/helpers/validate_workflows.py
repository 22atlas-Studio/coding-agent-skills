"""Validate qa/workflows.yaml against schema + auth.yaml personas."""
# /// script
# requires-python = ">=3.13"
# dependencies = ["pydantic>=2.9", "pyyaml>=6.0.2"]
# ///
from __future__ import annotations
import sys
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError, Field


class WorkflowValidationError(Exception):
    pass


class Workflow(BaseModel):
    id: str
    name: str
    persona: str
    entry_route: str
    test_data: dict[str, str] = Field(default_factory=dict)
    definition_of_done: str
    do_not_change: str = ""
    regression_checks: list[str] = Field(default_factory=list)


class WorkflowsFile(BaseModel):
    app: str
    last_scaffold: str | None = None
    workflows: list[Workflow]


def validate_workflows_file(path: Path, known_personas: set[str]) -> WorkflowsFile:
    raw = yaml.safe_load(path.read_text())
    try:
        wf = WorkflowsFile.model_validate(raw)
    except ValidationError as e:
        raise WorkflowValidationError(f"{path}: {e}") from e

    seen_ids: set[str] = set()
    for w in wf.workflows:
        if w.id in seen_ids:
            raise WorkflowValidationError(f"{path}: duplicate workflow id {w.id!r}")
        seen_ids.add(w.id)
        if w.persona not in known_personas:
            raise WorkflowValidationError(
                f"{path}: workflow {w.id!r} references persona {w.persona!r} "
                f"not declared in auth.yaml (known: {sorted(known_personas)})"
            )
    return wf


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: validate_workflows.py <workflows.yaml> <persona1,persona2,...>", file=sys.stderr)
        sys.exit(2)
    personas = set(sys.argv[2].split(","))
    try:
        validate_workflows_file(Path(sys.argv[1]), personas)
        print("ok")
    except WorkflowValidationError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
