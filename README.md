# coding-agent-skills

Sean Weldon's coding agent skill library for Claude Code, Codex, OpenCode, and any agent that reads `~/.agents/skills`.

This repository is the scrubbed pack from his private harness: the guardrail hooks, the six stack gotcha skills, review and QA skills, session handoff skills, reviewer prompts, and the OpenCode agents and commands that belong in that pack. It is not a copy of the whole private library.

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

It also symlinks each file under `opencode/agents/` and `opencode/commands/` into `~/.config/opencode/agents` and `~/.config/opencode/commands`.

It skips a destination that already exists and is not a symlink. It does not copy hooks or a settings file.

Hook wiring is in `hooks/README.md`. Point the hook commands at this repo, or copy the four scripts into `~/.claude/hooks/`. Do not copy a private settings file, and do not turn on a permissions bypass.

## What is inside

Counts are from this tree.

| Item | Count |
|---|---|
| Skills (directories with `SKILL.md`) | 17 |
| Lessons in the six stack gotcha skills | 163 |
| Hooks, excluding tests | 4 |
| Hook test cases | 35 (27 git-safety + 8 law-inject) |
| Commands | 8 (Claude 5, OpenCode 3) |
| Agent prompt files | 14 (Claude 9, OpenCode 5) |
| Rules files | 3 |
| Templates | 4 |
| Harnesses linked by `install.sh` | 4 |

Exact commands, run from the repo root:

```bash
find skills -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l
total=0
for f in skills/react-expo-gotchas/SKILL.md skills/supabase-gotchas/SKILL.md skills/python-backend-gotchas/SKILL.md skills/flutter-dart-gotchas/SKILL.md skills/typescript-gotchas/SKILL.md skills/ai-llm-gotchas/SKILL.md; do
  n=$(grep -c '^- ' "$f" || true)
  echo "  $n $f"
  total=$((total + n))
done
echo "  total $total"
find hooks -maxdepth 1 -type f ! -name README.md | wc -l
grep -c '^run ' hooks/tests/test-git-push-pipe-guard.sh hooks/tests/test-law-inject.sh
find commands -maxdepth 1 -name '*.md' | wc -l
find opencode/commands -maxdepth 1 -name '*.md' | wc -l
find commands opencode/commands -maxdepth 1 -name '*.md' | wc -l
find agents -name '*.md' ! -name README.md | wc -l
find opencode/agents -name '*.md' | wc -l
find agents opencode/agents -name '*.md' ! -name README.md | wc -l
find rules -maxdepth 1 -name '*.md' | wc -l
find . -path './.git' -prune -o -type f -path '*/templates/*' -print | wc -l
grep -oE '\.claude/skills|\.codex/skills|\.agents/skills|\.config/opencode' install.sh | sort -u | wc -l
```

Lesson bullets per gotcha skill: react-expo 38, supabase 42, python-backend 27, flutter-dart 13, typescript 13, ai-llm 30.

The four hooks are `pre-tool-git-safety.sh`, `pre-tool-law-inject.sh`, `pre-tool-workflow-budget.sh` (Python, despite the `.sh` name), and `stop-quality-gate.sh`. Laws 4, 7, and 8 are nudges. The law injector does not block on them. The live copies of these four scripts and the git-safety test were compared with this tree. The logic matches. The live files still name a machine path and a private checkout, so the scrubbed copies stay. The test lives in `hooks/tests/` and points at the hook beside that directory.

Claude commands, in `commands/`: `pickup`, `wrap`, `handover`, `retro`, and `recall`. OpenCode commands, in `opencode/commands/`: `pickup`, `wrap`, and `handover`. The blank handover body is `templates/HANDOVER.md`.

Claude agent files under `agents/` are prompt text with no agent frontmatter: `code-reviewer.md`, `security-reviewer.md`, `mobile-code-reviewer.md`, and the six files under `agents/reviewers/`. OpenCode agents under `opencode/agents/` are `planner.md`, `code-reviewer.md`, `security-reviewer.md`, `mobile-code-reviewer.md`, and `secondary-reviewer.md`.

## Left out of the OpenCode drop

These files were in the OpenCode directory on the machine and are not in this repo:

- `manager.md`: it loads herdr-graph and herdr-dispatch.
- `analyst.md`: its handoff is a graph node back to that manager.
- `builder-coder.md`: a build worker for the private monorepo, and it reports to that manager.
- `sync-project`, `start-build`, `prototype`: client tracking, the build scheduler, and the sales-prototype workflow.
- `qa-only`, `promote`, `recall`, `review`, `review-report`, `review-staged`, `review-today`, `watchdog-review`: each one only runs a skill that is not in this library (`qa`, `source-command-retro`, `recall-wiki`, or the review-report family).
- `ponytail-audit` and `ponytail-review`: five-line command prompts in the ponytail plugin's own tag format (`delete`, `stdlib`, `native`, `yagni`, `shrink`, and "Lean already. Ship."). They are not a Sean skill, and this repo does not vendor that plugin.
