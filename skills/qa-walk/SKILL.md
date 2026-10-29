---
name: qa-walk
description: Use when running an end-to-end QA pass on a built application. Walks every user workflow with an autonomous goal-driven agent, produces a consolidated brief mirrored to Obsidian, and appends regression checks. Triggers on `/qa-walk APP`, "QA walk this app", "smoke pass on X", or "run end-to-end QA".
---

# QA Walk

Autonomous E2E QA via a goal-feature pattern: one workflow, one definition of done, one findings file.

## When to Use

- Pre-ship smoke pass before a client handoff or App Store submission
- After a feature merge that touches multiple flows
- When Sean says "QA walk <app>" or invokes `/qa-walk <app>`

## Args

`/qa-walk <app> [--runner codex|claude] [--budget-usd <cap>] [--workflows <glob>] [--no-regression-append]`

Defaults: `--runner codex`, `--workflows '*'`. Codex is default per cross-model verification (Sean prefers Codex over Claude for verification passes; same-model self-verification is theatrically defective). The spend cap is optional. Do not put a price in the note you write back.

## Codex Setup (one-time per host)

Codex CLI ships with **zero MCP servers and no browser** by default. Before running `--runner codex` against a web app, do this once on the host:

```bash
codex mcp add playwright -- npx -y @playwright/mcp@latest
codex mcp list   # confirm 'playwright' shows enabled
```

The runner invocation that works on Codex CLI 0.130.0:

```bash
cat goal.md | codex exec \
    --skip-git-repo-check \
    -C <workspace-dir>
```

Why each flag:
- **`exec`** subcommand: non-interactive. The older `codex --no-interactive` flag is gone.
- **Do not disable the sandbox.** If the sandbox cannot reach the dev server, stop with `BLOCKED-DEV-SERVER` and fix the sandbox policy. This library does not ship a permissions bypass.
- **`--skip-git-repo-check`**: `qa/runs/*` workspaces aren't their own git repos.
- **Prompt via stdin**, not `--goal <file>`: matches Codex 0.130.0 prompt-source semantics.
- **No `--max-iterations`**: Codex self-manages iteration cap. The `goal.md` should instruct "stop on terminal verdict" so it doesn't loop indefinitely.

A 3-iteration localhost walk is on the order of 125K tokens. Scope the workflow list before launching a batch.

## Process

### 1. Preflight

Resolve `<app>` to its `qa/` directory:
- `<app>/qa/` inside the app checkout, else error: "no qa/ directory for app <app>"

Run:

```bash
cd .agents/skills/qa-walk/helpers
uv run python preflight.py --qa-dir <resolved-qa-dir> --app <app> --runner <runner> --probe-url <dev-server-url>
```

The `--probe-url` is read from `qa/qa.yaml::dev_server_url` if present, else inferred (`http://localhost:5173` for Vite, `http://localhost:3000` for Next.js, `http://localhost:8081` for Expo Web). If preflight fails, emit the error verbatim and stop.

### 2. Cluster by persona

Read `qa/workflows.yaml`. Group workflows by `persona`. Cap concurrency at 4 personas - if more, run remaining personas after the first batch.

### 3. Per-workflow loop (within a persona cluster, serial)

For each persona, dispatch ONE runner instance. The runner:

1. Runs `bypass.command` from auth.yaml if defined (shell-passthrough via `subprocess.run(cmd, shell=True)`).
2. Logs in once via the persona's `login` strategy.
3. For each workflow in this persona (sequential):
   - Generate `goal.md`:
     ```bash
     uv run python .agents/skills/qa-walk/helpers/generate_goal.py \
       <app> <workflow.json> <persona.json> <qa-dir> > <run-dir>/workflows/<id>/goal.md
     ```
     Pass the resolved `<qa-dir>` (the app's `qa/` directory) so
     `test_data: { <key>: from-fixture }` placeholders resolve against
     `<qa-dir>/fixtures.yaml`. The arg is optional - workflows that
     don't use `from-fixture` work without a fixtures file.
   - Invoke the runner:
     - **Codex**: `.agents/skills/qa-walk/runners/codex.sh <run-dir>/workflows/<id> <run-dir>/workflows/<id>/goal.md`
     - **Claude**: dispatch a subagent via the Agent tool with `runners/claude/goal-prompt.md` + `goal.md` as the system prompt; subagent has access to Playwright MCP; subagent writes `findings.json` to its workspace.
   - Capture screenshots on every state transition into `<run-dir>/workflows/<id>/screenshots/`.
   - Log all 4xx/5xx into `<run-dir>/network.jsonl`.
   - Stop on iteration cap (12), budget cap, time cap (60 min), or terminal verdict.

If `--budget-usd` cap reached mid-run: mark all unwalked workflows BLOCKED-BUDGET and proceed to step 4.

### 4. Aggregate

Pre-compute `appended_count` from BUG findings (count of findings with verdict=BUG that have a `suggested_regression_check`).

```bash
uv run python .agents/skills/qa-walk/helpers/aggregate_brief.py \
  <app> <run_ts> <runner> <budget_usd> <appended_count> \
  <run-dir>/workflows/*/findings.json > <run-dir>/brief.md
```

Also write `<run-dir>/findings.json` with the run-level RunFinding aggregate.

### 5. Mirror to Obsidian

```bash
uv run python .agents/skills/qa-walk/helpers/mirror_obsidian.py \
  <run-dir>/brief.md <app> <run_ts>
```

If vault unreachable, helper prints a warning and continues.

### 6. Append regression checks (unless --no-regression-append)

```bash
uv run python .agents/skills/qa-walk/helpers/append_regression.py \
  <qa-dir>/workflows.yaml \
  <run-dir>/findings.json \
  <run_ts>
```

Then commit, with an explicit pathspec limited to the qa files this run changed:

```bash
git add <qa-dir>/workflows.yaml \
        <qa-dir>/runs/<run_ts>/brief.md \
        <qa-dir>/runs/<run_ts>/findings.json
git commit -m "qa: regression checks from <run_ts>" -- <qa-dir>
```

(`runs/<ts>/screenshots/`, `transcript.log`, per-workflow `state.yaml`, and `network.jsonl` are gitignored - only brief.md + findings.json land in git.)

### 7. Report to Sean

Print the brief.md content + the path to the run dir + the path to the Obsidian mirror.

## Helpers

All helpers live at `.agents/skills/qa-walk/helpers/` and are uv-runnable Python:

| Helper | Purpose |
|---|---|
| `validate_auth.py` | Schema + env-var checks on `qa/auth.yaml` |
| `validate_workflows.py` | Schema + persona-cross-check on `qa/workflows.yaml` |
| `generate_goal.py` | Render `goal.md` for one workflow |
| `aggregate_brief.py` | Per-workflow `findings.json` -> `brief.md` |
| `append_regression.py` | BUG findings -> `regression_checks` lines (idempotent) |
| `mirror_obsidian.py` | Copy `brief.md` to `$QA_NOTES_DIR/QA/<app>/<ts>/` when that directory is set |
| `preflight.py` | All-of-the-above plus dev-server probe and Codex-on-PATH check |
| `findings_schema.py` | Pydantic models for the findings JSON contract |

## Verdict types

`PASS` | `BUG` | `BLOCKED-AUTH` | `BLOCKED-DEPENDENCY` | `BLOCKED-BUDGET` | `BLOCKED-DEV-SERVER` | `INSPECT`

Severity for BUG: `critical` | `high` | `medium` | `low`.

## What's NOT in v1

Native mobile (Maestro), Slack draft / Linear filing, CI/cron mode, visual regression diffing, multi-app `/qa-walk all`, Flutter. See spec.

## Reference

The design notes that motivated this skill are not in this library. The runnable surface is this directory: helpers, runners, and templates.
