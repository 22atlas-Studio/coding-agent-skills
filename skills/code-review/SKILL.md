---
name: code-review
description: Use when preparing to ship a client app, before App Store submission, before handoff, or when user says "review code", "pre-ship audit", "is this ready to ship", "find bugs". Runs the frontier codex reviewer (gpt-5.6-sol at max reasoning) over the deliverable, then fixes and re-verifies.
---

# Pre-Ship Code Review - the frontier codex reviewer

The single deepest review this library has. One frontier reviewer at maximum reasoning
depth (`gpt-5.6-sol` / `max`) replaces the old parallel-Claude-agent passes, on
the reasoning that a second opinion is only worth paying for when it comes from a
different model than the one that wrote the code.

**This is the expensive lane and the ONLY deep one.** Routine pre-push review is
`/precheck` (`gpt-5.6-sol` / medium). Do not run this on iteration.

## When to use

- Before App Store / Play Store / TestFlight submission
- Before a standalone client-repository push, delivery, or handoff
- Before a production deploy
- After a major feature milestone, on the bundle

## Cost shape - read before firing

`gpt-5.6-sol` at `max` is the top of the ladder available to us
(`low` < `medium` < `high` < `xhigh` < `max` < `ultra`; `low` is sol's own
default, and `ultra` is banned - see below). Two things drive the bill, and they
multiply:

- **Price per token** - the tier. Fixed by the profile.
- **Token volume** - yours to control. Every tool result stays in context and is
  re-sent on each later turn, so a sprawling read is what makes a review costly.
  Measured 2026-08-12: a one-word turn already carries ~70K input tokens of
  baseline, and frontier-tier runs at high effort averaged 0.65 MB of transcript
  versus 0.31 MB on the previous gate - deeper effort buys more exploration, not
  just pricier tokens.

So scope deliberately. A whole-repo audit on a 400-file app is a different
purchase from a 12-file release bundle, and the model will read as widely as you
let it.

`ultra` exists above `max` and is **not available**. It is defined as "maximum
reasoning with automatic task delegation" - it spawns its own sub-agents, so
unlike a model pin its cost is unbounded rather than merely high, and delegated
fan-out you cannot see or cap is the exact shape that drained the plan in August
2026. `scripts/check_codex_pilot.py` rejects it in every lane, and `max` is the
ceiling here. Using it would mean a deliberate, reviewable edit to `BANNED_EFFORT`
in that gate - which is the point. Do not reach for it to make one review
"more thorough".

## Step 1 - preflight gate

Never spend the frontier lane on code that does not compile.

```bash
# whatever the PROJECT configures, not a bare global invocation
npx tsc -p tsconfig.app.json --noEmit     # or the package's own typecheck script
```

A package with no typecheck script is **ungated, not clean** - say which packages
you actually covered. If the build is red, fix it and re-run before Step 2.

## Step 2 - scope the review

```bash
git log --oneline <base>..HEAD
git diff --stat <base> HEAD
```

State the scope out loud before firing: file count, LOC, and whether this is a
bundle review or a whole-repo audit. Over ~50 files or ~5000 LOC, split it - a
too-broad diff both costs more and degrades into silent-exit
(`feedback_codex_cli_silent_exit_workaround`).

## Step 3 - fire the frontier reviewer

`codex exec review --base <sha>` is purpose-built for diffs but **rejects a custom
prompt** (`--base` and `[PROMPT]` are mutually exclusive - verified again on
codex 0.144.6 and again on 0.146.1, exit 2). The pre-ship charter below is the whole point of this
skill, so use the freeform `codex exec` form with the diff written to a file the
prompt names - the same pattern `.githooks/pre-commit` uses.

```bash
TS=$(date +%Y-%m-%dT%H-%M-%S)
OUT=.codex/reviews/codereview-<topic>-${TS}.md
git diff --no-color <base> HEAD > ./.codex-review-diff

nohup codex exec --profile review-deep -c plugins={} \
  --skip-git-repo-check --color never --disable image_generation \
  "$(cat ~/.claude/skills/code-review/charter.md)" \
  > "$OUT" 2>&1 < /dev/null &
PID=$!
```

- `--profile` and `-c` are **exec-level**: they precede everything.
- `-c plugins={}` is mandatory - plugins cost ~6K input tokens on EVERY turn and
  CANNOT be cleared from a profile (an empty `[plugins]` table silently does
  nothing, unlike `[mcp_servers]`).
- Direct-redirect with `>`, **never pipe** - pipes buffer codex output forever.
- Close stdin with `< /dev/null` or codex hangs on "Reading additional input".
- Clean up `./.codex-review-diff` afterwards.

Wait with the Monitor tool (`until ! kill -0 <PID>`), not sleep-polling. Budget
10 min; `max` effort is slow by design.

## Step 4 - extract the verdict, and log what it cost

Read from the **LAST** `codex` sentinel, not the first - on a deep run codex
emits intermediate sentinels while still exploring:

Strip ANSI first. codex-cli 0.146.1 began emitting colour codes into REDIRECTED
output, which silently zeroed both the sentinel match and the model/effort parse -
`--color never` fixes it at the source, but do not depend on that alone:

```bash
CLEAN=$(mktemp); sed -e 's/\x1b\[[0-9;]*m//g' "$OUT" > "$CLEAN"
LAST=$(grep -n '^codex$' "$CLEAN" | tail -1 | cut -d: -f1)
tail -n +"$((LAST + 1))" "$CLEAN" | head -160
grep -oE 'VERDICT: (GO|NO-GO)' "$CLEAN" | tail -1
```

Then append the cost line, reading back the model codex ACTUALLY resolved rather
than the pin you asked for:

```bash
printf '%s verdict=%s model=%s effort=%s bytes=%s out=%s topic=%s\n' \
  "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$VERDICT" \
  "$(sed -n 's/^model:[[:space:]]*//p' "$CLEAN" | head -1)" \
  "$(sed -n 's/^reasoning effort:[[:space:]]*//p' "$CLEAN" | head -1)" \
  "$(wc -c < "$OUT" | tr -d ' ')" "$OUT" "<topic>" \
  >> .codex/reviews/.history.log
```

**A missing verdict is not a pass.** Exit 0 with no findings block means the
review died (no-verdict death); re-run once, then fall back to the read-only
reviewer agents rather than reporting a clean result.

## Step 5 - fix

Claude fixes; the frontier model reviews. Do not spend the expensive lane on
edits. Group fixes by file ownership so parallel work cannot collide, run the
project's gates after each group, and treat every finding as a hypothesis until
reproduced - a reviewer's verdict is unverified input like any other.

## Step 6 - round 2, scoped to the delta

Re-review **only the fixes**, never the whole bundle again:

```bash
codex exec --profile review-deep -c plugins={} review --color never --uncommitted   # or --commit <sha>
```

Report each original finding as VERIFIED / NEW ISSUE / REMAINING. Repeat until
clean. Round 2 on the full base range is the single easiest way to double the
cost of this skill for no added coverage.

## Step 7 - ship report

```
## Ship Report - <project>
- Gates: <package>: PASS (0 errors)   <package-without-typecheck>: UNGATED
- Reviewer: gpt-5.6-sol / max
- Findings: N (P1: n, P2: n)
- Fixed: N   Accepted: N (each with justification)
- Recommendation: GO / NO-GO
```

Never upgrade a green functional pass to "launch-ready" - name the open legs
(cross-browser, perf, a11y, load) explicitly.

## The charter

The review checklist lives in `charter.md` next to this file and is passed as the
prompt. Always reference it through the global skill path
(`~/.claude/skills/code-review/charter.md`), never a repo-relative one: this skill
runs from CLIENT repos, where `.agents/skills/...` does not exist. Keep it there, not inline here: it is the reviewer's instructions, and
editing it is how you tune what the frontier lane looks for.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Running this on routine iteration | That is `/precheck` (sol/medium). This lane is for delivery boundaries. |
| Passing `--base` with the charter prompt | Mutually exclusive. Write the diff to a file and reference it. |
| Omitting `-c plugins={}` | ~6K wasted input tokens on every turn; a profile cannot clear plugins. |
| Round 2 over the full range | Re-review only the delta (`--uncommitted` / `--commit`). |
| Reviewing code that does not compile | Preflight gate first. |
| Trusting exit 0 as a clean verdict | Parse for a real findings block; no verdict = failed review. |
| Piping codex output | Buffers forever. Direct-redirect only. |
| Parsing the transcript without stripping ANSI | 0.146.1 colours redirected output; pass `--color never` AND strip. |
| Reaching for `ultra` | Banned in every lane - unbounded delegated fan-out. `max` is the ceiling. |
