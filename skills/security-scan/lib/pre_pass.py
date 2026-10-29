# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Deterministic security pre-pass.

Apply security-patterns.json rules across a repo and emit RawFinding[] JSON.
Stdlib only. Runnable as a script or importable (run_pre_pass).

Usage:
    uv run pre_pass.py <repo_root> <patterns.json> [--out -|<file>]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from globs import path_matches_any  # noqa: E402

# rule_name -> severity. Unknown rules default to "medium".
RULE_SEVERITY: dict[str, str] = {
    "hardcoded_secret_prefix": "critical",
    "service_role_in_client": "critical",
    "raw_auth_users_write": "high",
    "request_controlled_email_recipient": "high",
    "dom_injection_sink": "high",
    "expo_router_auth_push": "medium",
}

IGNORE_DIRS = {
    ".git", ".claude", "node_modules", "dist", "build", ".expo", ".next",
    "__pycache__", ".venv", "Pods", ".audit-run", "coverage",
}
MAX_BYTES = 1_000_000  # skip files larger than ~1 MB


def _iter_files(root: Path):
    root = root.resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Check only repo-relative parts to avoid false matches from the absolute path.
        rel_parts = path.relative_to(root).parts
        if any(part in IGNORE_DIRS for part in rel_parts):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
        except OSError:
            continue
        yield path


def _rule_hits(line: str, rule: dict) -> bool:
    subs = rule.get("substrings")
    if subs and any(s in line for s in subs):
        return True
    rx = rule.get("regex")
    if rx and re.search(rx, line):
        return True
    return False


def run_pre_pass(repo_root: Path, patterns: dict) -> list[dict]:
    # Resolve to absolute so relative_to() works against the absolute paths
    # _iter_files yields (it resolves root internally). The driver passes a
    # relative root like a downstream app directory.
    repo_root = Path(repo_root).resolve()
    rules = patterns.get("patterns", [])
    findings: list[dict] = []
    for path in _iter_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable
        applicable = []
        for rule in rules:
            inc = rule.get("paths")
            if inc and not path_matches_any(rel, inc):
                continue
            exc = rule.get("exclude_paths")
            if exc and path_matches_any(rel, exc):
                continue
            applicable.append(rule)
        if not applicable:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for rule in applicable:
                if _rule_hits(line, rule):
                    findings.append(
                        {
                            "severity": RULE_SEVERITY.get(rule["rule_name"], "medium"),
                            "confidence": "high",
                            "category": rule["rule_name"],
                            "file": rel,
                            "start_line": lineno,
                            "end_line": lineno,
                            "description": rule.get("reminder", rule["rule_name"]),
                            "suggestion": None,
                        }
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic security pre-pass")
    ap.add_argument("repo_root")
    ap.add_argument("patterns_json")
    ap.add_argument("--out", default="-")
    args = ap.parse_args(argv)

    patterns = json.loads(Path(args.patterns_json).read_text(encoding="utf-8"))
    findings = run_pre_pass(Path(args.repo_root), patterns)
    payload = json.dumps(findings, indent=2)
    if args.out == "-":
        sys.stdout.write(payload + "\n")
    else:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
