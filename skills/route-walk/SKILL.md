---
name: route-walk
description: Use when probabilistically enumerating every distinct user path through a built application and emitting a CSV route map. Reads the app's route files + state machines + tier/auth gates, identifies the decision axes that vary across paths, fills the cross-product (filtering impossible combos), and writes a `<DATE>-route-enumeration.csv` ready for QA coverage, demo planning, or PM communication. Triggers on `/route-walk <app>` or "enumerate every path through X" or "give me a probabilistic route map".
---

# Route Walk

Produces a decision-axis CSV that captures every realistic path a user can take through a built application. The CSV is the **input artifact** for `/qa-walk` (one CSV row = one walkable scenario) and the **deliverable** for PM/client communication ("here is every flow we have to test").

The column shape is the mandatory table later in this skill. Do not copy a route CSV out of a client tree.

## When to Use

- Pre-QA: before `/qa-walk` runs, so the walk has a coverage matrix instead of vibes
- Pre-demo: enumerating routes the operator might be asked to walk through
- Pre-sign-off: forcing a 1-to-1 between the feature list and exercised paths
- Pre-handoff: documenting the path surface for a takeover (a contractor or a new owner)
- When the user says "give me every path" / "enumerate every flow" / "make a route CSV"

## When NOT to Use

- Trivial apps under ~10 routes - write the list inline, no CSV needed
- Single-flow tools (a one-page checkout, a CLI) - no decision tree to enumerate
- Marketing sites - routes are static pages, no behavioral branches worth enumerating

## Args

`/route-walk <app> [--out <path>] [--max-rows <n>]`

- `<app>` - directory slug under `~/projects/<app>/` or `products/<app>/`
- `--out` - CSV path (default: `~/projects/<app>/docs/<DATE>-route-enumeration.csv`)
- `--max-rows` - soft cap, default 200; warn rather than error if exceeded

If no `<app>` is given, scan `~/projects/*/PROJECT.md` and ask which one.

## Process

### 1. Preflight

Locate the app:
- `~/projects/<app>/app/` (mobile/web app subdir)
- `~/projects/<app>/` (root)
- `products/<app>/` (non-client product)

Read for context (in parallel):
- `PROJECT.md` - phase, features, tier model, decisions
- `app/src/app/_layout.tsx` + `(auth)/_layout.tsx` + `(app)/_layout.tsx` (Expo Router) OR `app/page.tsx` / `routes/` (Next/React Router)
- The auth store / entitlement store / mode store - these define the highest-cardinality axes
- Any state machine files (XState, custom reducers) - every transition is a row candidate

If the app has neither `PROJECT.md` nor a discoverable route tree, ask the user to point at the entry surface - do not guess.

### 2. Identify Decision Axes

A decision axis is a column where the value materially changes which screens, services, or outcomes the user sees. Mine them in this order:

1. **Entry point** - cold_launch, returning_signed_in, push_tap, deep_link, share_link
2. **Auth state** - signed_out, anonymous_guest, registered, registered_onboarded
3. **Auth method** - email_register, email_login, sso, password_reset, guest_session, magic_link
4. **Tier / role / RBAC** - read the entitlement store enum (e.g. `guest | customer | staff | admin`)
5. **Theme / palette / locale** - read the ThemeProvider tier→palette resolver if present
6. **Start surface** - every screen reachable from the root layout
7. **Per-surface choices** - filters, visit mode (in_person/video/phone), service category, payment methods
8. **Outcome axes** - success / abandoned / error / timeout / declined (mirror the actual code branches)
9. **Terminal state** - BOOKED, CONFIRMED, CANCELLED, EXITED, ABANDONED, SIGNED_OUT, ERROR, etc.
10. **Cross-cutting flags** - happy_path Y/N, coverage_notes (file path + 1-line WHY)

Aim for ~15-30 columns. Fewer is fine for simple apps; more produces noise.

**Anti-pattern:** don't invent axes that aren't in the code. Every column must be backed by a real branch - a `switch`, an `if (tier === ...)`, a state machine transition, a feature flag, a router push with conditional params. If you can't cite a file:line for an axis, drop it.

### 3. Probabilistic Enumeration

For each flow (AUTH, BOOK, APPT, etc.):

1. Start with the **happy path** (most common values for every axis)
2. Walk each axis and emit one row per **realistic variant**:
   - 4-tier RBAC → 4 rows for tier-dependent surfaces (but ONLY where tier visibly matters - skip "staff views the about page")
   - Card vs Apple Pay → 2 rows where iOS gating splits the branch
   - Reschedule counter loops → 2-3 counter-depth rows (not one row per counter; that's combinatorial explosion)
3. Add **sad paths**: error states, abandonment points, timeout edges, permission denials, network failures
4. Add **edge paths**: deep-link variants, offline launch, expired session refresh, cached entitlement

**Filtering rule:** drop rows that violate code invariants. Examples:
- `auth_state=signed_out` × `tier=premium` is impossible (premium requires auth)
- `visit_mode=video` × `tier=guest` is impossible (a video visit requires a signed-in customer)
- `payment_method=apple_pay` × `Platform.OS=android` is impossible

If unsure whether a combo is reachable, grep for a guard. No guard → keep the row and call it out in `coverage_notes`.

### 4. Build the CSV

ALWAYS use `csv.DictWriter` to write the file. Column drift is the #1 failure mode of hand-edited route CSVs (a hand-written 130-row CSV had 72 broken rows due to inconsistent NA padding).

Pattern (drop into a `/tmp/build_route_csv.py` and run):

```python
import csv

COLS = ['route_id', 'flow', 'entry_point', 'auth_state', ..., 'happy_path', 'coverage_notes']

def R(**kw):
    row = {c: 'NA' for c in COLS}
    row.update(kw)
    return row

ROWS = [
    R(route_id='AUTH-001', flow='AUTH', entry_point='cold_launch', ..., happy_path='Y',
      coverage_notes='Files+line: (auth)/welcome.tsx:14 signInAnonymously'),
    # ...
]

with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    [w.writerow(r) for r in ROWS]
```

Naming: `route_id` is `<FLOW>-<NNN>` zero-padded to 3 digits (BOOK-001, APPT-014). Keep flow prefixes 3-5 chars.

### 5. Validate

After writing, run this validator (always - don't skip):

```bash
python3 -c "
import csv
with open('<csv-path>') as f:
    r = csv.reader(f)
    h = next(r); rows = list(r)
broken = [(i+2, row[0], len(row)) for i, row in enumerate(rows) if len(row) != len(h)]
print(f'cols={len(h)} rows={len(rows)} broken={len(broken)}')
from collections import Counter
print('flow:', dict(Counter(r[1] for r in rows)))
print('happy:', dict(Counter(r[h.index(\"happy_path\")] for r in rows)))
print('terminals:', dict(Counter(r[h.index(\"terminal_state\")] for r in rows)))
[print(b) for b in broken[:10]]
"
```

Pass criteria:
- `broken == 0`
- Every flow has at least 1 happy + 1 sad row
- `terminal_state` only contains values from the documented enum (no column-drift leakage)
- Tier distribution roughly matches the app's intended user mix (a B2C app shouldn't be 95% guest)

### 6. Print Report

```
route-walk complete: <app>
  CSV: <out-path>
  Rows: <N> (<happy-count> happy / <sad-count> sad)
  Flows: <flow-distribution>
  Tiers: <tier-distribution>
  Terminal states: <state-distribution>

Next: /qa-walk <app> --workflows '<flow>-*' to execute a Tier-1 subset
       OR ship the CSV directly as PM/client artifact
```

## Output Shape - Mandatory Columns

Every route-walk CSV must include these baseline columns (rename to fit app vocabulary, but keep the slot):

| Column | Purpose |
|--------|---------|
| `route_id` | `<FLOW>-<NNN>` stable identifier; never reused even after deletion |
| `flow` | Top-level category (AUTH, BOOK, APPT, …) - 3-5 char prefix |
| `entry_point` | How the user arrives at the start surface |
| `auth_state` | signed_out / anonymous_guest / registered / registered_onboarded |
| `terminal_state` | What state the row ends in (BOOKED, CONFIRMED, CANCELLED, EXITED, ABANDONED, ERROR, …) |
| `happy_path` | Y/N - does this row represent the intended success path |
| `coverage_notes` | One-line WHY + ideally a `file:line` citation |

App-specific axes go between `auth_state` and `terminal_state`. Order them logically (surface → choice → outcome).

## Anti-Patterns

- **Hand-writing rows without DictWriter** → column drift, broken CSV
- **Cartesian explosion** - 5 tiers × 6 filters × 4 modes × 3 payments × 2 outcomes = 720 rows of mostly-NA → unusable; trim to ~150 rows max by collapsing axes that don't visibly diverge
- **Inventing axes** - if a column has no branch in code, drop it
- **Skipping sad paths** - a CSV with only happy paths is a smoke list, not a coverage matrix
- **Reusing row IDs across runs** - append new IDs; never re-map BOOK-007 to a different scenario

## Files

- `helpers/validate_csv.py` - the validator from step 5, broken out for reuse

## Related

- **`/qa-walk`** consumes the CSV: each row maps to a goal-feature pair the QA agent walks
- **`code-review`** skill: similar decision-axis mining but for code structure, not user paths
- Column shape: the mandatory columns table in this skill. Do not treat a client CSV as the reference copy.
