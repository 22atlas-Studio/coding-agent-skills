---
name: write-tech-spec
description: Write a code-grounded technical implementation spec (tech.md) for a single ticket or feature. Use when user says "write a tech spec", "spec out this issue", "TECH.md", "implementation spec", or when handing a ticket to an implementing agent (a coding agent, a worker, a subagent). Output is a single Markdown file with 8 fixed sections, dense file:line refs, and concrete code snippets - modeled on Warp's Oz `specs/APP-N/TECH.md` format.
---

# Write Tech Spec

Produce a single `tech.md` for a known issue or feature, in a fixed 8-section format. The output is the brief that an implementing agent (or human) reads end-to-end and ships from. **Code-grounded, not waffly** - every claim about current behavior cites a `file.ext:line[-line]` reference, every proposed change includes a concrete code snippet.

## When to use

- Spec'ing out an issue that already has a product-level description (PRD, GitHub issue body, Linear ticket, brief)
- Handing a piece of work to an implementing agent and you want one document that contains everything it needs
- Translating a vague "we should do X" into a reviewable plan before any code is written
- Producing the `tech.md` half of a `specs/<ID>/{product.md,tech.md}` pair

## When NOT to use

- The work is multi-phase and needs vertical-slice planning across phases - use `prd-to-plan` first, then write a tech spec per phase.
- The product-level scope isn't agreed yet - use `write-a-prd` first.
- You only need a checklist of tickets - use `prd-to-issues` instead.

## Inputs

Before starting, the conversation must contain (or you must locate):

1. **An identifier** - `APP-1234`, `SH-007`, GH issue number, Linear key. Used in the spec title and the output path.
2. **A problem statement** - what's broken or missing. From a PRD, ticket body, or user message.
3. **The codebase** - read it. Don't speculate on what files exist.

If any of the three is missing, ask the user once for the missing piece before proceeding.

## Process

### 1. Read the codebase before writing

Locate every file relevant to the change. For each, note the precise line range that implements the current behavior. **Do not write the spec from memory or from filenames alone** - open the files and confirm the lines match the claim you're about to make.

Aim for 3-8 file:line citations in the "Relevant code" section. Fewer than 3 usually means insufficient exploration; more than 8 usually means the spec covers too much and should be split.

### 2. Trace the end-to-end flow

Walk through what happens today, step by step, from the user action that triggers the bug/missing-feature to the final state. Then walk through what *will* happen after the change. Both walkthroughs go in the spec.

### 3. Draft proposed changes as numbered subsections

Each numbered change must include:
- A one-line statement of what changes
- A code snippet showing the new shape (signature, structure, or 3-10 lines of body - not the full file)
- The file path it goes in

Group related changes under one number. Don't pad the list to look thorough.

### 4. List risks, mitigations, and follow-ups honestly

Risks the implementer needs to handle (concurrent state, feature-flag interactions, migration ordering, regression surfaces). Don't invent risks to look thorough; don't omit known ones to look clean. Each risk gets a one-line mitigation.

Follow-ups are work that's *out of scope for this spec* but should not be lost. Cleanup, hardening, or related improvements that surface during the design.

### 5. Write the file

Output goes to one of these paths, in priority order:

1. If user specified a path → use that.
2. If working in a product with a `specs/` directory (for example `products/<name>/specs/`) → `specs/<ID>/tech.md`.
3. If working in a product with `docs/specs/` → `docs/specs/<ID>/tech.md`.
4. Otherwise → `./tech-<ID>.md` in the current working directory.

The filename is always lowercase `tech.md` (Warp uses `TECH.md`; pick one case per repository and keep it).

### 6. Verify before declaring done

After writing, re-read the file once and check:
- Every file:line reference resolves (the file exists, the lines contain what the spec claims).
- Every code snippet is syntactically valid for the language.
- The end-to-end flow names real functions/types from the codebase, not invented ones.

## Template

Use this exact structure. Section names and order are fixed. Drop a section by leaving it as `_None._` rather than removing it - readers expect the same shape every time.

<tech-spec-template>
# Tech Spec: <one-line summary>

**Issue:** `<ID>`
**Product spec:** [`./product.md`](./product.md) <!-- or link to the PRD/ticket -->

## Problem

What's broken, missing, or wrong today. 2-6 sentences, concrete. Name the user-visible symptom or the structural deficiency, not the desired solution.

## Relevant code

- `path/to/file.ext:LINE-LINE` - one-line description of what this code does today
- `path/to/other.ext:LINE` - ...
- (3-8 entries; group related lines into one entry with a range)

## Current state

Walk through the existing behavior end-to-end. Reference the file:line entries above. Be precise about what data flows where and which branches are taken. If a feature flag, env var, or config controls behavior, name it.

This section explains the system as a reader would observe it today. No proposals yet.

## Proposed changes

### 1. <Short title for the change>

What changes, in one sentence. Then a code snippet showing the new shape - signature, struct, or 3-10 lines of body. Reference the file path the change lives in.

```language
// path/to/file.ext
fn new_or_modified_function(arg: Type) -> ReturnType {
    // ...
}
```

### 2. <Next change>

...

<!-- Repeat as needed. Group related edits under one number; don't pad. -->

## End-to-end flow

Numbered walkthrough of what happens *after* the change ships, from the triggering action to the final state. Reference real types and functions named above (or in the proposed changes). 5-10 steps is typical.

1. User action / event triggers ...
2. ...
3. ...

## Risks and mitigations

- **<Risk name>**: one-sentence description of the risk. **Mitigation:** one-sentence plan.
- **<Risk name>**: ...

If a section of the system might regress, name it. If a migration must run before/after a deploy, say so. If concurrent writes or feature-flag interactions matter, call them out.

If there are genuinely no risks, write `_No material risks identified._` - don't invent filler.

## Testing and validation

How the change is verified before merge. Mix of:

- **Unit tests** - what new or changed test files cover (path + behavior tested)
- **Integration / manual checks** - what to click through, what to observe
- **Regression watch** - what existing test suites must stay green

Keep this concrete. "Test the happy path and edge cases" is not a test plan; "Add `tests/foo.test.ts: handles concurrent claims via SKIP LOCKED` and verify against the existing `gateway-poller.test.ts` suite" is.

## Follow-ups

Work that's *out of scope* for this spec but should not be lost:

- ...
- ...

Or `_None._` if the spec is genuinely self-contained.
</tech-spec-template>

## Quality bar (red flags during review)

These mean the spec needs another pass before handing it off:

| Red flag | Fix |
|---|---|
| "Relevant code" has filenames but no line numbers | Open the files; cite ranges. |
| Proposed changes describe *what to do* in prose without code | Add the snippet. |
| End-to-end flow uses verbs like "handles" or "processes" without naming the function | Name it. |
| Risks section is `_No material risks._` on a non-trivial change | You haven't thought hard enough - re-read the proposed changes. |
| Spec covers more than one logical change | Split into two specs with separate IDs. |
| Total length under 1KB | Probably under-spec'd. Real specs are usually 3-10KB. |
| Total length over 20KB | Probably over-scoped. Split. |

## Why this format (background)

Adopted from Warp's Oz `specs/APP-N/TECH.md` convention (github.com/warpdotdev/warp). The 8 fixed sections force the writer to do code-reading work *before* the implementing agent does, instead of leaving discovery work scattered across PR comments. Sample reference: `specs/APP-3904/TECH.md` in the Warp repo.

The dual-doc pattern (`product.md` + `tech.md`) (for example `specs/SH-001/`) aligns with this - `product.md` is the *what/why*, `tech.md` is the *how* this skill produces.
