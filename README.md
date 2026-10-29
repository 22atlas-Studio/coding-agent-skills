# coding-agent-skills

**A scrubbed skill library that Claude Code, Codex, and OpenCode can share.**

This repository holds the skills, hooks, commands, and reviewer prompts Sean Weldon uses across those harnesses. It is in private review before an open-source release. The tree contains 17 skills, 163 lessons in six stack gotcha skills, 4 hooks, 8 commands, 14 agent prompt files, 3 rules files, and 4 templates.

## Status

Status for this repository is recorded in this section. There is no `PROJECT.md`.

| | |
|---|---|
| Lifecycle | Private review before open-source release |
| Current focus | Confirm the scrubbed pack, the installer, and the hook and skill tests before any public release. |

## What It Does

1. **Install one library into four harnesses** - `install.sh` symlinks every skill into Claude Code, Codex, and the shared skill directory, and symlinks the OpenCode agents and commands into the OpenCode config directory.
2. **Load the gotchas, reviews, and handoffs** - An agent can read 17 skills, including six stack gotcha skills with 163 lessons, plus the reviewer prompts and the pickup, wrap, and handover commands.
3. **Catch the git and stop mistakes** - Four hooks refuse dangerous git commands, a piped `git push`, printing a dotenv file, an untiered fan-out, and a stop while lint or tests are failing. Laws 4, 7, and 8 are reminders, not blocks.

## Quick Start

### Prerequisites

- bash
- git
- Python 3, for the fan-out hook and the pytest suites
- shellcheck, for the shell lint listed under Commands

No environment file is required.

### Install

From the repository root:

```bash
bash install.sh
```

The script skips a destination that already exists and is not a symlink. It does not copy hooks or a settings file.

### Run

There is no server to start. After install, Claude Code, Codex, and OpenCode read the linked skills and OpenCode files. To turn on the guards, point the harness at the scripts in `hooks/` using `hooks/README.md`. Do not copy a private settings file, and do not turn on a permissions bypass.

Confirm the git-safety hook with:

```bash
bash hooks/tests/test-git-push-pipe-guard.sh
```

## Commands

| Command | Purpose |
|---|---|
| `bash install.sh` | Link skills and OpenCode files into the four harness locations |
| `bash hooks/tests/test-git-push-pipe-guard.sh` | Run the 27 git-safety hook cases |
| `bash hooks/tests/test-law-inject.sh` | Run the 8 law-injector cases |
| `python3 -m pytest skills/security-scan/tests` | Run the security-scan tests |
| `(cd skills/qa-walk/helpers && python3 -m pytest tests)` | Run the qa-walk helper tests |
| `shellcheck -x install.sh hooks/pre-tool-git-safety.sh hooks/pre-tool-law-inject.sh hooks/stop-quality-gate.sh hooks/tests/test-git-push-pipe-guard.sh hooks/tests/test-law-inject.sh skills/qa-walk/runners/codex.sh` | Lint the bash scripts |

Run each command from the repository root. `pre-tool-workflow-budget.sh` is Python, so it is not in the shellcheck command. There is no typecheck gate, build, or release script in this repository.

## Architecture

```text
agents/        Claude reviewer prompts
commands/      Claude handoff commands
hooks/         Guardrail hooks and their tests
install.sh     Symlink installer
opencode/      OpenCode agents and commands
rules/         Standing laws and review rules
skills/        Skill directories, each with SKILL.md
templates/     Blank handover template
```

`install.sh` links each directory under `skills/` into `~/.claude/skills`, `~/.codex/skills`, and `~/.agents/skills`. It links each file under `opencode/agents` and `opencode/commands` into `~/.config/opencode/agents` and `~/.config/opencode/commands`. Those are the four harness locations. Hooks stay in this repository until a harness is pointed at them.

The six gotcha skills are react-expo (38 lessons), supabase (42), python-backend (27), flutter-dart (13), typescript (13), and ai-llm (30). Commands are 5 Claude files in `commands/` and 3 OpenCode files in `opencode/commands/`. Agent prompt files are 9 under `agents/` and 5 under `opencode/agents/`.

A few internal-only prompts were left out of this tree.

## Quality

Run each command in the Commands section separately and inspect its exit code. The hook tests and both pytest suites are the automated gates. shellcheck covers the bash scripts named above.

- Run each configured gate separately and inspect its exit code.
- Document manual, browser, device, or live-data checks that automation cannot prove.
- Do not call a change verified unless it was exercised against the required real system or data.

This repository has no web UI. A passing hook test does not prove a live agent session. The manual check is that `bash install.sh` creates the symlinks and that a harness can see the linked skills.

## Security

- Keep secrets out of skills, hooks, commands, and prompts. Nothing in this tree should contain a credential.
- The law injector blocks `tail`, `cat`, and `head` on a dotenv file. Do not weaken that check. Laws 4, 7, and 8 stay reminders.
- This library does not authenticate users or store customer data. Do not add tokens, account identifiers, or private paths.
- Report security concerns through a private GitHub security advisory on this repo.

## Deployment

There is no hosted deployment and no deploy command. Clone this repository onto the machine where the agents run, then run `bash install.sh` from the root.

## Repository Context

The template context files are not in this repository. The rules files that do ship are below.

| File | Purpose |
|---|---|
| `rules/ring0-laws.md` | Ten standing laws. Laws 4, 7, and 8 are nudges. |
| `rules/agents.md` | When to delegate work to a reviewer or subagent. |
| `rules/security.md` | Ownership checks and untrusted-input rules for review. |

## Contributing

Use a focused branch, preserve unrelated work, and run the commands in the Commands section. Record each exit code in the pull request. Do not describe a change as verified from a reading of the diff alone.
