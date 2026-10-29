<div align="center">

# coding-agent-skills

**One skill library for Claude Code, Codex, and OpenCode.**

Skills, guardrail hooks, handoff commands, and reviewer prompts drawn from real client builds, scrubbed so any coding agent can load them.
Install once and every harness on the machine reads the same gotchas, review gates, and session handoffs.

![Claude Code](https://img.shields.io/badge/Claude_Code-skills_%2B_hooks-D97757?logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-skills-412991?logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-agents_%2B_commands-111111)
![Skills](https://img.shields.io/badge/skills-17-2EA44F)
![Lessons](https://img.shields.io/badge/gotcha_lessons-163-0969DA)
![Status](https://img.shields.io/badge/status-private_review-orange)

</div>

---

## Contents

- [What it does](#what-it-does)
- [Where it is today](#where-it-is-today)
- [How it fits together](#how-it-fits-together)
- [Skill catalog](#skill-catalog)
- [Guardrail hooks](#guardrail-hooks)
- [Quick start](#quick-start)
- [Commands](#commands)
- [Repository tour](#repository-tour)
- [Quality and testing](#quality-and-testing)
- [Security](#security)
- [Contributing](#contributing)

## What it does

1. **Install one library into four harness locations** - `install.sh` symlinks every skill into Claude Code, Codex, and the shared skill directory, and symlinks the OpenCode agents and commands into the OpenCode config directory.
2. **Load the gotchas before writing code** - six stack gotcha skills carry 163 lessons, each one a bug that already cost a real debugging cycle.
3. **Review before you ship** - precheck, code-review, security-scan, qa-walk, and route-walk turn "it looks done" into a gated verdict.
4. **Hand work between sessions and agents** - pickup, wrap, handover, recall, and retro keep project state durable across harnesses.
5. **Catch the expensive mistakes** - four hooks refuse dangerous git commands, a piped `git push`, printing a dotenv file, an untiered agent fan-out, and a stop while lint or tests are failing.

## Where it is today

*Status snapshot: October 29, 2026*

| Area | What it covers | Status |
|------|----------------|--------|
| Skills | 17 skill directories, each with a `SKILL.md` | ✅ Shipped in the tree |
| Gotcha lessons | 163 lessons across six stacks | ✅ Shipped in the tree |
| Hooks | 4 guardrail hooks with 35 test cases | ✅ Tests pass locally |
| Commands and prompts | 8 commands, 14 agent prompt files, 3 rules files, 4 templates | ✅ Shipped in the tree |
| Public release | Open-source publication | 🔨 In private review |

**Current focus**

- **Release review** - confirm the scrubbed pack, the installer, and the hook and skill tests before any public release.

## How it fits together

### Install topology

```mermaid
flowchart LR
    subgraph Repo["📦 coding-agent-skills"]
        SK["skills/"]
        OA["opencode/agents"]
        OC["opencode/commands"]
        HK["hooks/"]
    end

    INS{{"bash install.sh"}}

    subgraph Harness["🖥️ Harness locations"]
        CL["~/.claude/skills"]
        CX["~/.codex/skills"]
        AG["~/.agents/skills"]
        OP["~/.config/opencode/<br/>agents + commands"]
    end

    SK --> INS
    OA --> INS
    OC --> INS
    INS -- symlink --> CL
    INS -- symlink --> CX
    INS -- symlink --> AG
    INS -- symlink --> OP
    HK -. "wired by hand,<br/>see hooks/README.md" .-> CL
```

Everything is a symlink, so a `git pull` in this repository updates every harness at once. The installer skips any destination that already exists and is not a symlink, and it never copies hooks or a settings file.

### A session, start to finish

```mermaid
flowchart LR
    P["🔎 pickup<br/>rebuild current context"] --> I["🧭 investigate-first<br/>grounded report before code"]
    I --> B["🛠️ build<br/>load the stack gotchas"]
    B --> R["✅ precheck · code-review<br/>security-scan · qa-walk"]
    R --> W["📦 wrap · handover<br/>durable state"]
    W --> T["🧠 retro<br/>distill lessons"]
    T -. "next session" .-> P
    RC["🗂️ recall<br/>prior context"] -.-> I
```

## Skill catalog

| Group | Skill | When it loads |
|-------|-------|---------------|
| **Stack gotchas** | `react-expo-gotchas` | React, Expo, Expo Router, NativeWind, EAS, Next.js, Vercel |
| | `supabase-gotchas` | PostgREST, RLS, edge functions, GoTrue, storage |
| | `python-backend-gotchas` | uv, Pydantic v2, Typer, FastAPI, httpx, Stripe webhooks |
| | `ai-llm-gotchas` | Model selection, model ids, extraction limits, RAG trust boundaries |
| | `flutter-dart-gotchas` | google-services wiring, flavors, analyze scope, iOS white screens |
| | `typescript-gotchas` | tsc verification, Vitest, ESM imports, built-but-not-wired props |
| **Review and QA** | `precheck` | Before pushing: Codex review of staged, uncommitted, and recent commits |
| | `code-review` | Pre-ship audit before store submission or handoff |
| | `security-scan` | Whole-repo security gate against the app's own threat model |
| | `qa-walk` | Goal-driven end-to-end walk of every user workflow |
| | `route-walk` | Enumerates every distinct user path into a CSV route map |
| **Process** | `investigate-first` | Investigate and report before any code generation |
| **Continuity** | `pickup` | Resume a project from remote-current state |
| | `wrap` | Package a session into durable project state |
| | `handover` | Evidence-backed note for the next agent |
| | `recall` | Search prior context, handovers, and history |
| | `retro` | Distill lessons and reusable patterns from finished work |

### Gotcha lessons by stack

```mermaid
pie showData
    title 163 gotcha lessons
    "supabase" : 42
    "react-expo" : 38
    "ai-llm" : 30
    "python-backend" : 27
    "flutter-dart" : 13
    "typescript" : 13
```

## Guardrail hooks

```mermaid
flowchart LR
    TC["Agent tool call"] --> PRE["PreToolUse hooks<br/>git-safety · law-inject<br/>workflow-budget"]
    PRE -- "dangerous git, piped push,<br/>dotenv print, untiered fan-out" --> BLK["⛔ blocked, exit 2"]
    PRE -- "push to a<br/>non-origin remote" --> NUD["💬 reminder,<br/>call proceeds"]
    PRE -- "clean" --> OK["✅ call runs"]
    ST["Agent tries to stop"] --> QG["stop-quality-gate.sh"]
    QG -- "lint, typecheck,<br/>or tests fail" --> BACK["⛔ stop refused,<br/>keep working"]
    QG -- "green" --> DONE["✅ stop allowed"]
```

| Hook | Event | What it does |
|------|-------|--------------|
| `pre-tool-git-safety.sh` | PreToolUse `Bash` | Blocks dangerous git commands, a pipe after `git push`, and `git worktree prune` without `--dry-run` |
| `pre-tool-law-inject.sh` | PreToolUse `Bash` | Blocks `tail`, `cat`, and `head` of a dotenv file; nudges on a push to a remote other than `origin` |
| `pre-tool-workflow-budget.sh` | PreToolUse `Workflow` | Blocks an untiered agent fan-out (Python, run with `python3`) |
| `stop-quality-gate.sh` | Stop | Runs lint, typecheck, and tests for a Python or Node project and blocks the stop when they fail |

Wiring examples live in [`hooks/README.md`](hooks/README.md). The ten standing laws the hooks enforce are in [`rules/ring0-laws.md`](rules/ring0-laws.md); laws 4, 7, and 8 are reminders, not blocks.

## Quick start

### Prerequisites

- bash and git
- Python 3, for the fan-out hook and the security-scan tests
- [uv](https://docs.astral.sh/uv/), for the qa-walk helper tests
- shellcheck, for the shell lint

No environment file is required.

### Install

```bash
git clone git@github.com:22atlas-Studio/coding-agent-skills.git
cd coding-agent-skills
bash install.sh
```

### Run

There is no server to start. After install, Claude Code, Codex, and OpenCode read the linked skills and OpenCode files. To turn on the guards, point the harness at the scripts in `hooks/` using [`hooks/README.md`](hooks/README.md). Do not copy a private settings file, and do not turn on a permissions bypass.

Confirm the git-safety hook with:

```bash
bash hooks/tests/test-git-push-pipe-guard.sh
```

## Commands

Run each command from the repository root and inspect its exit code.

| Command | Purpose |
|---|---|
| `bash install.sh` | Link skills and OpenCode files into the four harness locations |
| `bash hooks/tests/test-git-push-pipe-guard.sh` | Run the 27 git-safety hook cases |
| `bash hooks/tests/test-law-inject.sh` | Run the 8 law-injector cases |
| `python3 -m pytest skills/security-scan/tests` | Run the 20 security-scan tests |
| `(cd skills/qa-walk/helpers && uv run pytest tests)` | Run the 28 qa-walk helper tests (uv installs the helper dependencies) |

<details>
<summary><b>Shell lint</b></summary>

```bash
shellcheck -x install.sh hooks/pre-tool-git-safety.sh hooks/pre-tool-law-inject.sh \
  hooks/stop-quality-gate.sh hooks/tests/test-git-push-pipe-guard.sh \
  hooks/tests/test-law-inject.sh skills/qa-walk/runners/codex.sh
```

`pre-tool-workflow-budget.sh` is Python, so it is not in the shellcheck command. There is no typecheck gate, build, or release script in this repository.

</details>

## Repository tour

| Path | What it is |
|------|------------|
| `skills/` | 17 skill directories, each with a `SKILL.md` |
| `agents/` | 9 Claude reviewer prompt files, loaded by path ([why no frontmatter](agents/README.md)) |
| `commands/` | 5 Claude handoff commands: pickup, wrap, handover, recall, retro |
| `opencode/` | 5 OpenCode agents and 3 OpenCode commands |
| `hooks/` | 4 guardrail hooks and their tests |
| `rules/` | Standing laws, delegation rules, and review security rules |
| `templates/` | Blank handover template |
| `install.sh` | Symlink installer |

| Rules file | Purpose |
|---|---|
| [`rules/ring0-laws.md`](rules/ring0-laws.md) | Ten standing laws. Laws 4, 7, and 8 are nudges. |
| [`rules/agents.md`](rules/agents.md) | When to delegate work to a reviewer or subagent. |
| [`rules/security.md`](rules/security.md) | Ownership checks and untrusted-input rules for review. |

A few internal-only prompts were left out of this tree.

## Quality and testing

- **83 automated tests** across the hooks (27 + 8) and two skill helper suites (20 + 28).
- **Every gate runs on its own** so each exit code is visible; a piped command hides the code that matters.
- **Verified means exercised** against the real system or data, never inferred from a reading of the diff.

This repository has no web UI. A passing hook test does not prove a live agent session. The manual check is that `bash install.sh` creates the symlinks and that a harness can see the linked skills.

## Security

- **No secrets in the tree** - nothing in skills, hooks, commands, or prompts should contain a credential.
- **Dotenv files stay unprinted** - the law injector blocks `tail`, `cat`, and `head` on a dotenv file. Do not weaken that check.
- **No user data** - this library does not authenticate users or store customer data. Do not add tokens, account identifiers, or private paths.
- **Reporting** - raise security concerns through a private GitHub security advisory on this repository.

## Contributing

Use a focused branch, preserve unrelated work, and run the commands in the [Commands](#commands) section. Record each exit code in the pull request. Do not describe a change as verified from a reading of the diff alone.

---

<div align="center">

Built by **Sean Weldon** at **22atlas**

</div>
