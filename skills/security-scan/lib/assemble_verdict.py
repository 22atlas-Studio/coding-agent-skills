# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Assemble a security-scan verdict + report from synthesized findings.

Reads findings.json (RawFinding[]), writes latest.json and a markdown report.
Stdlib only. Importable (compute_counts/decide_verdict/render_report) and runnable.

Usage:
    uv run assemble_verdict.py <findings.json> --security-dir <dir> \
        --app-name <name> [--base-sha <sha>] [--codex] \
        [--fail-on critical,high] [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low")
_SEV_ORDER = {s: i for i, s in enumerate(SEVERITIES)}


def compute_counts(findings: list[dict]) -> dict[str, int]:
    counts = {s: 0 for s in SEVERITIES}
    for f in findings:
        sev = f.get("severity")
        if sev in counts:
            counts[sev] += 1
    return counts


def decide_verdict(counts: dict[str, int], fail_on: set[str]) -> str:
    if any(counts.get(s, 0) > 0 for s in fail_on):
        return "FAIL"
    if sum(counts.values()) > 0:
        return "PASS_WITH_WARNINGS"
    return "PASS"


def render_report(findings: list[dict], meta: dict) -> str:
    counts = meta["counts"]
    lines: list[str] = []
    lines.append(f"# Security Scan - {meta['app_name']}")
    lines.append("")
    lines.append(f"- Date: {meta['date']}")
    lines.append(f"- Verdict: **{meta['verdict']}**")
    lines.append(
        f"- Counts: critical={counts['critical']} high={counts['high']} "
        f"medium={counts['medium']} low={counts['low']}"
    )
    lines.append(f"- Base SHA: {meta.get('base_sha') or 'n/a'}")
    lines.append(f"- Codex cross-check: {'on' if meta.get('codex') else 'off'}")
    lines.append("")
    if not findings:
        lines.append("## Findings")
        lines.append("")
        lines.append("No findings. All scanned scopes are clean.")
        lines.append("")
        return "\n".join(lines)
    lines.append("## Findings")
    lines.append("")
    lines.append("| # | Severity | Category | Issue | File:Line | Fix direction |")
    lines.append("|---|----------|----------|-------|-----------|---------------|")
    for i, f in enumerate(findings, start=1):
        loc = f["file"]
        if f.get("start_line") is not None:
            loc = f"{loc}:{f['start_line']}"
        issue = str(f.get("description", "")).replace("|", "/")
        fix = str(f.get("suggestion") or "-").replace("|", "/")
        lines.append(
            f"| {i} | {f['severity']} | {f.get('category', '')} | {issue} | {loc} | {fix} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Assemble security-scan verdict + report")
    ap.add_argument("findings_json")
    ap.add_argument("--security-dir", required=True)
    ap.add_argument("--app-name", required=True)
    ap.add_argument("--base-sha", default=None)
    ap.add_argument("--codex", action="store_true")
    ap.add_argument("--fail-on", default="critical,high")
    ap.add_argument("--date", default=None)
    args = ap.parse_args(argv)

    findings = json.loads(Path(args.findings_json).read_text(encoding="utf-8"))
    findings.sort(key=lambda f: (_SEV_ORDER.get(f.get("severity"), 99), f.get("file", "")))
    counts = compute_counts(findings)
    fail_on = {s.strip() for s in args.fail_on.split(",") if s.strip()}
    verdict = decide_verdict(counts, fail_on)
    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    latest = {
        "verdict": verdict,
        "scanned_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base_sha": args.base_sha,
        "codex": args.codex,
        "counts": counts,
        "findings": findings,
    }

    sec_dir = Path(args.security_dir)
    sec_dir.mkdir(parents=True, exist_ok=True)
    (sec_dir / "latest.json").write_text(json.dumps(latest, indent=2) + "\n", encoding="utf-8")

    meta = {"app_name": args.app_name, "date": date, "verdict": verdict,
            "counts": counts, "base_sha": args.base_sha, "codex": args.codex}
    report = render_report(findings, meta)
    (sec_dir / f"{date}-security-scan.md").write_text(report, encoding="utf-8")

    # Compact inline summary for the interactive caller.
    sys.stdout.write(
        f"{verdict} - critical={counts['critical']} high={counts['high']} "
        f"medium={counts['medium']} low={counts['low']}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
