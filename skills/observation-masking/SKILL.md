---
name: observation-masking
description: >
  Manage context window bloat from large tool outputs during long sessions.
  Auto-activates when: tool output exceeds ~2k tokens, session has 10+ turns,
  context feels sluggish or repetitive, working with large files/logs/API responses,
  or agent starts "forgetting" earlier decisions. Use when asked to "reduce context",
  "offload output", "save context space", or when verbose tool results accumulate.
---

# Observation Masking

Replace verbose tool outputs with compact references. Full content goes to files; context keeps only what matters for the next decision.

## Why

Tool outputs (file reads, search results, command output) reach 80%+ of context tokens. Once used for a decision, keeping full output provides diminishing value while crowding out newer information.

## Decision Table

| Mask | Don't Mask |
|------|------------|
| Tool output from 3+ turns ago | Output actively being reasoned about |
| Verbose logs/dumps already summarized | Error messages still being debugged |
| Search results after picking the relevant hit | Most recent tool output |
| File reads after extracting the needed section | Output referenced by current plan |
| API responses after parsing key fields | System prompt / tool definitions |

## Techniques

### Large command output (tests, builds, logs)

When output exceeds ~50 lines, write to scratch file and summarize inline:

```
# Write full output
Write(.claude/sessions/scratch-test-run-1.md, full_output)

# Continue with summary only
"14 passed, 2 failed. Failures: test_auth_token (line 42, assertion error on expiry), test_db_pool (timeout). Full output: .claude/sessions/scratch-test-run-1.md"
```

### Informational file reads (not being edited)

After reading a large file to understand structure - note key findings, don't re-read. For revisits, use Grep or Read with line range instead of full file.

### Search results (Grep/Glob)

Record relevant file paths + line numbers. Navigate directly for subsequent work. Don't carry the full result set forward.

### API responses / scraped content

Write raw to `.firecrawl/` or `.claude/sessions/`. Extract only needed fields. Use `jq`, Grep, or Read with offset for later access.

### Sub-agent isolation

Heavy retrieval tasks (exploring unfamiliar code, bulk searches) - delegate to Task tool sub-agents. They run in isolated context and return only the summary. Parent context stays clean.

## Scratch File Convention

```
.claude/sessions/scratch-{topic}-{n}.md
```

Examples: `scratch-grep-results-1.md`, `scratch-api-response-1.md`, `scratch-test-output-1.md`

## Compaction Checkpoint

At natural breakpoints (subtask done, switching files, changing approach):

1. Which tool outputs am I still actively using?
2. For inactive outputs - information is either captured in code/decisions already written, or retrievable from scratch file
3. Mask before running `/compact` to preserve higher-quality summaries

## Integration

- **Session files**: `.claude/sessions/YYYY-MM-DD-topic.tmp` - scratch files live alongside these
- **Sub-agents**: Task tool naturally isolates context; prefer for heavy retrieval
- **/compact**: Mask first, then compact - better signal-to-noise in the summary
