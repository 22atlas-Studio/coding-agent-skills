# Contract reference

The machine output `latest.json` is shaped so a downstream gate can validate the `findings` array with no translation. A single finding object is a `RawFinding`:

```json
{
  "severity": "critical | high | medium | low",
  "confidence": "low | medium | high",
  "category": "<short kebab/snake label, e.g. hardcoded-secret>",
  "file": "app/services/auth.ts",
  "start_line": 42,
  "end_line": 42,
  "description": "<one sentence problem statement>",
  "suggestion": "<smallest correct fix direction, or null>"
}
```

Severity vocabulary is lowercase `critical|high|medium|low` everywhere (JSON and report). Reviewer partials still emit `P0-P3`; the agent maps `P0->critical, P1->high, P2->medium, P3->low` during synthesis (per `../../plugins/code-audit/shared/severity-map.md`).

`latest.json` envelope:

```json
{
  "verdict": "PASS | PASS_WITH_WARNINGS | FAIL",
  "scanned_at": "2026-05-27T18:00:00Z",
  "base_sha": null,
  "codex": false,
  "counts": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "findings": [ /* RawFinding[] */ ]
}
```

Default threshold: `FAIL` when `counts.critical > 0 || counts.high > 0`; else `PASS_WITH_WARNINGS` when any finding exists; else `PASS`. `FAIL` is the no-go result for a downstream gate.
