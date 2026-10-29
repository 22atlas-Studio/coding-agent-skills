# coding-agent-skills

Sean Weldon's coding agent skill library for Claude Code, Codex, and any agent that reads `~/.agents/skills`.

This repository is the scrubbed pack from his private harness: the guardrail hooks, stack gotcha skills, review and QA skills, session handoff skills, and cross-harness setup that were in the source export. It is not a copy of the whole private library.

No license file was in the export for this pack.

## Install

From a clone of this repo:

```bash
bash install.sh
```

The script symlinks each directory under `skills/` into:

- `~/.claude/skills` (Claude Code)
- `~/.codex/skills` (Codex)
- `~/.agents/skills` (shared skill directory)

It skips a destination that already exists and is not a symlink. It does not copy hooks, commands, or a settings file.

Hook wiring is in `hooks/README.md`. Point the hook commands at this repo, or copy the four scripts into `~/.claude/hooks/`. Do not copy a private settings file, and do not turn on a permissions bypass.

OpenCode can read skills from `~/.agents/skills` after install. This export does not contain OpenCode's agent files or command files, so those are not installed.

## What is inside

Counts are from this tree.

| Item | Count |
|---|---|
| Skills (directories with `SKILL.md`) | 15 |
| Lessons in the stack gotcha skills | 120 |
| Hooks, excluding tests | 4 |
| Hook test cases | 35 (27 git-safety + 8 law-inject) |
| Commands | 5 |
| Agent prompt files | 9 |
| Rules files | 3 |
| Templates | 4 |
| Harnesses linked by `install.sh` | 3 |

Exact commands, run from the repo root:

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l
total=0
for f in skills/react-expo-gotchas/SKILL.md skills/supabase-gotchas/SKILL.md skills/python-backend-gotchas/SKILL.md skills/flutter-dart-gotchas/SKILL.md; do
  n=$(grep -c '^- ' "$f" || true)
  echo "  $n $f"
  total=$((total + n))
done
echo "  total $total"
find hooks -maxdepth 1 -type f ! -name README.md | wc -l
grep -c '^run ' hooks/tests/test-git-push-pipe-guard.sh hooks/tests/test-law-inject.sh
find commands -maxdepth 1 -name '*.md' | wc -l
find agents -name '*.md' ! -name README.md | wc -l
find rules -maxdepth 1 -name '*.md' | wc -l
find . -path './.git' -prune -o -type f -path '*/templates/*' -print | wc -l
grep -oE '\.claude/skills|\.codex/skills|\.agents/skills' install.sh | sort -u | wc -l
```

Lesson bullets per gotcha skill: react-expo 38, supabase 42, python-backend 27, flutter-dart 13.

The four hooks are `pre-tool-git-safety.sh`, `pre-tool-law-inject.sh`, `pre-tool-workflow-budget.sh` (Python, despite the `.sh` name), and `stop-quality-gate.sh`. Laws 4, 7, and 8 are nudges. The law injector does not block on them.

The commands are `pickup`, `wrap`, `handover`, `retro`, and `recall`. The blank handover body is `templates/HANDOVER.md`.

The agent files are prompt text with no agent frontmatter: `code-reviewer.md`, `security-reviewer.md`, `mobile-code-reviewer.md`, and the six files under `agents/reviewers/`.

## Not in this export

These were in the proposed pack and are not in the source this repo was built from. They are not recreated here:

- TypeScript gotcha skill
- AI pipelines gotcha skill
- MCP overwrite guard
- parity check script
- `ponytail-audit` and `ponytail-review` commands
- the OpenCode agents (8) and OpenCode commands (16)

A private reviewer plugin, and the four registered reviewer subagents that lived in it, were also absent. The fan-out prompts under `agents/reviewers/` are the read-only reviewers that were in the export.
