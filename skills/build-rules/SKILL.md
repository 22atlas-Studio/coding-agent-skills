---
name: build-rules
description: The quality rules every build-loop skill follows (loop, new-build, build-task, code-audit, precheck, security-scan, figma-parity, qa-walk, triage, ship, wrap, pickup). Load it before any of those skills, or when the user asks how the build loop keeps AI-written code honest.
---

# Build rules

These rules came from real failures. Each one stops a mistake that looked like success at the
time. Every build-loop skill follows all of them. When a rule and a shortcut disagree, the rule
wins, and you say what it cost.

## 1. Words mean what they say

- **Done** means the change works when you use it as a real user would, on a fresh account or a
  clean state. Compiling, booting, a green test run and "it looks right" are steps toward done.
  Say which steps you ran.
- **Verified** means you exercised the real thing. A test against data you invented about an
  outside service only checks your own guess about it. Capture a real response or read the
  vendor's docs first.
- **Shipped** means the commit is on the remote branch. Check with
  `git merge-base --is-ancestor <sha> origin/<branch>` before you say it.
- Report what failed as plainly as what passed. A skipped step is named as skipped.

## 2. Tests must be able to fail

- Write the test, run it, and watch it fail for the reason you expect. Then write the fix.
- A test that passes the first time it runs has proved nothing yet.
- After a fix, break the production line on purpose (delete or invert it) and run the tests. If
  they stay green, the test is hollow: tighten it until the break turns it red, then restore.
- Check the test count after every run. If it dropped after you added tests, a file failed to
  load.
- Zero skipped tests on the files that matter.

## 3. Read results the right way

- Never pipe a command whose exit code you will act on (`npm test | tail` reports the exit code
  of `tail`). Run it bare, then read the output in a second step.
- Never hide a failing command's errors (`2>/dev/null`) while you are working out why it fails.
- A tool's own "success" message is a claim. Re-read the end state with a separate command.
- A contradiction in your own output means the check is broken. Fix the check before you blame
  the app.

## 4. Keep secrets out of sight

- Never print a key, token or password. A fingerprint (length, first 4, last 4) is the most you
  show.
- Never `cat`, `head` or `tail` a `.env` file, and never `grep` a line out of it: that prints the
  value. To confirm a setting exists, use `grep -q '^NAME=' .env && echo "NAME is set"`.
- Never screenshot a page that shows a secret.
- Never commit a secret. Scan before the first push.

## 5. The user holds three gates

- **Plan:** you deliver the plan and stop.
- **Build:** after the user says to build, you build, test and commit, then stop.
- **Push:** you push, open a pull request, merge or deploy only after the user says so, each
  time.
- A build go covers one slice, including fixing what its review finds. The next slice needs its
  own go, and so does every push, merge and deploy. Production deploys always need their own
  yes.
- Ask before deleting data, branches or accounts you did not create in this session.

## 6. Review every change, including your fixes

- Every change gets a second-opinion review before it is pushed (`precheck`).
- Each round of fixes is a new change and gets its own review.
- Before merging, the merged result must be exactly the code you tested:
  `git merge-tree --write-tree origin/main HEAD` must print the same tree as
  `git rev-parse HEAD^{tree}`.
- A bug fixed in one place may live in others. Search for every other place with the same
  pattern.

## 7. Work in small slices

- Build one thin slice that works end to end, check it, then widen it.
- Before you build on something uncertain (a new library, an outside API), try it in a
  throwaway probe first.
- Change only what the slice needs. Match the patterns the project already uses.
- Commit messages carry no attribution lines. Read every new commit message back with
  `git log -1 --format=%B`; if a co-author attribution trailer slipped in, amend that commit's message
  before anything else (some hosting plans refuse deploys from commits with unknown co-authors).

## 8. Write for the user

- Plain words, short sentences. Lead with the answer, then the evidence.
- No long dashes (use a hyphen or a colon).
- Give one recommendation with the reason. Offer a list of options only when asked.
- Never give time estimates for coding work.

## Where loop state lives

The build-loop skills keep their state in the project, so any tool can pick the work up:

| Path | What | Committed |
|---|---|---|
| `.build-loop/brief.md` | The product brief from `new-build` | yes |
| `.build-loop/plan.md` | The slices, each with a status | yes |
| `.build-loop/reviews/` | Audit reports from `code-audit` | yes |
| `.build-loop/parity/` | Design references and comparisons from `figma-parity` | yes |
| `.codex/reviews/` | Review records from `precheck` | yes |
| `qa/runs/<ts>/brief.md`, `findings.json` | Walk results from `qa-walk` | yes |
| `qa/runs/<ts>/` screenshots, transcript, state, network log | Walk working files | no (add to `.gitignore`) |
| `.claude/sessions/` | The repository copy of each `wrap` handover | yes |

A slice status is one of `pending`, `building`, `review`, `done` or `blocked`. Only evidence
moves a slice forward: a slice is `done` once its walk passed.
