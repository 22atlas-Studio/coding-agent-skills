"""Render goal.md from a workflow + persona context."""
# /// script
# requires-python = ">=3.13"
# dependencies = ["pyyaml>=6.0"]
# ///
from __future__ import annotations

from pathlib import Path
from typing import Mapping


GOAL_TEMPLATE_HEAD = """# Goal: {name}

## Context
- App: {app}
- Persona: {persona} (logged in as {email})
- Entry route: {resolved_route}

## Definition of Done
{definition_of_done}
"""

GOAL_TEMPLATE_REGRESSION = """
## Regression checks (these have failed before and must not fail now)
{regression_lines}
"""

GOAL_TEMPLATE_TAIL = """
## Do not change
{do_not_change}

## Response format

On every iteration, write to `state.yaml`:

```yaml
iteration: <n>
current_step: <one-line description>
evidence_captured: [<screenshot paths>, <network capture paths>]
blocking_observations: [<things preventing progress>]
candidate_verdict: PASS | BUG | BLOCKED-AUTH | BLOCKED-DEPENDENCY | BLOCKED-DEV-SERVER | INSPECT | NOT_YET
```

Mark the goal achieved ONLY when the audit shows the Definition of Done
has actually been met. Do not accept proxy signals (URL changed, button
was clicked) as completion. If you observe a bug, set
candidate_verdict=BUG and stop - don't try to fix it. If you cannot
proceed, set candidate_verdict=BLOCKED-* with a one-line reason.

When you set a final verdict, write `findings.json` next to `state.yaml`
following the schema in `qa-walk/helpers/findings_schema.py`.
"""


def load_fixtures(qa_dir: Path | str | None) -> dict[str, str]:
    """Load qa/fixtures.yaml if present. Returns {} when missing.

    The runner-side resolution lets a workflow declare
    `test_data: { deal_id: from-fixture }` and have it become the real
    seeded UUID at goal.md render time, without each runner having to
    re-discover the deal via API/SQL.
    """
    if qa_dir is None:
        return {}
    fixtures_path = Path(qa_dir) / "fixtures.yaml"
    if not fixtures_path.exists():
        return {}
    import yaml  # imported lazily so unit tests that don't pass qa_dir don't need it
    raw = yaml.safe_load(fixtures_path.read_text()) or {}
    return {str(k): str(v) for k, v in (raw.get("fixtures") or {}).items()}


def _resolve_value(value, fixtures: Mapping[str, str], key: str) -> str:
    """Translate `from-fixture` → `fixtures[key]`. Other values pass through."""
    if str(value) == "from-fixture":
        if key not in fixtures:
            raise KeyError(
                f"test_data['{key}'] = from-fixture but qa/fixtures.yaml has no '{key}' entry"
            )
        return fixtures[key]
    return str(value)


def generate_goal(
    app: str,
    workflow: dict,
    persona: dict,
    *,
    qa_dir: Path | str | None = None,
) -> str:
    fixtures = load_fixtures(qa_dir)
    resolved_route = workflow["entry_route"]
    for key, value in (workflow.get("test_data") or {}).items():
        resolved = _resolve_value(value, fixtures, key)
        resolved_route = resolved_route.replace("{" + key + "}", resolved)

    out = GOAL_TEMPLATE_HEAD.format(
        name=workflow["name"],
        app=app,
        persona=workflow["persona"],
        email=persona["email"],
        resolved_route=resolved_route,
        definition_of_done=workflow["definition_of_done"].rstrip(),
    )

    regression_checks = workflow.get("regression_checks") or []
    if regression_checks:
        regression_lines = "\n".join(f"- {line}" for line in regression_checks)
        out += GOAL_TEMPLATE_REGRESSION.format(regression_lines=regression_lines)

    out += GOAL_TEMPLATE_TAIL.format(do_not_change=workflow["do_not_change"].rstrip())
    return out


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) not in (4, 5):
        print(
            "usage: generate_goal.py <app> <workflow.json> <persona.json> [<qa-dir>]",
            file=sys.stderr,
        )
        sys.exit(2)
    app = sys.argv[1]
    workflow = json.loads(open(sys.argv[2]).read())
    persona = json.loads(open(sys.argv[3]).read())
    qa_dir = sys.argv[4] if len(sys.argv) == 5 else None
    print(generate_goal(app, workflow, persona, qa_dir=qa_dir))
