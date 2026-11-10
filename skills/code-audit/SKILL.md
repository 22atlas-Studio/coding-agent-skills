---
name: code-audit
description: Use when the user says "audit my code", "is this safe to ship", "what's wrong with this codebase", "review the whole repo" or "find the bugs before launch". Reads the whole repo, ranks what it finds as P1, P2 or P3, and writes a report with a file and line for every finding.
---

# Code audit

Load the `build-rules` skill first and follow it throughout.

An audit reads the whole repo and answers one question: what could hurt the user's users or
the user's business if this ships today. It reports. It does not change code. Fixes come
later, as slices, after the user agrees.

## Severity

| Level | Meaning | Examples |
|---|---|---|
| P1 | Blocks shipping | Data loss, one account reading another's data, a secret in the repo, a payment or login flow that can fail silently |
| P2 | Should fix soon | Missing error handling on a real failure, a check that skips on bad input, a flow with no test |
| P3 | Polish | Dead code, a file grown too large to read, unclear names, stale comments |

## 1. Map the repo first

Do not judge anything until you can say what the app is. Collect:

```bash
git ls-files | head -200
git log --oneline -20
```

Then read the README, the dependency file (`package.json`, `pyproject.toml`, `requirements.txt`,
`Gemfile`, `go.mod`), the config for the host (Vercel, Docker, CI files) and the project's
test command. Write a short map: what the app does, where requests come in, where data is
stored, which outside services it calls, and how it is deployed. Put the map at the top of the
report. If a later finding contradicts the map, fix the map.

## 2. Check each area

Work through these in order. For each one, search the whole repo for the pattern, then read the
hits.

1. **Correctness.** Money, dates and time zones, rounding, off-by-one on lists and pages, code
   paths that return success when the work did not happen.
2. **Security.** Run the `security-scan` skill's checklist. Fold its P1 items into this report.
3. **Data loss.** Deletes without a check, writes that overwrite instead of merge, migrations
   with no way back, jobs that can run twice.
4. **Error handling.** Empty `catch` blocks, errors turned into a blank screen or a 200, calls
   to outside services with no timeout or retry limit.
5. **Tests that cannot fail.** Tests with no assertion, assertions on the mock instead of the
   code, skipped tests, snapshots nobody reads. Pick the five most important tests and break the
   code they cover on purpose. A test that stays green is a finding.
6. **Dead code and file bloat.** Unused files and exports, copies of the same logic, files over
   about 500 lines that mix several jobs.

## 3. Write each finding so it can be checked

Every finding has four parts:

```
[P1] One-line title - path/to/file.ts:42
What fails: the concrete thing that goes wrong, for a named user, in plain words.
How to see it: the command, request or click that shows it.
Fix direction: the smallest change that closes it.
```

No file and line, no finding. "Could be a problem" is not a finding. Say what breaks and for
whom.

## 4. Re-check every P1

A first-pass finding is a guess. For each P1, go back to the code and try to prove it wrong:
read the callers, read the guard above it, run the request if you can. Mark it `confirmed` with
the evidence, or drop it. Say how many first-pass P1s were dropped.

## 5. Write the report

Write `.build-loop/reviews/YYYY-MM-DD-audit.md` (today's date) with these sections:

1. Verdict in one sentence: ship, fix first, or stop.
2. The repo map.
3. P1 findings, then P2, then P3.
4. What was not checked and why (no staging site, no test database, a folder skipped).
5. Commands you ran and their results.

Never paste a secret into the report. Show a fingerprint (length, first 4, last 4).

## 6. Turn findings into slices after the user agrees

Show the user the verdict and the P1 and P2 list. Ask which to fix. Only then add slices to
`.build-loop/plan.md`, one per fix or per group of fixes in the same file, each with status
`pending`. Each slice names the finding it closes. A fix for a pattern covers every place the
pattern appears.

## Report to the user

- The verdict and the count of P1, P2 and P3.
- The three findings that matter most, in plain words.
- The path to the report.
- What was not checked.

**Stop** for the plan gate. Wait for the user to say which findings to turn into slices.
