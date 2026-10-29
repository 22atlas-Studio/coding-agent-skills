#!/usr/bin/env bash
# qa-walk Codex runner. Invokes `codex exec` against a goal.md and writes findings.json.
#
# Usage:
#   codex.sh <workspace-dir> <goal.md path>
#
# Exit codes:
#   0  workflow completed (verdict in findings.json)
#   1  Codex invocation failed (no findings.json produced)
#   2  preflight (binary missing, args wrong, playwright MCP missing)
#
# Validated invocation (Codex CLI 0.130.0, example app tracer 2026-05-12):
#   - `codex exec` is the non-interactive subcommand (was `codex --no-interactive` in spec; that flag is gone)
#   - Prompt goes via stdin, NOT --goal
#   - Do not pass a sandbox bypass. If localhost is blocked, exit and report BLOCKED-DEV-SERVER.
#   - Workspace dirs under qa/runs/* are not their own git repos - need --skip-git-repo-check
#   - Codex has no max-iterations flag; iteration cap is self-managed via goal.md instructions

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "usage: $0 <workspace-dir> <goal.md>" >&2
    exit 2
fi

WORKSPACE="$1"
GOAL_FILE="$2"

if ! command -v codex >/dev/null 2>&1; then
    echo "codex not found on PATH" >&2
    exit 2
fi

if ! codex mcp list 2>/dev/null | grep -q playwright; then
    echo "codex playwright MCP not configured - run:" >&2
    echo "  codex mcp add playwright -- npx -y @playwright/mcp@latest" >&2
    exit 2
fi

if [[ ! -f "$GOAL_FILE" ]]; then
    echo "goal file not found: $GOAL_FILE" >&2
    exit 2
fi

mkdir -p "$WORKSPACE/screenshots"

codex exec \
    --skip-git-repo-check \
    -C "$WORKSPACE" \
    < "$GOAL_FILE" \
    2>&1 | tee "$WORKSPACE/transcript.log"

if [[ ! -f "$WORKSPACE/findings.json" ]]; then
    echo "Codex completed but no findings.json produced; transcript at $WORKSPACE/transcript.log" >&2
    exit 1
fi
