# Security Rules (resident)

High-stakes, non-obvious security rules that must be in context BEFORE code is
written. The generic remainder (secrets hygiene, input validation, injection,
auth basics, data protection, dependency audits) lives in the `security-rules`
skill - it is the 'obvious' the Claude 5 guidance says not to state resident.

## IDOR Prevention (Supabase)
- Service-role Supabase clients bypass RLS - NEVER trust entity IDs from user input without ownership verification
- Every edge function that accepts an entity ID (conversation_id, note_id, etc.) MUST verify `entity.user_id === user.id` before any read/write
- When using service-role client alongside RLS, treat every DB query as if RLS does not exist - add explicit WHERE user_id clauses
- Email/notification endpoints must restrict recipients to the authenticated user's own verified address - never allow arbitrary `to` fields

## CI/CD (GitHub Actions)
- **NEVER use `pull_request_target` workflows.** This trigger runs in the context of the base repo with full repo secrets, but checks out PR code from the fork - a classic exfiltration vector. Attackers submit a PR that modifies the workflow itself (or any script it calls) and the workflow runs with secrets attached. Use `pull_request` instead (no secrets by default), and gate any privileged actions on `if: github.event.pull_request.head.repo.full_name == github.repository`. If you need a label-based moderation flow, use a separate `workflow_run` workflow that triggers on the completion of an untrusted `pull_request` workflow - it gets secrets but never reads PR-controlled content.
- **NEVER use shared caches in a publish/deploy pipeline.** Cache poisoning is a known attack class: an attacker pollutes a build cache from a PR (or any untrusted branch), then the publish workflow restores that cache and ships the poisoned artifact. Publish jobs must (a) skip `actions/cache` entirely, or (b) use a key namespace scoped to `${{ github.ref }}` AND restricted to trusted refs (main/master/release tags), AND verify checksums of restored artifacts before use. Never share a cache key between a `pull_request`-triggered job and a publish/release job.
- Corollary: keep CI and publish workflows in **separate files** so triggers and caches can't leak across them. Don't conditionally branch a single workflow into "is this a publish run?" - that's how shared caches happen.
