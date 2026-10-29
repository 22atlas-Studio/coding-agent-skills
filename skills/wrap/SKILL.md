---
name: wrap
description: Package a session into durable, harness-neutral project state and handovers. Use when the user says wrap, end session, package the work, prepare continuity, or update session state for another agent.
---

# Wrap

Package the session so any later harness can resume it.

## 1. Establish Evidence

- Resolve every project touched from the conversation, current directory, and project-scoped git changes.
- Inspect the branch, `git status --short --branch`, diff summary, staged diff summary, and relevant recent commits.
- Record test, build, review, deploy, and runtime probes actually run this session, including failures and untested surfaces. Do not rerun broad gates merely to make the handover look complete.
- Treat earlier agent completion claims as unverified until the artifact or command output confirms them.

## 2. Persist Durable Learning

Invoke the `diary` skill when available so the live session narrative is retained before distillation. A missing diary skill is best effort and must not block the portable handover.

Invoke the `retro` skill when available. Store only lessons that generalize or prevent a repeated failure. Project-specific decisions belong in the project's existing guidance or `memory/decisions.md`, not a harness-specific memory file. If no retro skill is available, record the omission in the final summary and continue.

## 3. Update All Context Files

Every wrap brings every context file of every touched project up to date. A file that now states something false (stale remote, branch, phase, version, command, rule, next action) is a wrap defect, not a later chore.

For each touched project, enumerate and check each of these that exists:

- `PROJECT.md`: last-session, phase, feature, next-action, and blocker fields.
- `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md`: remote, default branch, quality profile, required runtime versions, commands, and any rule or hazard learned this session that the next agent needs.
- `README.md` and other repo docs that describe behaviour the session changed.
- The project's decision or memory docs (`memory/decisions.md`, `decisions/`), the harness project memory (`~/.claude/projects/<slug>/memory/` plus its `MEMORY.md` index), and any portfolio or registry file the project already keeps.

Rules:

- Change only lines the session's verified evidence contradicts or newly supports. Never prefill completion, and update task status only when current evidence supports it.
- Preserve existing structure and unrelated content. Cross-check sibling files against each other: two files disagreeing on one fact means one is stale, so resolve it from the source of truth (code, remote, registry) rather than picking one.
- Before editing, decide per repository whether the wrap may commit. It may only when the index is empty (`git diff --cached --quiet` exits 0) and every context file it will touch, plus the repository session-copy path step 4 will write, is clean or absent in `git status --porcelain`. Otherwise someone else's work is in play: do not touch a context file that was already dirty (report the stale line and the edit it needs instead), and do not commit in that repository; report the exact commands instead.
- When the wrap may commit, at least one repository file will actually change, and the checkout sits on the default branch, create and switch to the docs branch now, before any handover is written, so every handover records the final branch.
- A checkout the repository reserves for syncing only (the integration clone) is never branched, edited or committed in place: make the context edits, the session copy and the commit in a linked worktree created from the fetched default branch, following the repository's worktree convention.
- Do not commit yet: the single context commit happens at the end of step 4, so it also carries the repository session copy.
- Record the files checked and the files changed for the step 8 report.

## 4. Write The Handover

Write one concise handover per touched project to the harness-neutral canonical store:

`~/.local/share/agent-handovers/<project>/YYYY-MM-DD-HHMMSS-<session>-handover.md`

Use a filesystem-safe project slug and session label. Create the directory when needed. Never overwrite another session's file.

Also write or append the repository's conventional session copy when safe:

- the repository or worktree: `.claude/sessions/YYYY-MM-DD-<project>-<worktree>-handover.md`, where `<worktree>` is the basename of `git rev-parse --show-toplevel`.
- A repo that already standardizes on `.codex/sessions/`: follow that convention.
- Standalone client-owned repos: do not add internal handovers to the client tree. The canonical store is sufficient.

Include:

```markdown
# Session Handover - Topic
**Date**: YYYY-MM-DD HH:MM
**Project**: slug
**Branch**: branch
**Working Directory**: absolute path

## Goal
## Decisions
## Completed
## In Progress
## Evidence
## Current State
## Risks And Blockers
## Next Action
## Key Files
## Context For Resumption
```

Omit empty sections. Include exact uncommitted paths or a concise grouped summary. The next action must be singular and executable. Exclude secrets, credentials, private client data, pricing, and unsupported verification claims.

Read the canonical file back after writing it and confirm its project, timestamp, working directory, and next action are present.

Then, in each repository step 3 cleared for committing, make one scoped docs commit of the step 3 context-file edits plus the repository session copy written above, on the branch step 3 selected. Stage explicit paths only, and before committing assert `git diff --cached --name-only` equals the intended list exactly. Do not push without the push word. Files outside any repository (harness memory, the handover store) need no commit. Skip the commit when the intended list is empty. After committing, rewrite the canonical handover's Current State and uncommitted-path lines to the post-commit state, add the commit sha, and read it back.

## 5. Sync Recall Surfaces

- For a client project, invoke `sync-project <slug>` when available. Re-read the canonical Obsidian note or returned tracking state to confirm the update landed. Stop and report if a required client state sync fails.
- For non-client or mixed work, append from the handover to the appropriate Obsidian project note or daily note when available. This branch is best effort.
- If the checkout has a memory ingest script, you may run it with `--apply`. Skip it when the script is absent. Direct file pickup remains authoritative.

Never replace a multi-entry Obsidian note with a summary.

## 6. Check Delivery Drift

These checks are read-only and best effort:

- Run `stranded-branches` in the current repository when available. Surface `STRANDED` work, but never merge or delete a branch during wrap.

## 7. Do not prune worktrees here

List linked worktrees if that helps the report. Do not bulk-remove them during wrap, and do not call a worktree-manager prune. Removal is a separate operator decision.

## 8. Report And Stop

Output one compact line per project:

`wrap complete: project=SLUG handover=PATH repo-copy=PATH_OR_SKIPPED context=CHANGED_FILES_OR_UNCHANGED obsidian=PATH_OR_SKIPPED recall=UPDATED_OR_SKIPPED delivery=SUMMARY worktrees=NOT_PRUNED tests=SUMMARY risks=SUMMARY`

Then report uncommitted changes and suggest exact scoped commit commands if useful. Apart from the context commit at the end of step 4, never auto-commit; never push, send Slack or email, transition tickets speculatively, or include secrets. A handover write or readback failure fails the wrap; optional recall services do not.
