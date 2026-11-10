---
name: ship
description: Use when the user says "push it", "ship it", "open a PR", "merge it", "go". Runs the push and merge gate: checks the branch, a clean tree, green gates on the exact commit and a clean review, then pushes, opens a pull request, and merges only on a separate merge go.
---

# Ship

Load the `build-rules` skill first and follow it throughout.

This skill has two gates. "Push" lets you push and open a pull request. "Merge" is a separate word and lets you merge. A go for one never covers the other, and a go for one change does not carry to the next.

## 1. Refuse without a go

If the user has not said push, ship, go or the like for this change, stop and ask. A slice set to `review` is not permission. Never push on your own initiative.

## 2. Pre-push checks

Run each, read the result, and stop at the first failure.

```bash
git branch --show-current          # must be a feature branch, never the default branch
git status --short                 # must be empty
git fetch origin
git log --oneline origin/HEAD..HEAD   # the commits you are about to push
```

1. **Branch:** if you are on the default branch (`git symbolic-ref --short refs/remotes/origin/HEAD` names it), create a branch first (`git switch -c feat/<short-name>`). Never push straight to it. `origin/HEAD` is git's own pointer to the remote's default branch, so it works in every shell. If git says it does not exist, run `git remote set-head origin --auto` once.
2. **Clean tree:** anything uncommitted is committed or named to the user before going on.
3. **Gates on this exact commit:** run `git rev-parse HEAD`, then the test, typecheck and lint commands, each bare with `echo "exit: $?"`. Compare the test count with the last run. All must pass on this HEAD.
4. **Review:** find the newest precheck record in `.codex/reviews/` (where `precheck` writes it) and its reviewed sha. `git diff --name-only <reviewed-sha>..HEAD` may list only files under `.codex/reviews/`, `.build-loop/reviews/` and the app's `qa/runs/` (review records and walk reports). If it lists anything else, run `precheck` on the commits after that sha. A push go does not cover changing code: if precheck finds anything, report it and **stop** for the user's go to fix it. Push only on a clean verdict. A review that ends with no verdict counts as failed.
5. **Secrets:** scan the commits you will push for keys and tokens (`git diff origin/HEAD..HEAD` read for key-shaped strings, and any secrets file in the file list). Stop and tell the user if anything shows up.
6. **Walk:** if the slice has no `qa-walk` brief under the app's `qa/runs/` with no blocking findings, say so in the pull request instead of calling it verified.

## 3. Push and open the pull request

```bash
git push -u origin "$(git branch --show-current)"
echo "exit: $?"
```

Never force-push. If the push is rejected, fetch, read what changed, and bring the branch up to date with a normal merge or rebase of your own commits. Ask first if that touches commits other people made.

Check the tools first: `gh --version` and `gh auth status`.

- With `gh`: `gh pr create --title "<conventional title>" --body-file <path to a file you wrote>`.
- Without `gh`, or when it is not signed in: print the compare link for the branch from `git remote get-url origin` and hand the user the title and body to paste.

The body has three parts: **Summary** (what changed and why, in plain words), **Verification** (each check that ran with its result, and each check that did not run, named), and **Risks** (what could go wrong and how to undo it). No internal ticket text, no prices.

Then confirm the push landed: `git merge-base --is-ancestor HEAD origin/<branch>` must exit 0.

**Stop.** Report the pull request link and the Verification section. Wait for a merge go.

## 4. Merge (only on a separate merge go)

```bash
git fetch origin
git merge-tree --write-tree origin/HEAD HEAD
git rev-parse 'HEAD^{tree}'
```

The two printed trees must be identical. If they differ, the merge would produce code you did not test: stop, bring the branch up to date, re-run the gates and the review, and ask again.

Then merge with the exact commit pinned. Give the merge a plain subject and body of your own with no attribution lines:

```bash
gh pr merge <number> --merge --match-head-commit "$(git rev-parse HEAD)" \
  --subject "<conventional subject>" --body "<plain summary>"
```

Without `gh`, give the user the merge button steps and the sha to confirm.

After the merge, check the landed commit:

```bash
git fetch origin
git log -1 origin/HEAD
git merge-base --is-ancestor <sha> origin/HEAD
echo "landed: $?"
```

The log shows your change and `landed` is 0. Only then say it is merged. Set the slice to `done` if its walk passed.

## 5. Deploys

Never deploy to production without its own yes from the user, naming the target. A merge go is not a deploy go. Staging deploys need a go for that deploy too. After any deploy, check the changed behaviour on the live address.

## Report

- the branch, the sha and the pull request link,
- the gate results on that sha,
- the review verdict,
- whether it is pushed, merged or deployed, each stated only after its check passed.
