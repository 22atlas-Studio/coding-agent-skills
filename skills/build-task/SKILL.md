---
name: build-task
description: Use when the user says "build the next slice", "build it", "execute", "go ahead and build", "implement slice 2". Builds exactly one slice from .build-loop/plan.md with tests written first, runs the full gates, proves the tests can fail, commits, and sets the slice to review.
---

# Build one slice

Load the `build-rules` skill first and follow it throughout.

Build only the slice the user named, or the first `pending` slice in `.build-loop/plan.md`. Never start a second slice in the same run.

## 1. Read before you touch

1. Read the slice in `.build-loop/plan.md` and the matching must-have in `.build-loop/brief.md`.
2. Read every file the slice lists, and the files next to them. Copy the project's patterns for naming, folders, error handling and data access.
3. Find the gate commands (test, typecheck, lint) in the plan's `## Gates` section or in the manifest.
4. Run the full test command once, bare, before changing anything. Write down the pass count. This is the baseline.
5. Run `git status --short --branch`. If the tree has changes you did not make, stop and ask whose they are.

Set the slice to `building`.

If the slice depends on an outside service that has not been proven, make a throwaway probe first. Capture one real response and build against that. Test data written from a guess about how the service answers only checks the guess.

## 2. Red: write the tests first

Write the tests for the slice's behaviour, one at a time, through the entry point a user or caller would use (a page, an endpoint, a command). Test what the feature does. Leave out tests that check how the code is arranged inside.

For each test:

```bash
<project test command> <path to the new test file>
echo "exit: $?"
```

The test must fail, and it must fail for the reason you expect (the feature is missing). Fix a wrong-reason failure, such as an import error or a typo, before going on. A test that passes the first time proves nothing: tighten it until it fails.

## 3. Green: build the smallest thing that passes

Write the code for one test, run it, see it pass, then move to the next test. Change only what the slice needs. Keep unrelated tidying out of the commit.

## 4. Run the full gates

Run each one bare, one at a time. Read the exit code, then read the output.

```bash
<test command>
echo "exit: $?"
<typecheck command>
echo "exit: $?"
<lint command>
echo "exit: $?"
```

- Compare the pass count with the baseline from step 1. It must be higher by the number of tests you added. A count that fell means a test file failed to load.
- No skipped tests in the files you touched.
- A gate with no command in this project is reported as "not covered". Never report it as passed.

## 5. Prove the tests can catch a break

Pick the main line of production code that makes the slice work. Break it on purpose (delete the line or invert the condition). Run the slice's tests bare, exactly as in the other steps, and read the exit code:

```bash
<project test command> <path to the slice's test file>
echo "exit: $?"
```

The exit code must be non-zero. Never judge this run through `| tail` or `| grep`: a pipe reports the exit code of the last command in it, so a hollow test can look red. If the tests stay green, they are hollow: strengthen them and repeat. Then restore the line, run the tests again (exit 0), and check the diff is exactly what you intended:

```bash
git diff --stat
```

## 6. Commit

```bash
git add path/one path/two          # explicit paths only
git diff --cached --stat           # must list exactly the intended files
git commit -m "feat(scope): short plain summary"
git status --short                 # must show nothing left for the files you changed
```

Read the message back right away:

```bash
git log -1 --format=%B
```

If it has a co-author attribution trailer (some AI tools add one by default), rewrite this commit's message
before doing anything else: `git commit --amend -m "<the same subject>"`, then read it back
again. A co-author who is not on the user's hosting team can block deploys (Vercel's Hobby
plan refuses them).

Use a conventional message (`feat`, `fix`, `test`, `chore`, `docs`). Keep it short and factual, with no story and no attribution lines. Never commit a secrets file. Fixes to this work found in review go in separate commits.

Set the slice to `review` in `.build-loop/plan.md` and commit that edit with the slice work or as its own `docs(plan)` commit.

## Report

Tell the user:
- what the slice does now, in one or two plain sentences,
- the commit sha and the files in it,
- the gate results with counts (baseline, now),
- the break test: which line you broke, and that the tests caught it,
- what is still unverified, such as the real flow, which `qa-walk` covers.

**Stop.** Do not push. The next steps are `precheck`, then `qa-walk`, then the user's push go.
