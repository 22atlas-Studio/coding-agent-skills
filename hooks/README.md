# Guardrail hooks

These are the Claude Code hooks from the harness that are safe to copy. They read a JSON tool payload on stdin.

| File | Event | Matcher | What it does |
|------|--------|---------|----------------|
| `pre-tool-git-safety.sh` | PreToolUse | `Bash` | Blocks dangerous git commands, a pipe after `git push`, and `git worktree prune` without `--dry-run`. Exit 2 blocks. |
| `pre-tool-law-inject.sh` | PreToolUse | `Bash` | Blocks `tail`/`cat`/`head` of a dotenv file (law 3). Nudges, and does not block, on `git push` to a remote other than `origin` (laws 4, 7 and 8). |
| `pre-tool-workflow-budget.sh` | PreToolUse | `Workflow` | Blocks an untiered agent fan-out. The file is Python. Run it with `python3`. |
| `stop-quality-gate.sh` | Stop | (none) | Runs lint, typecheck, and tests for a Python or Node project and blocks the stop when they fail. |

`pre-tool-workflow-budget.sh` keeps a `.sh` name because that is the name the harness invokes.

Example wiring. Do not copy a private settings file. Do not set a permissions bypass.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Workflow",
        "hooks": [{ "type": "command", "command": "python3 \"$HOME/.claude/hooks/pre-tool-workflow-budget.sh\"" }]
      },
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "bash \"$HOME/.claude/hooks/pre-tool-git-safety.sh\"" },
          { "type": "command", "command": "bash \"$HOME/.claude/hooks/pre-tool-law-inject.sh\"" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": "bash \"$HOME/.claude/hooks/stop-quality-gate.sh\"" }]
      }
    ]
  }
}
```

Copy the four scripts into `~/.claude/hooks/` (or point the commands at this repo). Then run:

```bash
bash hooks/tests/test-git-push-pipe-guard.sh
bash hooks/tests/test-law-inject.sh
```

The git-safety script's tests are the original 27 cases. The law-inject script's tests are the eight law cases from the phase-2 harness. The phase-2 harness itself is not shipped: it hardcoded a machine path and also drove hooks that are not in this pack.
