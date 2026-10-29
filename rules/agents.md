# Agent Delegation Rules

## When to Delegate
- Task requires specialized focus (security audit, performance analysis)
- Non-overlapping parallel work possible (multiple file reviews)
- Task needs limited tool scope (read-only analysis)
- Deep exploration of specific area (research into one module)

## When NOT to Delegate
- Single file edits, simple bug fixes, config changes
- Tasks you can complete in <3 tool calls
- Pure Q&A or conversational responses

## Delegation Rules
- Pass objective context (why, not just what)
- Each agent: one clear input, one clear output
- Evaluate every sub-agent return before accepting
- Max 3 follow-up cycles per sub-agent to prevent loops
- Store intermediate outputs in files, not just memory
- Avoid overlapping file edits from parallel agents
- Consolidate results before presenting to user

## Model Selection
- **Haiku**: File creation from exact spec (migrations, stores, hooks), no reading required
- **Sonnet**: 90% of tasks - read existing files + write new ones, UI screens, modifications
- **Opus**: Scaffolding (project init, layout, auth), architectural decisions, 5+ file coordination
- **Pattern (validated)**: For admin panels or multi-page apps, use opus for scaffold then 3 parallel sonnet agents for page groups by route directory

## Advisor Mode (Opus plans, Sonnet executes)
- For medium-complexity tasks, use **Opus as planner + Sonnet as executor in a single Agent call**: main agent drafts the plan, delegates execution to a Sonnet subagent with the full plan as its prompt
- Saves ~12% tokens per task vs pure-Opus, preserves plan quality
- Apply when: (a) plan fits in one message, (b) execution is mechanical (edits to known files), (c) task needs Opus judgment at the top but not mid-execution
- Skip when: plan requires iterative exploration, or execution hits unexpected branches

## Coordination Patterns (choose simplest that works)
Anthropic's multi-agent coordination patterns, ordered by coupling:
1. **Independent parallel** - agents share nothing, fan out/fan in. Default choice.
2. **Shared read-only context** - all agents read the same brief, outputs independent.
3. **Pipeline / handoff** - agent A's output is agent B's input, sequential.
4. **Shared mutable state** - coordinated writes to a blackboard (TASKS.md, Linear).
5. **Full peer-to-peer** - agents negotiate live. Avoid unless mandatory.
Start at 1; only escalate when the simpler pattern demonstrably fails. Sophistication backfires.

## Single-Agent Default
- When compute is normalized, a single agent with good scaffolding usually beats a multi-agent swarm
- Default to single-agent unless parallelism is mandatory (independent work, strict time budget)
- "Start simple" applies here: multi-agent orchestration adds coordination overhead that often exceeds its gains

## SDK vs Deterministic Code
- **MAPPING** (structured → structured): Use templates, AST transforms, code generators
- **JUDGMENT** (natural language → code): Use Agent SDK with constraints

## Git Commit Discipline
- Keep commits atomic: commit only the files you touched and list each path explicitly
- For tracked files: `git commit -m "<scoped message>" -- path/to/file1 path/to/file2`
- For brand-new files: `git restore --staged :/ && git add "path/to/file1" "path/to/file2" && git commit -m "<scoped message>" -- path/to/file1 path/to/file2`

## Anti-Patterns
- Don't use swarms for simple Q&A
- Don't use a single agent for 10+ file refactors (use parallel agents)
- Don't build custom orchestration when the harness already has a task tool
- Don't over-delegate - simple tasks don't need agents

## Workflow Cost Discipline (enforced by pre-tool-workflow-budget.sh)

The Workflow tool fan-out can spend millions of tokens fast (real incident 2026-06-01: 33 agents, 2.55M tokens for an audit + one design doc, because the fan-out defaulted to inherited Opus and a per-finding verify layer multiplied). Rules:
- TIER MODELS in any fan-out: `model:'sonnet'` (or `'haiku'`) for readers/verifiers/extractors; reserve Opus (omit model) for a single final synthesis/judgment agent. Never let a parallel()/pipeline() fan-out inherit Opus across the board. The PreToolUse hook BLOCKS this exact pattern (escape hatch: `WF_BUDGET_OK:<reason>` in the script).
- COUNT THE REAL FAN-OUT before launching: a per-item secondary layer (verify-per-finding) multiplies (items x children), not adds. Cap secondary fan-out (e.g. verify only high/medium severity).
- ANNOUNCE the estimated agent count to the user BEFORE launching when it exceeds ~8 - honestly, not after.
- DEFAULT TO DIRECT WORK: for most tasks a single well-scoped agent or just working inline beats orchestration. Reach for Workflow only when parallelism is genuinely mandatory.
