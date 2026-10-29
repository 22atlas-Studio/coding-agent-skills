---
description: Extract session learnings into skills and memory. Run at end of significant sessions.
---

# Session Retrospective

Extract reusable patterns from the current conversation and persist them.

## Instructions

### Step 1: Analyze the Current Session

Review the full conversation in context. Identify:

1. **Workflows that worked** - multi-step processes that produced good results
2. **Failures and fixes** - what broke, why, and how it was resolved
3. **Patterns worth reusing** - approaches that would help in future sessions
4. **Anti-patterns discovered** - things that wasted time or produced bad output
5. **Tool/config discoveries** - new flags, settings, or integrations found

### Step 2: Classify Each Insight

**Step 2a - SCOPE first (context locality).** Before anything else, ask of each insight: *does this apply to other projects, or only this one?* A lesson loads where it applies and nowhere else - a project-specific lesson written to root memory/CLAUDE.md bloats every future session of every project.

| Scope | Destination | Test |
|-------|-------------|------|
| **Project-specific** (this codebase's quirk, this client's decision, a file/function/flow only here) | the project's own CLAUDE.md under a `## Project Lessons` section (`the project's own CLAUDE.md`); plus the project's `memory/decisions.md` if it exists | "Would this help on a *different* project?" -> No |
| **Cross-cutting** (a stack/tool/process truth, an agency convention, a failure mode that recurs across clients) | root `~/.claude/CLAUDE.md` / `.claude/rules/` / root memory, per the type table below | "Would this help on a *different* project?" -> Yes |

Default to **project-specific** when unsure - it is cheap to promote a project lesson to root later (a recurrence proves it cross-cutting), expensive to claw a wrongly-global lesson back out of every session.

`/pickup` reads the project CLAUDE.md `## Project Lessons` block and `memory/decisions.md`, so project-scoped lessons are picked back up automatically next session (the wrap->pickup symmetry; see `docs/specs/2026-06-04-pickup-wrap-symmetry.md`).

**Step 2b - TYPE (applies to cross-cutting insights; project-specific ones just become a `## Project Lessons` bullet or a `memory/decisions.md` entry):**

| Type | Destination | When |
|------|-------------|------|
| **Workflow** (multi-step reusable process) | Skill in `.claude/skills/` | 3+ steps and likely to recur |
| **Convention** (coding style, naming) | CLAUDE.md or `.claude/rules/` | Applies across sessions |
| **Config fix** (env var, tool setting) | Memory file (file-based only) | Gotcha worth remembering |
| **Anti-pattern** (thing to avoid) | Memory file or skill update | Cost significant time |
| **Pattern/pitfall** (worked or failed) | `the pattern store` (project memory) | Any reusable success/failure/pitfall |
| **One-off fix** | Skip | Unlikely to recur |

**IMPORTANT - Memory storage rules:**
- **File-based memory** is the ONLY memory store. Write to `~/.claude/projects/<project>/memory/`
- **project memory**: patterns ONLY (`the pattern store`). Do NOT use `a second memory store` - it creates 100% duplicate data.
- **Ephemeral in-memory helpers** are not a persistence store.

### Step 3: Check for Existing Patterns

Before creating anything new:

1. Read MEMORY.md
2. Search project memory: `a pattern search(query: "<keywords>")` - check for existing patterns
3. Check if the insight already exists - **update rather than duplicate**
4. Check existing skills in `.claude/skills/` for overlap
5. Check CLAUDE.md files for existing rules

### Step 4: Persist Insights

For **project-specific lessons** (the Step 2a default):
- Append one imperative bullet to a `## Project Lessons` section in the project's own CLAUDE.md (`the project's own CLAUDE.md`). Create the section if absent. This file is what `/pickup` reads, so the lesson returns next session - no root write needed.
- If the project has a `memory/decisions.md` (agentic-workflow skeleton), append durable decisions there too (append-only, dated).
- Do NOT also write these to root memory or root CLAUDE.md - that is the bloat this routing exists to prevent.

For **skills** (reusable workflows):
- Create/update `SKILL.md` in `.claude/skills/<skill-name>/`
- Include concrete steps, not vague guidance

For **memory updates** (file-based only):
- Create/update topic file in memory dir with proper frontmatter (name, description, type)
- Add one-line entry to MEMORY.md under the appropriate section
- Keep MEMORY.md under 200 lines - if approaching limit, consolidate

For **CLAUDE.md rules**:
- Append to appropriate section, imperative tone, one bullet per rule

For **project memory patterns** (via MCP tools):
- Use `the pattern store` for each reusable success, failure, or pitfall
- Categories: `deployment`, `testing`, `api`, `delivery`, `integrations`, `supabase`, `expo`, `firebase`, `vercel`
- Check with `a pattern search` first; use `reinforce the existing pattern` if similar exists

### Step 5: Feedback Graduation Check

Review feedback files older than 14 days. For each:

1. **Read** the feedback file content
2. **Check** if the rule already exists word-for-word in `~/.claude/CLAUDE.md`
3. If YES (already in CLAUDE.md): **delete the feedback file** and remove from MEMORY.md
4. If rule is universal and proven (applied 2+ times): **promote to CLAUDE.md**, then delete feedback file
5. If still context-specific or too fresh: leave in place

Run this check:
```
find memory/ -name "feedback_*.md" -mtime +14 | while read f; do echo "$f"; done
```

For each candidate, verify against CLAUDE.md before deleting. This prevents unbounded feedback file growth.

### Step 6: Project Lifecycle Check

Review project files for staleness:

| Status | Action |
|--------|--------|
| **Active** (work in last 2 weeks) | Keep full file + MEMORY.md link |
| **Complete/shipped** | Keep file for reference, one-line MEMORY.md entry |
| **Dead/scrapped** (no activity 4+ weeks, explicitly abandoned) | Delete file, remove from MEMORY.md |
| **Paused** (explicitly paused, may resume) | Keep file, mark as PAUSED in MEMORY.md |

Check recent git history for the project directory and cross-reference it with project memory status fields.

For dead projects: verify lessons are captured in feedback files or CLAUDE.md before deleting.

### Step 7: Report

Output:

```
Session Retrospective Complete

Insights extracted: N
- Project lessons -> project CLAUDE.md / memory/decisions.md: [list]  (project-specific)
- Skills created/updated: [list]
- Memory entries added: [list]  (file-based only, cross-cutting)
- CLAUDE.md rules added: [list]  (root, cross-cutting)
- project memory patterns stored: [count] (success: N, pitfall: N, failure: N)
- Skipped (one-off): [count]

Feedback graduation:
- Promoted to CLAUDE.md: [list]
- Deleted (already in CLAUDE.md): [list]
- Kept (still fresh/specific): [count]

Project lifecycle:
- Active: [count]
- Flagged for cleanup: [list]

MEMORY.md: [line count]/200 lines
```

## Quality Gates

Before persisting any insight, verify:
- [ ] Applies to future sessions (not just this one)
- [ ] Doesn't duplicate an existing rule or memory
- [ ] Specific enough to be actionable
- [ ] General enough to be reusable

## Arguments

- No arguments: full retro (default)
- `ARGUMENTS`: Optional focus area (e.g., "retro testing" or "retro pipeline")
