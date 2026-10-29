# Goal: Dealer accepts customer offer

## Context
- App: example-app
- Persona: dealer (logged in as operator@example.test)
- Entry route: /dealer/deals/42

## Definition of Done
Dealer sees incoming customer offer on the deal page, clicks Accept,
deal status flips from OFFER_PENDING to ACCEPTED, the badge updates
without a hard reload, POST /api/notifications fires once, and zero
console errors appear in the page lifecycle.

## Regression checks (these have failed before and must not fail now)
- Accept button is not stuck disabled when offer is pending (bug from run 2026-04-28-1430)
- Status badge updates without a full page reload (bug from run 2026-05-03-1100)

## Do not change
Don't navigate away from this deal. Don't touch other deals.
Don't modify dealer profile settings.

## Response format

On every iteration, write to `state.yaml`:

```yaml
iteration: <n>
current_step: <one-line description>
evidence_captured: [<screenshot paths>, <network capture paths>]
blocking_observations: [<things preventing progress>]
candidate_verdict: PASS | BUG | BLOCKED-AUTH | BLOCKED-DEPENDENCY | BLOCKED-DEV-SERVER | INSPECT | NOT_YET
```

Mark the goal achieved ONLY when the audit shows the Definition of Done
has actually been met. Do not accept proxy signals (URL changed, button
was clicked) as completion. If you observe a bug, set
candidate_verdict=BUG and stop - don't try to fix it. If you cannot
proceed, set candidate_verdict=BLOCKED-* with a one-line reason.

When you set a final verdict, write `findings.json` next to `state.yaml`
following the schema in `qa-walk/helpers/findings_schema.py`.
