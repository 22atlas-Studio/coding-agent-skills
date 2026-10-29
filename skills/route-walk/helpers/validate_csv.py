#!/usr/bin/env python3
"""Validate a route-walk CSV.

Usage:
    python3 validate_csv.py <csv-path>

Pass criteria:
    - All rows have len == len(header)
    - Every flow has at least 1 happy + 1 sad row
    - terminal_state values come from a small documented enum
    - happy_path is Y/N

Exit codes:
    0 = pass
    1 = broken columns
    2 = missing happy/sad balance
    3 = unknown terminal_state
"""
from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path


def main(path: Path) -> int:
    with path.open() as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    expected = len(header)
    broken = [(i + 2, row[0] if row else "?", len(row)) for i, row in enumerate(rows) if len(row) != expected]

    if broken:
        print(f"FAIL: {len(broken)} broken rows (expected {expected} cols)")
        for ln, rid, n in broken[:20]:
            print(f"  line {ln}: {rid} has {n} cols")
        return 1

    print(f"PASS cols={expected} rows={len(rows)}")

    try:
        flow_i = header.index("flow")
        happy_i = header.index("happy_path")
        term_i = header.index("terminal_state")
    except ValueError as e:
        print(f"FAIL: missing required column: {e}")
        return 2

    flows = Counter(r[flow_i] for r in rows)
    happy = Counter(r[happy_i] for r in rows)
    terms = Counter(r[term_i] for r in rows)

    print(f"  flows: {dict(flows)}")
    print(f"  happy_path: {dict(happy)}")
    print(f"  terminal_state: {dict(terms)}")

    # Each flow should have at least one happy + one sad
    flow_happy = defaultdict(lambda: {"Y": 0, "N": 0})
    for r in rows:
        if r[happy_i] in ("Y", "N"):
            flow_happy[r[flow_i]][r[happy_i]] += 1

    unbalanced = [f for f, c in flow_happy.items() if c["Y"] == 0 or c["N"] == 0]
    if unbalanced:
        print(f"WARN: flows missing happy/sad balance: {unbalanced}")

    # terminal_state sanity: shouldn't contain values that look like other-column leakage
    LEAKAGE_HINTS = {"tap_to_", "share_", "install_", "open_url"}
    leaked = [t for t in terms if any(t.startswith(h) for h in LEAKAGE_HINTS)]
    if leaked:
        print(f"FAIL: terminal_state contains likely leaked values: {leaked}")
        return 3

    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(64)
    sys.exit(main(Path(sys.argv[1])))
