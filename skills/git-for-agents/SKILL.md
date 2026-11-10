---
name: git-for-agents
description: Use when an autonomous agent (a Claude Code or Codex subagent, a worker in a parallel dispatcher, a self-hosted agent runtime) needs to make git changes. Guides worktree isolation, atomic commits, push safety, and the agent/human pull request boundary. Use before writing any agent that runs `git` commands, when designing parallel agent dispatch, or when an agent's git workflow is producing merge conflicts, accidental adds, or broken branches.
---

# Git for Autonomous Agents

Practical patterns for making git safe and efficient when an LLM agent is the operator. Distilled from running parallel subagents and worker dispatchers against shared repositories.

## Core Principle

**Agents write; humans (or reviewer agents) merge.** The agent's contract ends at `git push origin <branch>`. Anything beyond that (auto-merge, force push, history rewrite) multiplies blast radius and removes the review checkpoint.

## When to Use

- Designing a new agent that touches git (a worker, a dispatcher, a custom subagent)
- Dispatching 2+ parallel agents that may touch overlapping files
- Diagnosing why an agent's pushes keep getting rejected, hooks keep failing, or branches keep breaking
- Setting up safe pushes from a repository an agent did not create
- Any time you're about to give an agent `Bash` access with git commands in scope

## When NOT to Use

- Single-shot human-driven commits (use the user's normal git workflow)
- Pure read-only agents (`git log`, `git blame`): they don't need this
- Repository administration (rebases, history surgery, repo init): keep humans in the loop

## The Minimum Viable Agent Contract

```
1. Create a fresh worktree on a fresh branch
2. Make all changes inside that worktree only
3. git add <explicit paths>      # never -A or .
4. git commit -m "<scoped msg>"  # type(scope): description, from the index
5. git push origin <branch>      # no force, no --no-verify
6. Open a pull request; STOP.
7. On any failure: capture diff + log to an artifacts dir, abandon the worktree, exit non-zero.
```

Every pattern below justifies why one of these steps is non-negotiable.

## Patterns

### 1. One worktree per agent

Worktrees are the highest-leverage primitive. Each agent gets its own checkout sharing one `.git/`:

```bash
git worktree add .agents/worktrees/<agent-id> -b feat/<task-id>-<slug>
# ... agent works inside the worktree ...
git worktree remove .agents/worktrees/<agent-id>
```

- No file collisions between parallel agents
- Cheap (shares objects with the main checkout)
- A dispatcher can run several concurrent agents this way
- Cleanup is one command, with no orphaned `.git` lockfiles

### 2. One branch per task

The agent is short-lived and the task is durable. Name branches `feat/<ticket-id>-<slug>` so reviews, telemetry, and memory can correlate to the work item. If the same task is retried by a new agent instance, it should reuse the same branch (or add a `-retry-2` suffix) instead of inventing a new one keyed off a PID.

### 3. Atomic commits with explicit paths

**Never** `git add .` or `git add -A` in agent code. They hoover up unrelated work, secrets in dotenv files, build artifacts, and other agents' files:

```bash
git add path/one path/two path/new-file
git diff --cached --name-only        # must list exactly the intended paths
git commit -m "feat(scope): msg"     # commit from the index
git status --short                   # the intended paths must now be clean
```

Avoid `git commit -m msg -- <paths>`. It commits from the working tree, bypasses what you staged, and silently skips paths git does not track yet, so a new file can be left out while the commit still succeeds. Stage first, check the staged list, then commit.

### 4. Conflict avoidance for parallel work

Order patterns by coupling, prefer the simplest:

| Pattern | When |
|---|---|
| **Independent parallel** (default) | Partition by directory or file glob *before* dispatch: agent A owns `src/api/`, agent B owns `src/ui/`. No shared writes. |
| **Pipeline / handoff** | Agent A's branch is merged or rebased into agent B's base before B starts. Sequential, no live coordination. |
| **Shared mutable state** | Use only when partition fails. Pick a coordinator (for example a TASKS.md blackboard) and serialize writes. |

Skip "full peer-to-peer" entirely. Agents negotiating live is a debugging nightmare.

### 5. Commit message discipline

Deterministic and greppable beats clever:

- Format: `type(scope): description` (Conventional Commits)
- Reference the ticket or job ID so memory and telemetry can correlate: `feat(worker): wire job memory writer [JOB-1234]`
- One logical change per commit: squashing breaks `git bisect` and blame
- No co-author attribution trailers from agents (some hosting plans refuse deploys from commits with unknown co-authors, and it pollutes attribution)

### 6. Push safety

The default agent `git push` should be `git push origin <branch>` and **stop**. Specifically:

| Flag | Default | When override is OK |
|---|---|---|
| `--force` / `--force-with-lease` | **Never** | Only on the agent's own short-lived branch, never on `main` or a protected branch |
| `--no-verify` | **Never** | Only when a human explicitly requested it for a known-safe situation |
| `--no-gpg-sign` | **Never** | Don't bypass signing |

If a hook fails, the agent should **capture the failure to its artifacts dir and exit non-zero**. It must never retry with `--no-verify`. Never pipe `git push` through `grep` or `head`: the pipe hides push's exit code.

### 7. The pull request as the agent/human boundary

Agents open pull requests; humans (or a reviewer agent) merge. This:

- Keeps blast radius small (worst case: one bad pull request, easy revert)
- Gives review-time visibility before code reaches `main`
- Lets CI catch what the agent didn't
- Creates a structured artifact (description, diff, comments) that downstream telemetry can reason about

`gh pr create --title ... --body ...` and stop.

### 8. Start clean and capture state on failure

Agents shouldn't try to recover from messy git state. They should start from a clean state:

```bash
# Before any work: a fresh worktree on a fresh branch from the remote default branch
git fetch origin
git worktree add .agents/worktrees/<id> -b feat/<task-id> origin/main
```

Never `git stash` inside a worktree. The stash stack is shared by every worktree of the repository, so one agent can pop another agent's work. If there is work in progress to keep, commit it on a branch (`wip: ...`).

On failure:
- Dump `git status`, `git diff`, and the agent's stdout/stderr to an artifacts dir
- Abandon the worktree (`git worktree remove --force`)
- Exit non-zero

Don't let the agent try to "fix" a bad state. Cleanup is cheap; a half-fixed branch pushed to origin is expensive.

### 9. Repository boundaries

Before pushing, the agent resolves and verifies the repository's own remote (`git remote -v`) and confirms the branch descends from that remote's history. A directory name says nothing reliable about which repository it holds. Divergence, force-pushes, and history rewrites remain human-confirmed operations.

### 10. Read git as memory

`git log`, `git blame`, `git diff` are the cheapest, never-stale memory of what changed and why. Before an agent searches notes or external memory for "what did we do last week", it should run:

```bash
git log --since="2 weeks ago" --oneline -- <relevant-path>
git blame <file>
```

Free, instant, authoritative. Saves a context-window-eating memory roundtrip for facts that already live in commits.

## Quick Reference

| Task | Command |
|---|---|
| Spawn agent worktree | `git worktree add .agents/worktrees/<id> -b feat/<task> origin/main` |
| Clean up agent worktree | `git worktree remove --force <path>` |
| Stage and check | `git add path1 path2 && git diff --cached --name-only` |
| Commit from the index | `git commit -m "type(scope): msg"` |
| Push agent branch | `git push origin feat/<task>` |
| Open pull request and stop | `gh pr create --title ... --body ...` |
| Capture state on failure | `git status > artifacts/status.txt; git diff > artifacts/diff.patch` |

## Common Mistakes

| Mistake | Fix |
|---|---|
| `git add .` / `git add -A` in agent code | List paths explicitly. Always. |
| `git commit -- <paths>` with a new file | Stage with `git add`, check `git diff --cached --name-only`, commit from the index. |
| `git stash` in a worktree | Commit work in progress on a branch, or start a fresh worktree. |
| Auto-merging the agent's own pull request | Stop at pull request creation. A human or reviewer agent merges. |
| `--no-verify` on hook failure | Capture the failure, exit non-zero. Hooks exist for a reason. |
| Force-pushing to `main` | Never. Force-push is only for the agent's own feature branch, before review. |
| Reusing one worktree across parallel agents | One worktree per agent. They are cheap. |
| Branch named after the agent's PID or timestamp | Name the branch after the **task**. |
| Letting the agent "fix" a messy git state | Abandon the worktree. Restart cleanly. |

## Red Flags

If you catch the agent reasoning toward any of these, **stop and reset:**

- "I'll just `git add .` since the worktree is clean": the worktree can change before the commit
- "The hook is wrong, I'll bypass with `--no-verify`": diagnose the hook failure
- "I'll force-push to fix the bad commit": only on the agent's own branch, never on a shared one
- "I'll merge my own pull request since the diff looks clean": that defeats the boundary
- "I'll keep trying until git stops complaining": exit non-zero, dump state, let a human or reviewer see the failure

## Related in this library

- `hooks/pre-tool-git-safety.sh` blocks the dangerous git commands this skill warns about.
- `rules/agents.md` carries the atomic-commit rule for every agent session.
- `ship` applies patterns 6 and 7 to a real push and merge.
