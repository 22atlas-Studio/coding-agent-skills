"""Aggregate per-workflow findings into a single brief.md."""
# /// script
# requires-python = ">=3.13"
# dependencies = ["pydantic>=2.9", "jinja2>=3.1"]
# ///
from __future__ import annotations
from collections import Counter
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from findings_schema import WorkflowFinding, Verdict


_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, None: 4}
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _wall_clock_human(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s:02d}s"


def aggregate_brief(
    *, app: str, run_ts: str, runner: str, budget_usd: float,
    findings: list[WorkflowFinding], appended_count: int,
) -> str:
    counts: Counter[Verdict] = Counter(f.verdict for f in findings)
    bugs = sorted(
        [f for f in findings if f.verdict == "BUG"],
        key=lambda f: _SEVERITY_ORDER[f.severity],
    )
    blocked = [f for f in findings if f.verdict.startswith("BLOCKED")]
    inspect = [f for f in findings if f.verdict == "INSPECT"]

    cost_usd = sum(f.cost_usd for f in findings)
    wall_seconds = sum(f.wall_seconds for f in findings)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(disabled_extensions=("j2",), default=False),
        trim_blocks=False, lstrip_blocks=False,
    )
    tmpl = env.get_template("brief.md.j2")
    return tmpl.render(
        app=app, run_ts=run_ts, runner=runner,
        budget_usd=budget_usd, cost_usd=cost_usd,
        wall_clock_human=_wall_clock_human(wall_seconds),
        workflows_tested=len(findings), workflows_skipped=0,
        counts=dict(counts), bugs=bugs, blocked=blocked, inspect=inspect,
        appended_count=appended_count,
    )


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 6:
        print("usage: aggregate_brief.py <app> <run_ts> <runner> <budget_usd> <appended_count> <finding.json>...", file=sys.stderr)
        sys.exit(2)
    app, run_ts, runner = sys.argv[1], sys.argv[2], sys.argv[3]
    budget_usd, appended_count = float(sys.argv[4]), int(sys.argv[5])
    findings = [WorkflowFinding.model_validate(json.loads(Path(p).read_text())) for p in sys.argv[6:]]
    print(aggregate_brief(
        app=app, run_ts=run_ts, runner=runner,
        budget_usd=budget_usd, findings=findings, appended_count=appended_count,
    ))
