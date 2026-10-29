---
name: recall
description: Search the private repo semantic memory, curated Claude evidence, session handovers, and repository history for prior context. Use when the user says recall, asks what happened before, or needs prior decisions and patterns with citations.
---

# Recall

Search in this order:

1. Current Ring 0 and Ring 1 repository documentation.
2. project memory and patterns when available.
3. The curated Claude project memory and relevant `.claude/sessions/` handovers.
4. `.codex/sessions/` and targeted Git history.
5. Obsidian only when project context is missing from repository evidence.

Return brief sections for memory, patterns, related sessions, and conflicts. Cite file paths or memory record identifiers. Treat recalled material as possibly stale and verify drift-prone facts before acting.
