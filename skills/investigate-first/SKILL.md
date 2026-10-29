---
name: investigate-first
description: Run the Ronacher loop - investigate with the agent and write a grounded report BEFORE any code generation, gather context with composed bash pipelines instead of file dumps, and prove the dev environment is real before trusting any test result. Use when picking up an unfamiliar repo, starting a feature whose shape is not settled, debugging a system you have not read, or when a harness is about to be pointed at a codebase for the first time. Trigger phrases - "investigate first", "how should this work", "figure out the shape", "before we build", "ronacher loop".
user_invocable: true
---

# Skill: Investigate First

Source: Armin Ronacher (creator of Flask, founder of Earendil, the company
behind the Pi coding agent), David Andre podcast, September 2026.

His own description of his day: "a lot of what I'm doing actually is not so
much code generation, it is actually trying to figure out like how stuff
should work ... investigating with the machine together, here is a report,
how to get repo out of it. It is very traditional engineering for us still."

The loop below is that practice made mechanical. It is deliberately
conservative: one human driver, one real machine, no autonomous issue bot.

---

## When this fires

- The repo is unfamiliar, or the feature's shape is not settled.
- Someone is about to prompt "implement X" against a system nobody has read.
- A test result, benchmark, or "it works" claim is about to be believed.

## When it does NOT fire

- The change is a known one-liner in a file you have already read.
- You are executing an already-written spec (use the spec, not this).

---

## Step 1 - State the question, not the change

Write one sentence naming what you do not yet know. If you can only write
"implement X", you are not ready: the unknown is hiding inside X.

Bad: "add subscription cancellation."
Good: "where does subscription state actually live, and who writes it."

## Step 2 - Gather with composed bash, never with file dumps

Pi gives the model bash and little else on purpose. The reason is context
economy, not minimalism: one composed command can run several programs and
carry its own separators, so the model reads a shaped result instead of
pulling whole files into the window.

Compose one command per question, with explicit markers:

```bash
{
  echo "=== entrypoints"
  rg -l --no-messages -e 'def main|if __name__|export default|func main' -g '!node_modules' | head -20
  echo "=== writers of the state in question"
  rg -n 'subscription_status|setSubscription' -g '!node_modules' | head -40
  echo "=== migrations touching it"
  ls -1 migrations 2>/dev/null | tail -15
} 2>&1
```

Rules that make this pay off:

- `rg -n` and `sed -n 'A,Bp'` over `cat`. Read the lines that answer the
  question, not the file that contains them.
- Never pipe a command whose exit code you will report or branch on. Filter
  in a separate call (Ring 0, and it applies to investigation commands too).
- An unexpectedly empty result is a wrong-pool suspect (wrong cwd, wrong
  pathspec), not evidence of absence. Re-run from an absolute path before
  concluding anything is missing.

## Step 3 - Prove the environment is real before believing any test

Ronacher's one concrete war story: he helped someone debug a cloud coding
agent, asked how the database tests ran, and found that no Postgres had ever
started in that environment. Everything was mocked, so every run was green
and none of it meant anything.

Before quoting a test result, a benchmark, or a "verified" claim, prove the
dependencies the tests need are actually running:

```bash
echo "=== services the suite claims to need"
rg -n 'DATABASE_URL|REDIS_URL|KAFKA|localhost:5432|localhost:6379' -g '!node_modules' | head -20
echo "=== what is actually listening"
ss -ltnp 2>/dev/null | grep -E ':(5432|6379|9092|8080)' || echo "NONE LISTENING"
echo "=== containers"
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' 2>/dev/null || echo "no docker"
```

Then assert the suite actually executed: a non-zero test count, zero skips on
the specs you care about, and at least one test that touches the real service.
A green suite that collected zero tests, skipped the relevant ones, or mocked
the dependency out is not a pass. If the environment is not real, say so and
stop; do not report the green.

## Step 4 - Write the report to a file, not to chat

Investigation that lives only in a transcript dies at the next compaction.
Write it to a durable path before any edit:

`docs/investigations/YYYY-MM-DD-<topic>.md`

Fixed sections, kept short:

1. **Question** - the one sentence from Step 1.
2. **How it actually works** - with `file:line` references for every claim.
3. **Where the truth lives** - the source of truth for the state involved.
4. **Environment reality** - what is running, what is mocked, what is unproven.
5. **Open unknowns** - what is still not settled, and the cheapest probe for each.
6. **Proposed shape** - how it should work, and why that beats the alternatives.

A claim with no `file:line` behind it is a guess; label it as one or drop it.

## Step 5 - Hold, then build from the report

Deliver the report and stop. Building is the next decision, and it is a human
one. When the go comes, the report is the spec; if the build contradicts it,
the report was wrong and gets corrected in the same pass.

---

## Running this under Pi

The skill is discovered automatically: `~/.pi/agent/skills/investigate-first`
symlinks to `.agents/skills/investigate-first` in the repo, the same way
`pickup` and `wrap` do. No `--skill` flag needed.

```bash
# investigate (no writes to source; the report path is the only output)
pi "Investigate: where does subscription state live and who writes it. \
    Use the investigate-first skill. Write the report to \
    docs/investigations/$(date +%F)-subscription-state.md and change nothing else."

# build, later, from the report
pi "Implement the proposed shape in docs/investigations/<file>.md. \
    If the code contradicts the report, stop and say where."
```

Notes for this install specifically:

- Investigation is a reasoning task, not a throughput task; raise thinking
  rather than fan out. Use Pi's configured model instead of pinning one here.
- `pi-subagents` is installed, so delegation exists. Use it for the gathering
  in Step 2 if the repo is large (a `scout` at low thinking is the right shape
  for enumeration), but keep the report a single agent's work. A report
  stitched from several agents inherits every one of their guesses.
- Keep the work where the code is. A remote dev box reached over SSH or
  Tailscale beats a cloud sandbox whose services may never have started - the
  Step 3 gate exists precisely because that failure is silent.
- Do not point an autonomous issue-working bot at this loop. The value is the
  human reading the report.
