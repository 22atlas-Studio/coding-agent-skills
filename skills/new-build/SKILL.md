---
name: new-build
description: Use when the user says "I want to build...", "start a new project", "here is my idea", "turn this spec into a plan", "set up a new app". Turns an idea or rough spec into a short brief, a slice-by-slice plan, and (for a new project) a repo with working test, typecheck and lint gates. Stops after the plan.
---

# Start a new build

Load the `build-rules` skill first and follow it throughout.

This skill ends with a brief, a plan and a repo whose checks can fail. It writes no product code.

## 1. Look before you write

Run these and read the output:

```bash
git rev-parse --show-toplevel   # is there already a repo?
git status --short --branch
ls
```

- Existing project: read the README, the manifest (`package.json`, `pyproject.toml`, `Gemfile`, `go.mod`) and any `.build-loop/` folder. Do not scaffold over what is there.
- Empty folder: this is a new project. Step 5 sets up the repo.
- If `.build-loop/brief.md` already exists, show it and ask whether to extend it. Never overwrite a file the user may have edited.

## 2. Interview for the missing must-haves

Read what the user gave you first (idea, notes, pasted spec). Ask only for what is missing, in one short message with at most five questions:

1. Who is it for, and what is the one job they hire it to do?
2. What must work on day one? (the must-haves)
3. What is out of scope for now?
4. Does it need sign-in, payments, email or another outside service? Which one?
5. Is there a stack the user already uses or must use?

If the user says "you decide" on the stack, pick the simplest common stack for the job and give the reason in one line. Anything still unknown goes into the brief as an open question. Do not invent an answer.

## 3. Write `.build-loop/brief.md`

```markdown
# <Product name>
## Who it is for
## The problem
## Must-haves
## Out of scope
## Outside services and keys needed
## Open questions
```

Keep it to one page. Each must-have is one plain sentence a user could check by using the product.

## 4. Write `.build-loop/plan.md`

Cut the must-haves into thin vertical slices. A slice is a small piece that works from the screen (or command) down to the data and back. The first slice is the thinnest path that proves the riskiest unknown, such as an outside service or the data shape. If something is unproven (a new library, a vendor API), make a throwaway probe the first slice.

```markdown
## Slice 1: <short name>
Status: pending
What the user can do afterwards: <one sentence>
Files: <paths it will touch or create>
Checked by: <the tests, and the real flow to walk>
```

Every slice starts `pending`. Never write a slice as `done` ahead of the work.

Put the user's gates at the top of `.build-loop/plan.md`, so any AI tool that reads the plan sees
them, even one that never loads these skills:

```markdown
> Rules for AI tools: build a slice only after the user says "build" for it. Keep going,
> continue and next only mean show the next slice and stop. Push, merge and deploy each need
> their own go. Use the build-loop skills (`loop`, `build-task`, `ship`) when you have them.
```

Then add the same lines to the project's `AGENTS.md` (read by Codex and others) and `CLAUDE.md`
(read by Claude Code), creating them if they do not exist and adding to the end if they do.
Keep anything already in those files.

## 5. New project only: wire the gates (slice 0, after the build go)

For a new project, put this setup in the plan as `Slice 0: project setup`, status `pending`. It creates files and makes the first commit, so it runs only after the user says build. Then `build-task` (or you, inside the `loop`) does these steps:

1. Run `git init` if needed. Create the project in the chosen stack, using the stack's own installer where one exists.
2. Find or add three commands: test, typecheck, lint. Look in the `package.json` scripts, `pyproject.toml`, the `Makefile` or the README. If the stack has no typechecker, write "no typecheck" in `plan.md` and tell the user.
3. Add one placeholder test that asserts something false. Run the test command bare and confirm it fails with a non-zero exit code. Then fix the assertion, run again, and confirm it passes. Remove the placeholder once the first real test exists.
4. Prove the lint and typecheck commands can fail: add a known-bad line, run each, see it fail, then remove the line.
5. Write `.gitignore` with at least the `qa-walk` run artifacts it does not commit (screenshots, transcripts, per-workflow state and network logs under `qa/runs/`), the secrets file for the stack (the dotenv file and its variants, keeping the example file tracked) and the stack's dependency folder.
6. Record the three commands at the top of `.build-loop/plan.md` under `## Gates`, with the exit codes you saw.
7. Make the first commit: `chore: scaffold project with test, typecheck and lint gates`. Use `git add` with explicit paths, then `git status --short` to confirm nothing was left out.

Never print or open a secrets file. If a key is needed, name it in the brief and leave the value to the user.

## Stop

Report to the user:
- the brief in five lines or fewer,
- the slice list with one line each,
- the three gate commands and what you saw them do,
- the open questions.

**Stop at the Plan gate.** Do not start slice 1 until the user says "build".
