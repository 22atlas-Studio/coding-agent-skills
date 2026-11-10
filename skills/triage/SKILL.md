---
name: triage
description: Use when the user says "this is broken", "I found a bug", "it shows an error", "why does it do that", "fix this issue". Takes a bug report to a root cause and a failing test, fixes it, searches for the same bug elsewhere, and reports.
---

# Triage a bug

Load the `build-rules` skill first and follow it throughout.

The goal is a proven root cause, a test that failed before the fix, and a fix that makes it pass. Do not guess a fix before you can reproduce the bug.

## 1. Get the user's evidence first

Before you read any code, ask for what the user saw, unless they already gave it:

- a screenshot or the exact error text,
- the steps they took, and the page, command or account they used,
- what they expected to happen.

If the report has several symptoms, list them. Several symptoms often share one cause, so look for it before you plan several fixes. If the user cannot give evidence, find it yourself in the logs, the browser console or the failing request. Say which.

## 2. Reproduce it

1. `git status --short --branch` and `git log --oneline -10` so you know what code you are looking at.
2. Make the bug happen yourself, the way the user did. Use the project's run command, a test, or a direct request to the endpoint. Capture the actual error and, for a web call, the real status code.
3. If you cannot reproduce it, say so plainly and name what differs (data, account, version). Do not ship a fix for a bug you have not seen.

A generic message such as "Something went wrong" can hide any failed load. Capture the real status and body before you form a theory.

## 3. Find the root cause

- Trace from the symptom to the first place the data or state goes wrong. Read the code on that path.
- Check the one thing that changed lately: `git log -p` on the files involved.
- When a fix idea disagrees with your own evidence, stop. The cause is somewhere else.
- State the cause in one plain sentence and show the evidence: the line, the value, the log.

**Stop here unless the user already asked you to fix it.** A report of a bug or a question
("why does it do that?") asks for the cause. Tell the user the cause, the evidence and the
fix you propose, and wait for "fix it" or "build". Sections 4 to 7 change code and commit, so
they run only after that go.

## 4. Failing test first

Write a test that reproduces the bug through the same entry point the user used. Run it bare:

```bash
<project test command> <path to the new test file>
echo "exit: $?"
```

It must fail, with the same wrong behaviour you saw. If it passes, it does not capture the bug: fix the test before touching the code.

## 5. Fix and prove

1. Make the smallest change that fixes the cause.
2. Run the new test and see it pass.
3. Run the full gates (test, typecheck, lint), each bare, and compare the test count with the run before. It must have gone up by the tests you added.
4. Break the fix on purpose and confirm the new test goes red. Restore it.
5. Commit with explicit paths and a conventional message such as `fix(scope): short plain summary`. Use `git add <paths>`, then `git diff --cached --stat`, then commit.

## 6. Search for the same bug

A fixed spot is one instance. Search the whole project for the same pattern:

```bash
grep -rn "the-broken-pattern" --include="*.<ext>" .
```

Check every caller of any function or rule you changed. Fix the other spots in the same way, each with a test, or list them for the user if they need a decision.

## 7. Walk the real flow

Repeat the user's steps in the running app and confirm the symptom is gone. A green test run on its own does not show this. If you cannot run the app, say so and hand the user the exact steps to repeat.

## Report

Tell the user:
- the cause, in one or two plain sentences,
- the evidence that shows it,
- the fix and its commit sha,
- the other places with the same pattern, and what you did about each,
- what you checked and what you could not check.

**Stop.** Do not push. Pushing waits for the user's go (see `ship`).
