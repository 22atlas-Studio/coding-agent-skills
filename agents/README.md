# Reviewer prompts

These files are prompt text, loaded by path. They have no agent frontmatter on purpose: adding `name:` would register them as subagents and change how the review skills behave.

They are read-only. Bash, when a prompt allows it, is for inspection only.

The fan-out prompts in `reviewers/` are the read-only reviewers shipped in this repository. Do not invent extra reviewer subagents for prompts that are not here.

Laws 4, 7 and 8 in `code-reviewer.md` and `mobile-code-reviewer.md` are nudges. Do not treat them as blocks. The blocking laws are the dash glyph, attribution trailers, and printing secret files.
