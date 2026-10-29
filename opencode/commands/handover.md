---
description: Generate a structured session handover document.
---

# Handover

Review the conversation and write a handover from `templates/HANDOVER.md` in this library.

Save it to `.claude/sessions/YYYY-MM-DD-<worktree>-handover.md`, where `<worktree>` is `basename "$(git rev-parse --show-toplevel)"`. If that file already exists, append a `---` separator and a new timestamp.

The worktree segment is required. A bare `YYYY-MM-DD-handover.md` collides when two worktrees write on the same day.

Do not write the handover into a downstream repository. Write the note in your own checkout's `.claude/sessions/` directory, and put the downstream slug in the filename when the work was for another repo: `YYYY-MM-DD-<slug>-handover.md`.

Fill every section the template has. Omit a section that has nothing to report. Include the branch, the working directory, uncommitted changes (`git status --short` and `git diff --stat`), and what a fresh agent needs in order to resume.

Do not include secrets, credentials, pricing, or internal business data.

## Project state

If the working directory has a `PROJECT.md`, update its last-session block with today's date, what was done, what is next, and blockers (or "None"). Update a features table or a phase field only when this session changed them.

## Committing the note

Do not commit unless the operator asked. If they did:

- Never title a commit with the session narrative. Use `docs(<scope>): update project state` for a project-state file, and `chore: session notes` for the handover file. No date suffix, no topic, no parenthetical.
- No pricing or internal business data in the message.
- Stage an explicit pathspec. Do not `git add` the whole tree.
- If a hook refuses the commit, stop. Do not set an environment variable to bypass the hook.

## Landing the commit

Push only when the operator asked, and only to `origin`.

```bash
git fetch origin --quiet
git rev-list --count origin/master..HEAD
git rev-list --count HEAD..origin/master
```

If both counts are 0, `git push origin master` (or the checkout's default branch).

If either count is non-zero, do not push from a diverged checkout. Land from a separate worktree, rebase onto the fetched default branch, and push without force. If each touched file already matches the remote blob, do not push a duplicate.
