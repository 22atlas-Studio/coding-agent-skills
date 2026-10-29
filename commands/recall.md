---
description: Search project memory and patterns. Usage: /recall <query>
---

# Recall

Quick search across project memory, patterns, and sessions.

## Instructions

Given the user's query (passed as `$ARGUMENTS`):

1. **Search in parallel**  -  run all three searches simultaneously:
   - `a memory search(query: "$ARGUMENTS")`  -  stored knowledge
   - `a pattern search(query: "$ARGUMENTS")`  -  learned patterns (successes/failures/pitfalls)
   - `a recent-session list(limit: 5)`  -  check if there's a recent session snapshot related to the query

2. **Present results concisely**  -  group by source:
   ```
   ## Memory
   - [key]: [value summary] (namespace: [ns])

   ## Patterns
   - [outcome] [pattern summary] (category: [cat], seen: [N]x)

   ## Related Sessions
   - [name] ([date])
   ```

3. If no results from any source, say so and suggest checking:
   - MEMORY.md files: `~/.claude/projects/<project>/memory/`
   - Handover files: `.claude/sessions/`
   - Git log: `git log --oneline --grep="$ARGUMENTS"`

## Arguments

- `$ARGUMENTS`: Search query (required). Examples:
  - `/recall supabase deploy`  -  find supabase deployment patterns
  - `/recall deploy`  -  find notes about a deploy
  - `/recall gmail mcp`  -  find pitfalls about Gmail MCP integration
