---
name: handover
description: Write a concise, evidence-backed session handover for another agent. Use when the user asks for a handover, continuity note, resume packet, or current-state record.
---

# Handover

1. Read the current conversation state and inspect `git status --short --branch` plus `git diff --stat`.
2. Update the target `PROJECT.md` last-session section only when verified product state changed.
3. Write or append `.codex/sessions/YYYY-MM-DD-handover.md`.
4. Include topic, date, branch, working directory, goal, decisions, completed and partial work, uncommitted changes, commands and evidence, unresolved risks, next actions, and key files.
5. Keep the note concise enough for a fresh agent to act without replaying the transcript.

Never auto-commit, push, include secrets, or present compiled output as end-to-end verification.
