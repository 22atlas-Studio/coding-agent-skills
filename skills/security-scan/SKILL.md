---
name: security-scan
description: Routine internal whole-repo security gate for your apps. Scans one app against its own .claude/claude-security-guidance.md threat model + security-patterns.json, fans out parallel read-only security reviewers, triages findings, and writes an internal report + latest.json verdict. Use for "/security-scan <app>" or "is <app> secure to ship". Use security-audit for a high-assurance coverage-led audit with independently verified records. Do not use for client-facing paid audits, scoped diff review, or per-edit checks.
---

# security-scan - internal whole-repo security gate

Replicates a gated pattern (map, scan with subagents, triage, report). The stages are in this file. Output shapes are in `CONTRACT.md`. There is no separate scanner program in this library.

## Invocation modes

- Interactive (primary): `/security-scan <app>` or `/security-scan` from inside an app dir. Print the verdict + findings table inline; write the report to the app's `security/` folder. No separate pipeline gate, no base SHA, no CI context required.
- Headless: a pipeline gate can run the same flow and consume `latest.json`.

## Flow

### 1. Resolve target + load threat model
- Resolve `<app>` from `~/projects/<app>/`; if it has an `app/` subdir with a `.claude/`, that is the scan root. If `<app>` is omitted, use cwd if it contains `.claude/claude-security-guidance.md`.
- Require `<root>/.claude/claude-security-guidance.md` AND `<root>/.claude/security-patterns.json`. If either is missing: STOP. Tell the user to add both files. Do NOT synthesize a threat model.
- Engine Stage 1: capture app name, framework + versions, LOC, last-commit date.
- Pick the run dir: `RUN=<root>/security/.scan-run-$(date +%Y-%m-%d-%H%M)`; create `$RUN/_partials/`.

### 2. Deterministic pre-pass
Run the pattern matcher and keep its output for synthesis:
```bash
uv run "$HOME/.agents/skills/security-scan/lib/pre_pass.py" <root> <root>/.claude/security-patterns.json --out "$RUN/_partials/pre-pass.json"
```

### 3. Fan-out scanning subagents (engine Stage 2, parallel, ONE message, read-only)
Dispatch together:
- The guided security reviewer using `reviewers/security-guided.md`, with the FULL text of `<root>/.claude/claude-security-guidance.md` prepended as the gating standard, output to `$RUN/_partials/security-guided.md`.
- A second read-only security reviewer, same gating standard, output to `$RUN/_partials/security-auditor.md`.
- If `<root>/supabase/` exists, a third reviewer scoped to RLS/IDOR (service-role usage + ownership checks), output to `$RUN/_partials/rls-idor.md`.
Each reviewer is read-only and emits P0-P3 findings with file:line, or `No security findings.`

### 4. Synthesize (engine Stage 3) -> findings.json
You (main agent) read every partial plus `pre-pass.json` and produce `$RUN/findings.json` (a RawFinding[] per CONTRACT.md):
- Dedupe by file + start_line + root cause (keep the more specific; the deterministic pre-pass wins on exact-line secret/RLS hits).
- Map P0->critical, P1->high, P2->medium, P3->low. confidence: pre-pass=high; reviewer findings carry the reviewer's confidence (default medium).
- category = a short label; description = one sentence; suggestion = smallest fix direction or null.
- Invent nothing no reviewer flagged.

### 5. Codex cross-check (engine Stage 4) - OPT-IN
Only if `--codex` was passed. Follow engine Stage 4 EXACTLY (direct-redirect `>` never pipe, `--base` only, Monitor until-loop, silent-exit guard). Reconcile per the engine. If Codex is silent/unauthenticated: set the gate verdict fail-closed (FAIL) but still ship the report; note it under Residual Risk.

### 6. Assemble verdict + report
```bash
uv run "$HOME/.agents/skills/security-scan/lib/assemble_verdict.py" "$RUN/findings.json" \
  --security-dir <root>/security --app-name <app> \
  $( [ -n "$BASE_SHA" ] && echo --base-sha "$BASE_SHA" ) \
  $( [ "$CODEX" = 1 ] && echo --codex )
```
Then delete `$RUN/_partials/` and the run dir (keep only `security/<date>-security-scan.md` + `security/latest.json`).

Interactive: print the verdict line and the findings table from the report to chat. Headless: leave `latest.json` for the caller.

## Boundaries
- This skill: internal, whole-repo, our apps, read-only, report + verdict.
- security-audit: high-assurance coverage ledger, adversarial candidate validation, independently verified records, and durable report artifacts.
- full-code-audit: a broader external audit, not this gate.
- code-review: our broad pre-ship pass that fixes.
- security-guidance plugin: per-edit / end-of-turn, not whole-repo.

## Common mistakes
| Mistake | Fix |
|---------|-----|
| Synthesizing a threat model when the guidance file is missing | STOP. Tell the user to add both required files. Do not synthesize a threat model. |
| Reviewers editing code | Read-only analysis only |
| Piping Codex output | Direct-redirect `>` only |
| Emitting BLOCKER/HIGH in latest.json | Use lowercase critical/high/medium/low (the RawFinding severities) |
| Leaving the run dir behind | Delete `_partials/` and `.scan-run-*` after assembly |
