---
name: precheck
description: Use BEFORE pushing client-touching commits. Runs Codex `exec review` against staged + uncommitted + last-N commits, surfaces P1/P2 findings, and gates push on a clean verdict. Trigger phrases - "precheck", "review before push", "should I push", "is this ready to push", "codex check before push", `/precheck`.
---

# /precheck - Pre-push Codex review gate

Lightweight wrapper over `codex exec review --base <sha>` for catching ship-breaking bugs before they land on origin or a standalone client remote. It is user-invoked before commit or push.

## Why this exists

Codex catches ship-breaking regressions the implementing agent can miss. Standalone client repositories may have different hook configuration, so run this gate explicitly before delivery.

`/precheck` closes that gap as an opt-in pre-flight, not a hard hook. Same model as `/ultrareview`: explicit invocation, no friction on doc/script/internal-tooling commits.

## Usage

```
/precheck                              # default: review HEAD~1..HEAD + any uncommitted+staged
/precheck HEAD~3                       # review last 3 commits + uncommitted
/precheck <sha>                        # review <sha>..HEAD
/precheck --last 5                     # review last 5 commits (no uncommitted)
/precheck --client-only                # review the current standalone client repository
/precheck --staged-only                # review just staged changes (pre-commit gate)
```

Output lands at `.codex/reviews/precheck-<topic>-<ts>.md` so the full review is preserved alongside the existing post-push reviews.

## Workflow

### Step 1 - pick a base

Decision tree:
1. User passed an explicit `<sha>` or `HEAD~N` → use that.
2. `--last N` → use `HEAD~N`.
3. `--staged-only` → use `HEAD` (review only staged delta).
4. Default → use `HEAD~1` so the review covers the most recent commit plus any uncommitted/staged work.

Refuse with a clear error if `<sha>..HEAD` would be empty AND no uncommitted/staged changes exist - nothing to review.

### Step 2 - scope check

Before firing Codex, summarize what's in scope so the user can sanity-check:

```bash
git log --oneline <base>..HEAD
git status --short
git diff --stat <base> HEAD
```

If the current repository is not a standalone client project and the user did not pass `--client-only`, ask before firing. Codex review on routine internal docs is usually unnecessary friction.

For diffs that span >50 files or >5000 LOC, warn the user - Codex review at that scope tends to silent-exit per `feedback_codex_cli_silent_exit_workaround`. Recommend tightening scope via `--last 1` or a tighter base.

### Step 3 - fire Codex in background

FIRST, a workdir + context guard. `AGENTS.md` is the ONLY reviewer-prompt channel codex loads headless (persona, severity template, priorities, Known Failure Modes). A review fired from a scratchpad/extracted/trial dir with no `AGENTS.md` in the cwd->root chain runs PERSONA-LESS - it silently loses the entire prompt layer (real failure: a July precheck ran with workdir in a scratchpad trial dir). So:

```bash
# Refuse to review persona-less. Walk cwd -> / looking for an AGENTS.md.
d="$PWD"; found=""
while [ "$d" != "/" ]; do [ -f "$d/AGENTS.md" ] && { found="$d/AGENTS.md"; break; }; d=$(dirname "$d"); done
[ -z "$found" ] && { echo "ABORT: no AGENTS.md in cwd->root chain; review would run persona-less. cd into the repo."; exit 1; }
```

For client work, run Codex from the standalone repository root so its `AGENTS.md` loads.

Then fire, using the pinned `review` profile (validated reliable):

```bash
TS=$(date +%Y-%m-%dT%H-%M-%S)
TOPIC="<derive-from-most-recent-commit-subject-or-cwd-project>"
OUT=.codex/reviews/precheck-${TOPIC}-${TS}.md

nohup codex exec --profile review -c plugins={} --color never --disable image_generation \
  review --base <BASE_SHA> --skip-git-repo-check \
  > "$OUT" 2>&1 &
PID=$!
echo "Codex precheck PID=$PID  →  $OUT"
```

CRITICAL placement: EVERY flag above is `exec`-level and must go BEFORE the `review` sub-subcommand. `review` accepts only `--commit`, `--base`, and `--skip-git-repo-check`, plus an optional prompt. Do not add a sandbox bypass.

This bit on 2026-08-13, on a real review run: the older form with `--color never` after `review` died instantly with `error: unexpected argument '--color' found`, and `--title` is no longer accepted there at all. The tell was a 239-BYTE output file - far too small to be a review. ALWAYS size-check the output before reading a verdict out of it; a flag-parse death and a clean pass are both "exited quickly with no findings" if you only look at the exit code. Read the usage line codex prints on error rather than guessing which flag moved.

**TWO EFFORT LANES - pick by blast radius:**

| Lane | Profile | Model / effort | Use for |
|---|---|---|---|
| Routine | `--profile review` | `gpt-5.6-sol` / medium | every ordinary precheck. THE DEFAULT. |
| Delivery boundary | **`/code-review`** | `gpt-5.6-sol` / max | client-repo push, App Store / TestFlight submission, prod deploy, a multi-commit handoff bundle. Do not hand-roll it here - `/code-review` owns the frontier lane and carries the pre-ship charter. |

**VOLUME matters more than tier on a long review (measured 2026-08-12).** Cost is
`tokens x price`, and the tier only moves the second term. A trivial one-word turn
already carries ~70K input tokens of baseline, ~63% of it served from prompt cache;
the 12 enabled plugins plus the memories subsystem are ~8.2K of that on EVERY turn
(70,375 -> 62,137 measured), and memories fires its own unrelated tool calls. Plugins
CANNOT be cleared from a profile - an empty `[plugins]` table silently does nothing,
unlike `[mcp_servers]` - so always pass `-c plugins={}` on the command line. The
larger term is tool output: every `sed`/`cat` result stays in context and is re-sent
each turn, which is why review transcripts reach 1.2 MB. Scope with `--commit <sha>`
or `--uncommitted` before reaching for a cheaper model.

Do NOT reach for the deep lane because a diff feels important - reach for it when the artifact is leaving for a client or a store, and reach for it by running `/code-review` rather than by bumping this skill's model. On 2026-08-05 an orchestrator pilot pinned EVERY lane to `gpt-5.6-sol` at forced-`high` effort (sol's own default effort is `low`) and the plan's usage was gone in two days. The tier is ONE of two multipliers, not the whole control: it sets the price per token while the volume levers above set how many tokens there are, and they multiply. Forcing `high` on a model whose default is `low` is the part that was pure waste - it bought reasoning tokens nobody decided to spend.

NOTES (validated 2026-05-22/23; sandbox backport 2026-06-07; image-gen crash fix 2026-06-17; review profile 2026-07-11; cost tiering 2026-08-12):
- `--profile review` layers `~/.codex/review.config.toml`, which PINS the model + effort + read-only sandbox + `approval_policy = "never"` + an empty `[mcp_servers]` table (no npx server boots for a read-only review). This makes the gate DETERMINISTIC - it no longer drifts when the interactive codex model changes or auto-migrates. Tracked source of truth for both lanes: `.codex/profiles/review.config.toml` and `.codex/profiles/review-deep.config.toml`; the home-dir copies mirror them. Read the pin out of the tracked file rather than trusting any model name quoted in prose - a stale hardcoded `gpt-5.5` in this skill and in the hook is exactly what hid the switch to sol for a week.
- Valid codex slugs are `gpt-5.6-sol` / `-terra` / `-luna` (plus the older `gpt-5.5`). A bare `gpt-5.6` is NOT a slug; `gpt-5.4` and `gpt-5.4-mini` are flagged deprecated in codex's model cache.
- FRESH-MACHINE FALLBACK: `--profile review` requires the home-dir `~/.codex/review.config.toml` to exist, else the review exits with NO-VERDICT. If it's absent, mirror the tracked profile into `~/.codex/`, or use inline pins read from it: `codex exec -c model="gpt-5.6-sol" -c model_reasoning_effort="medium" -c sandbox_mode="read-only" -c approval_policy="never" review --base <sha> ...`. (The tracked pre-push hook auto-falls-back this way, sourcing the pins FROM `.codex/profiles/`, so its fallback cannot drift from the real gate.)
- `--disable image_generation` STAYS (belt-and-suspenders alongside the profile's `features.image_generation = false`) and needs codex-cli >= 0.140. It turns off the built-in image_gen tool that codex wires to the dead `gpt-image-2` model. Without it, GPT-5.x occasionally calls image_gen at review-end, the API 400s (`image_generation_user_error: The model 'gpt-image-2' does not exist`), and the review dies with NO verdict. On 0.130 the toggle is accepted but ignored - upgrade first (`npm i -g @openai/codex@latest`).
- ALWAYS direct-redirect with `>`, NEVER pipe (`feedback_codex_headless_no_pipe_buffering` - pipes buffer codex output indefinitely).
- GOTCHA: `-s/--sandbox` is rejected by the `review` sub-subcommand ("unexpected argument '-s'"). The profile's `sandbox_mode` handles it.
- The `codex exec review` subcommand IS purpose-built for diff review; do NOT pass a custom `[PROMPT]` along with `--base` - they are mutually exclusive (CLI rejects the combo).
- `--base <sha>` works against any commit; doesn't have to be `origin/master`. For a re-run after a P1 fix, review ONLY the fix - `--commit <sha>` (a single commit) or `--uncommitted` (staged+unstaged+untracked) - instead of re-scanning the whole `--base` range. Cheaper and tighter.
- Process runs ~2-4 min depending on diff size + model. Don't poll; use the Monitor tool until-loop.

After the run completes (Step 4), append a one-line record to the shared history log so the workhorse precheck path is measurable. **Log the model and effort codex ACTUALLY resolved** (they are printed in the transcript header) rather than the pin you asked for, plus transcript bytes as a context-burn proxy - without those fields a silent re-pin of the gate is invisible until the plan runs dry, which is precisely what happened in August:

```bash
verdict=$(awk '/^codex$/{f=1} END{exit !f}' "$OUT" && echo OK || echo NO-VERDICT)
ran_model=$(sed -n 's/^model:[[:space:]]*//p' "$OUT" | head -1)
ran_effort=$(sed -n 's/^reasoning effort:[[:space:]]*//p' "$OUT" | head -1)
bytes=$(wc -c < "$OUT" | tr -d ' ')
printf '%s verdict=%s model=%s effort=%s bytes=%s out=%s topic=%s\n' \
  "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$verdict" "${ran_model:-unknown}" "${ran_effort:-unknown}" \
  "$bytes" "$OUT" "$TOPIC" \
  >> .codex/reviews/.history.log
```

A routine precheck that logs `model=gpt-5.6-sol` is a misconfiguration, not a thorough review - check `~/.codex/review.config.toml` against `.codex/profiles/review.config.toml`.

### Step 3b - reviewer fan-out does not run inside precheck

A four-agent reviewer fan-out used to run here in parallel with Codex. It was removed from `/precheck` because four subagents over the full diff spend too many tokens on every routine commit.

`/precheck` is now Codex-only: one lightweight external reviewer, cheap enough to run on every push.

Use `/code-review` at a delivery boundary (a downstream push, a milestone handoff, or a store submission). That is where the heavier ruleset (ownership checks, Supabase IDOR, EAS env vars, NativeWind, Expo Router groups) earns its cost. Do not fire a multi-agent review on every push. The separate reviewer plugin that used to provide that fan-out is not in this library.

### Step 4 - wait for completion (Monitor tool)

```
Monitor: until ! ps -p <PID> >/dev/null 2>&1; do sleep 10; done
         echo done; wc -l $OUT
```

Set timeout 600000ms (10 min). If it exceeds, the diff was likely too broad - kill the process, suggest a tighter base, ask user.

### Step 5 - extract verdict

Codex final message lands after a `codex` sentinel line near the bottom of the output file.

**Pitfall (found 2026-08-11, on a real review run): on a longer/deeper review, codex can emit an INTERMEDIATE `codex` sentinel line mid-transcript while it is still exploring/tool-calling, before the TRUE final verdict.** The naive first-match awk pattern below grabs that intermediate block instead - caught only because the extracted text was suspiciously identical to a prior round's finding. Always extract from the LAST `codex` sentinel, not the first:

```bash
LAST=$(grep -n '^codex$' "$OUT" | tail -1 | cut -d: -f1)
tail -n +"$((LAST + 1))" "$OUT" | head -120
```

If you already ran the first-match form (`awk '/^codex$/{flag=1; next} flag' "$OUT"`), cross-check it against `tail -n 20 "$OUT"` before trusting it - if the file's literal last lines differ from what awk extracted, the verdict is wrong and you must re-extract from the last sentinel.

Look for `[P1]`, `[P2]` severity tags + `file:line` refs. Report a 3-column table to the user:

```
| Severity | File:line | Issue + Fix Direction (1 line) |
```

ALSO scan for the implicit verdict - Codex doesn't emit a literal `VERDICT: GO/NO-GO` for `exec review`, but the opening sentence is always the summary ("X is broken by Y; should be fixed before shipping" vs "no significant issues found"). Quote that sentence verbatim as the verdict line.

### Step 6 - gate the push

Gate on the Codex verdict (Step 5) alone:

| Codex | Gate |
|-------|------|
| no findings | Clean. Safe to push. |
| P2 only | Non-blocking. Show findings; let user decide. |
| P1 present | Blocking. Don't push. |

Print the Codex 3-col table before the verdict line so the user can sanity-check.

DO NOT auto-push. Push only when the operator asks. This skill stays opt-in advisory.

DO NOT auto-push. Push only when the operator asks. This skill stays opt-in advisory.

## Examples

### Example 1 - default precheck before a routine push

```
User: /precheck
You:  [run review against HEAD~1..HEAD + 2 uncommitted files]
      [find 1 P2 about a missing CORS header on an error path]

      Codex precheck (HEAD~1..HEAD, 4 files):
      | Severity | File:line | Issue |
      | P2 | functions/foo/index.ts:127 | Missing CORS headers on 500 path |

      Verdict: minor - non-blocking. Recommend fix in same commit before push.
```

### Example 2 - bundle review before a delivery

```
User: /precheck origin/master --client-only
You:  [4 commits, 9 files all under ~/projects/<app>/]
      [Codex finds 2 P1 + 1 P2]

      Codex precheck (origin/master..HEAD, 9 files in <app>):
      | Severity | File:line | Issue |
      | P1 | checkout-session:178 | charged amount does not match the displayed amount |
      | P1 | roles:229 | JWT role-claim forgeable... |
      | P2 | confirmation.tsx:66 | Skips push notification... |

      Verdict: 2 P1s block push. Fix before pushing.
      Want me to fix and re-precheck?
```

### Example 3 - pre-commit gate on staged work

```
User: /precheck --staged-only
You:  [review just the staged files vs HEAD - no commits yet]
      [Codex finds 0 issues]

      Codex precheck (staged only, 3 files):
      No issues.

      Safe to commit. Recommend: git commit -m "..." -- <staged paths>
```

## When NOT to use /precheck

- Pure docs commits (CLAUDE.md edits, README updates, memory file changes in `~/.claude/`). Codex review on these is token-waste.
- Single-file typo fixes or whitespace cleanups.
- Planning docs that are not shippable code.
- Internal tooling under `capabilities/`, `scripts/`, `templates/` unless it's about to land in a client product.

## When you absolutely SHOULD use /precheck

- Before any standalone client-repo push that includes edge functions, migrations, payment-flow code, or auth/RLS changes.
- Before a downstream delivery. A later hook may review the push, but precheck catches the bug before it lands in that remote's history.
- Before signaling "ready to deploy" or "ready to deliver" to a stakeholder.
- After multiple commits in a session - bundle-review catches cross-commit drift (e.g., a P2 in commit A becomes a P1 because commit C changed the assumption).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Passing `[PROMPT]` along with `--base` | `codex exec review` rejects the combo. Use either custom prompt OR `--base`, not both. Default review behavior + `--base` is the working pattern. |
| Piping codex output (`| tee` / `\| grep`) | Pipes buffer codex stdout indefinitely. Direct-redirect with `>` only. |
| Reviewing >50 files at once | Silent-exit risk per `feedback_codex_cli_silent_exit_workaround`. Tighten via `--last 1` or specific `<sha>`. |
| Auto-pushing after clean precheck | Don't. Let the user invoke push explicitly only when the operator asks. |
| Trusting "no findings" without checking the output file | Codex sometimes exits before generating a verdict on huge diffs. Always verify the output file ends with a real `codex` message + summary, not just exploration logs. |
| Running precheck on a doc-only commit | Token waste. Skip unless it changes client deployment instructions. |

## Integration with existing tools

- **A pre-push hook (`.githooks/pre-push`)** - blocks non-origin pushes from the private checkout. Standalone client repositories own their own push gates.
- **`/ultrareview`** - same invocation model (user-triggered), but heavier (multi-agent review of full branch). Precheck is the lightweight daily-driver; ultrareview is the pre-major-release gate. That command is not in this library.
- **`/code-review` (the skill)** - the manual 3-pass audit. Precheck is faster; code-review is more thorough. Use precheck for routine commits; code-review for a store submission or a handoff.
- A four-agent reviewer fan-out is an end-review gate, not a per-push gate. It is not shipped here. Use `/code-review` at a delivery boundary.

## Implementation notes

- Write reviews under `.codex/reviews/` in the checkout (a pre-push hook may write there too). Don't create a separate `.codex/precheck/` dir; co-locate so all codex artifacts live in one place.
- `<topic>` for the filename: take the most recent commit's scope tag (for example `checkout` from `fix(checkout): ...`) or fall back to the leaf directory name.
- Never log the review verdict to STDOUT alone - always write to file FIRST so it survives the conversation context.
- If `codex` CLI is missing or auth-expired, fail loud with `Codex CLI missing or unauthenticated. Run `codex login` to fix.` - don't silently fall back.
