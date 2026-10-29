---
name: python-backend-gotchas
description: "Python and backend service patterns for Python services: uv environments, Pydantic v2 stages, Typer CLIs, FastAPI lifespan and CORS, httpx/respx mocking, Stripe Checkout and webhook handling, dotenv load ordering. Load before writing Python, FastAPI, Pydantic, Typer, Stripe, or pipeline-stage code."
user_invocable: false
---

# Python & Backend

Extracted from the global CLAUDE.md on 2026-07-26 as part of the
Claude 5 progressive-disclosure prune. These are gotchas, not conventions.

- Python environments: always `uv` (never pip directly)
- Pydantic v2 for pipeline data + config validation
- pipeline stages as classes with `run()` methods returning `{ success, data, errors }` dicts
- Python adapters: `typing.Protocol` + `@runtime_checkable`
- Python CLIs: Typer + Rich for type-hinted CLI with styled output; flat module layout (no src/)
- prompts in `config/prompts/` YAML files
- local dev: SQLite (`aiosqlite`) for testing when PostgreSQL not required
- composable pipelines: optional override params (`Type | None = None`) for backwards-compatible orchestration
- optional integrations: `try/except ImportError` + graceful failure for all plugin modules
- FastAPI startup validation: `@asynccontextmanager async def lifespan(app)` + `app = FastAPI(lifespan=lifespan)` - fail fast on missing env BEFORE serving requests
- FastAPI CORS: `allow_origins=["*"]` + `allow_credentials=True` is invalid - browsers reject; use explicit domain list when credentials=True
- httpx mocking in pytest: `respx` library - `respx.mock` + `respx.post(url).mock(return_value=httpx.Response(200, json={...}))`
- Stripe webhooks: set `stripe.api_key` lazily inside each handler (not module-level); HTTP 500 on `list_line_items` failure so Stripe retries; use `Session.list_line_items(session_id, limit=1)` for price_id
- Stripe Checkout Sessions over Payment Links for programmatic one-off charges: reuses the existing `checkout.session.completed` webhook path, supports inline `price_data` (no pre-created Price object) and `expires_at`; a Payment Link needs a Price per request
- Stripe Checkout session lifetime has a ~31-min MINIMUM (`expires_at` can't be shorter): for a pay-after-expiry flow use a bounded grace window (`LATE_*_GRACE_MIN`, e.g. 45) and past-grace goes to ops reconciliation - NEVER auto-confirm/fulfil on a payment that lands after the intended window
- audioop removed from Python 3.13 stdlib: add `audioop-lts>=0.2.2` (identical API)
- CLI `load_dotenv`: call at TOP of `cli.py` BEFORE any package imports - module-level `os.environ.get()` in sub-modules freezes at import time
- webhook query params: `urllib.parse.urlencode()` - never f-string concat when values may contain spaces/special chars
- Pydantic enum + SQLite: any string written and read back through a `str Enum` field raises ValueError if not in enum - keep enum and write paths in sync
- provisioning API keys: generate once at task start, pass through entire flow - never re-derive from a different ID at different stages
- seeded data generators: put display-only draws on a SEPARATE rng stream and satisfy any graded/oracle-dependent scenario in a deterministic ANCHOR stage - a single added draw in the main sequence cascades into every downstream distribution and flaps unrelated threshold tests (happened 3x in one round, example-app 2026-07-23)
- fixing generated-data incoherence: permute the EXISTING value multiset, and swap whole BUNDLES (price + rent + tax together) not single fields - distribution stats and cross-field ratios then hold by construction with zero new draws (175 inversion pairs -> 0, every stat preserved). PERMUTE ONLY WITHIN THE SEGMENT THE VALUE BELONGS TO (same building, same neighborhood, same tier): a cross-segment permutation preserves every GLOBAL stat and still passes its own monotonicity test while relocating a cheap-neighborhood price onto an expensive-neighborhood home - my 'fix' shipped that and only a screenshot caught it (example-app 2026-07-24). When a stage REWRITES a driver field (sqft, beds), scale the dependent field by the same ratio instead of reshuffling: that preserves each row's own rate, which is the realism a grader actually reads. And assert the honest invariant (per-segment rate band), not a global ordering - across neighborhoods a larger home genuinely costs less.
- when a DB is a DERIVED artifact of a pipeline: reseed = full-column refresh on conflict + PRUNE rows absent from the source JSON - an insert-only reseed leaves stale rows and id collisions (2 codex P2s, example-app 2026-07-23)
- local OAuth/webhook callback listeners: loop until code-or-deadline with a SHORT per-call timeout (a stray favicon eats a single-shot `handle_request()`), a ~30-min window (not 300s - a human has to click), and `flush=True` on every print (non-TTY logs swallow the consent URL otherwise). Regression-test by firing a stray request BEFORE the real redirect.
- a FORWARDED-email test corpus is not a real inbox: forwarding strips delivery-time labels (`category:purchases` lands in Primary) and rewrites the sender (a domain allowlist sees the forwarder, not the retailer), so it structurally under-reports yield - separate discovery misses from extraction misses in every test or you will chase phantom parser bugs
- gates: run the PROJECT's configured invocation (`nx run frontend:lint`, project venv/config), NEVER a bare tool run (`uvx ruff check`, `npx eslint src`) - bare invocations resolve their own defaults instead of the repo's rule selection/project graph, in BOTH directions: a bare run missed a real E501 codex caught (2026-07-11) and a bare `npx eslint src` returned exit 1 while the real gate was clean (2026-07-23). Re-run the real gate before believing a red from a bare invocation.
- scrub exception messages from keyed/authenticated HTTP calls (urllib etc. embed the full keyed URL in error strings): log/raise status code + exception type only
