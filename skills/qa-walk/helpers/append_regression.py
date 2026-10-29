"""Append regression_checks to workflows.yaml from BUG findings. Idempotent."""
# /// script
# requires-python = ">=3.13"
# dependencies = ["pyyaml>=6.0.2"]
# ///
from __future__ import annotations
import sys
from pathlib import Path
import yaml


def _format_check(suggested: str, run_ts: str) -> str:
    return f"{suggested} (bug from run {run_ts})"


def append_regression_checks(workflows_path: Path, findings: list[dict], run_ts: str) -> int:
    """Append one regression_check per BUG finding. Returns the number appended.

    Idempotent: re-running with the same findings does not duplicate.
    """
    data = yaml.safe_load(workflows_path.read_text())
    by_id = {w["id"]: w for w in data["workflows"]}
    appended = 0

    for f in findings:
        if f.get("verdict") != "BUG":
            continue
        suggested = f.get("suggested_regression_check")
        if not suggested:
            continue
        wf = by_id.get(f["workflow_id"])
        if wf is None:
            continue
        wf.setdefault("regression_checks", [])
        line = _format_check(suggested, run_ts)
        # Idempotence: dedupe by suggested-prefix so re-running with the same
        # suggestion (or same suggestion at a different run_ts) does not add twice.
        prefix = suggested.strip()
        if any(c.startswith(prefix) for c in wf["regression_checks"]):
            continue
        wf["regression_checks"].append(line)
        appended += 1

    if appended > 0:
        workflows_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return appended


if __name__ == "__main__":
    import json
    if len(sys.argv) != 4:
        print("usage: append_regression.py <workflows.yaml> <run_findings.json> <run_ts>", file=sys.stderr)
        sys.exit(2)
    findings = json.loads(Path(sys.argv[2]).read_text())
    n = append_regression_checks(Path(sys.argv[1]), findings, sys.argv[3])
    print(f"appended {n}")
