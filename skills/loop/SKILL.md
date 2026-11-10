---
name: loop
description: Use when the user wants to build or change software with the full build loop ("build this", "run the loop", "take this from idea to shipped", "keep going on the plan"). Runs plan, build, review, fix, walk and ship one slice at a time, and stops at each of the user's gates.
---

# The build loop

Load the `build-rules` skill first and follow it throughout.

This skill drives the others. It decides what stage the work is in, runs the skill for that
stage, and stops whenever the user's go is needed.

## 1. Find where the work stands

Read, in this order:

1. The newest handover for this project, written by `wrap` (run `pickup` to find and read it).
2. `.build-loop/brief.md` and `.build-loop/plan.md`.
3. `git status --short --branch` and `git log --oneline -10`.

Then pick the stage:

| What you find | Stage |
|---|---|
| No brief or plan | Plan: run `new-build` |
| A plan with no slice `building` or `review`, and no build go in the user's message | Plan the next `pending` slice |
| A `pending` slice, and the user's message asks to build it | Build: run `build-task` |
| A slice `building` | Build: run `build-task` |
| A slice `review` | Review: run `precheck`, then `qa-walk` |
| Every slice `done` | Tell the user, and suggest a `code-audit` |
| A bug report from the user | Run `triage` first |

If the state disagrees with itself (the plan says `done` but the walk file is missing, or the
branch is not the one the handover names), stop and say what disagrees.

## 2. Run one stage, then report

### Plan
Run `new-build` (new project) or write the next slice into `.build-loop/plan.md`. Show the user
the slice: what it does, the files it touches, how it will be checked. **Stop.** Wait for "build"
(or "execute", "go ahead and build").

A `pending` slice is always at the Plan stage, even when it is already written in the plan. The
build go is a message from the user that asks for building after you showed them the slice.
"Keep going", "continue", "next", "carry on" and "what's next" only ask you to move the loop
forward: for a `pending` slice, moving forward means showing it and stopping. Change no code and
make no commit until the build go arrives.

### Build
Run `build-task` on the slice. It writes the tests first, sees them fail, builds, and commits.
Set the slice to `review`. If the slice has a Figma frame, run `figma-parity` on it.

### Review and fix
Run `precheck`. For each finding: fix it with a test that fails first, commit, and run
`precheck` again on the fix commits only. Repeat until the review is clean. Each fix round is a
new change. Then run `qa-walk` on the slice's user flow. A failed walk sends the slice back to
Build.

When the walk passes, report:
- what the slice does now,
- the checks that ran, with their results,
- what was not checked and why.

**Stop.** Wait for "push" (or "go", "ship it").

### Ship
Run `ship`. It pushes, opens the pull request and merges only after its own checks, and merges
only when the user said merge. Set the slice to `done` once the merge landed and the walk
passed. Then go back to Plan for the next slice.

## 3. End of a session

Run `wrap` before stopping for the day or when the conversation gets long, so the next session
(in any tool) can run `pickup` and carry on.

## Stop conditions

Stop and ask the user when:
- a stage needs their go (plan, build, push, merge, deploy),
- the same check fails three times for the same reason,
- a step needs a credential, a payment or an outside account,
- the work would delete data or touch production.
