#!/usr/bin/env python3
"""PreToolUse hook: Workflow cost discipline.

Fires the cost guard at the exact decision point (the Workflow tool call),
because passive rules in CLAUDE.md/rules demonstrably did not stop a
33-agent / 2.55M-token all-Opus fan-out on 2026-06-01.

Behavior:
  - BLOCK (exit 2) only the precise failure pattern: a parallel()/pipeline()
    fan-out with ZERO model tiering (every agent inherits the main-loop model,
    i.e. Opus, across the whole fan-out). The fix is trivial: add
    model:'sonnet'/'haiku' to the reader/verifier agents, reserve Opus for the
    final synthesis. Escape hatch: put `WF_BUDGET_OK:<reason>` anywhere in the
    script (e.g. a comment) and it passes.
  - ADVISE (exit 0 + stderr note) on any non-trivial workflow: surface the
    static agent-call count, the fan-out multiplier risk, and the
    announce-before-launch reminder. Non-blocking.
  - Tiny workflows (<=3 agent calls, no fan-out): silent allow.

FAIL OPEN: any error or unreadable script -> exit 0.
"""
import sys, json, re, os

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input", {}) or {}
    script = ti.get("script") or ""
    if not script and ti.get("scriptPath"):
        try:
            with open(ti["scriptPath"]) as f:
                script = f.read()
        except Exception:
            sys.exit(0)
    # Saved-name workflow (no inline script/path): can't analyze the fan-out
    # statically. Named heavy workflows (deep-research, audits, sweeps) are
    # exactly what saturated the API on 2026-07-04 (~4M tokens, locked out every
    # other session). Block the known-heavy names unless explicitly allowed.
    if not script:
        name = str(ti.get("name") or "")
        allowed = os.environ.get("WF_ALLOW_HEAVY") == "1" \
            or "WF_BUDGET_OK" in json.dumps(ti.get("args") or "")
        if re.search(r"deep[-_]?research|audit|sweep|fan[-_]?out|research", name, re.I) \
                and not allowed:
            sys.stderr.write(
                "Workflow budget guard: BLOCKED named workflow '%s'.\n" % name
                + "Named heavy workflows fan out to dozens of concurrent agents and can\n"
                + "saturate the API rate limit, starving every other session (happened\n"
                + "2026-07-04). Prefer DIRECT work: for fetch/compare of known URLs use\n"
                + "WebFetch + the API in a few single-threaded calls.\n"
                + "To override: set WF_ALLOW_HEAVY=1, or add WF_BUDGET_OK:<reason> to args.\n"
                + "Announce the agent count to the user BEFORE launching.\n"
            )
            sys.exit(2)
        sys.exit(0)

    # Explicit operator override.
    if "WF_BUDGET_OK" in script:
        sys.exit(0)

    agent_calls = len(re.findall(r"\bagent\s*\(", script))
    has_parallel = bool(re.search(r"\bparallel\s*\(", script))
    has_pipeline = bool(re.search(r"\bpipeline\s*\(", script))
    has_map_agent = bool(re.search(r"\.map\s*\(", script)) and agent_calls > 0
    fanout = has_parallel or has_pipeline or has_map_agent

    # Cheaper-tier override present anywhere in the script?
    tiered = bool(re.search(r"model\s*:\s*['\"](sonnet|haiku)", script))

    # Secondary fan-out nested under a primary one => real agent count is the
    # PRODUCT of the two list lengths (items x per-item children). This is the
    # multiplier that turned an expected ~13 into 33.
    nested = bool(re.search(r"=>\s*parallel\s*\(", script)) or \
        bool(re.search(r"parallel\s*\([\s\S]*?parallel\s*\(", script))

    # --- BLOCK: fan-out with no cheaper-tier model anywhere ---
    if fanout and not tiered:
        msg = [
            "Workflow budget guard: BLOCKED - this is a fan-out with no model tiering.",
            "Every agent() in a parallel()/pipeline() fan-out will inherit the main-loop model (Opus).",
            "That is exactly the 33-agent / 2.55M-token overrun pattern from 2026-06-01.",
            "",
            "Fix one of:",
            "  - Add model:'sonnet' (or 'haiku') to the reader/verifier/extractor agents in the fan-out;",
            "    reserve Opus (omit model) ONLY for a final synthesis/judgment agent.",
            "  - If the fan-out genuinely needs Opus, add  WF_BUDGET_OK:<reason>  (e.g. a // comment) to the script.",
            "",
            "Also before relaunching: estimate the REAL agent count (per-item verify layers MULTIPLY:",
            "items x risks-per-item), and announce that count to the user if it exceeds ~8.",
        ]
        if nested:
            msg.insert(3, "WARNING: a nested parallel()/pipeline() detected -> real agent count = items x per-item children, not the static agent() count.")
        sys.stderr.write("\n".join(msg) + "\n")
        sys.exit(2)

    # --- ADVISE: non-trivial workflow, tiered or small fan-out ---
    if agent_calls > 3 or fanout:
        note = [
            f"Workflow budget note: ~{agent_calls} static agent() call sites"
            + ("; fan-out present (parallel/pipeline)." if fanout else "."),
        ]
        if nested:
            note.append("Nested fan-out: REAL agent count multiplies (items x per-item children) - count it honestly.")
        note.append("Model tiering detected (sonnet/haiku in use)." if tiered
                    else "No cheaper-tier override seen - confirm Opus is warranted for every agent.")
        note.append("If the real count exceeds ~8, announce it to the user BEFORE launching, not after.")
        sys.stderr.write("\n".join(note) + "\n")
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
