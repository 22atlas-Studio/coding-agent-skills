---
name: typescript-gotchas
description: "TypeScript gotchas: tsc verification, Vitest over Jest, package refs, ESM imports, test-double export surfaces, and the optional-prop built-but-not-wired trap. Invoke before writing or reviewing TypeScript."
---

# typescript-gotchas

Migrated out of the always-loaded guidance on 2026-08-15 so it loads only when the work calls for it.

- `tsc --noEmit` to verify compilation before marking complete
- prefer simpler type patterns; if generics cause errors, simplify
- explicit return types for functions returning external package types
- testing: Vitest (not Jest)
- timing tests: 10ms+ async delays for short TTL expiration tests
- package refs: `file:../path` (not `workspace:*`) for npm compatibility
- `simple-git` ESM: `import { simpleGit } from 'simple-git'` (named export) - default fails in NodeNext
- a test double must mirror the REAL module's export surface, not the subset the current (buggy) code happens to call: a mock defining only `getPublicUrl` pinned the test to the broken helper and made it FAIL when the screen was corrected (2026-07-28)
- an optional prop behind a null guard fails SILENTLY at every call site that forgets it, and a component test that SUPPLIES the prop cannot catch it - assert at the call sites, or make the prop required (2026-07-27). RECURRED TWICE IN ONE WINDOW (2026-08-11/12): a flag shipped with NO production call site passing it, so the user-visible half of the change was dead code its own 3 passing tests could not see (caught by a design review, not the suite); and a display field shipped inert the next day for the same reason (caught by codex). THE GENERAL SHAPE IS "BUILT BUT NOT WIRED", and a test that supplies the input is structurally blind to it. MECHANICAL REMEDY: in the SAME commit that adds an optional input, either make it required or add a call-site assertion (a containment spec that reads the production sources and asserts at least one caller passes it, with a non-empty-sweep guard so a zero-match sweep cannot pass vacuously).
- Node 22 `node --test test/` treats the directory as a module path (MODULE_NOT_FOUND reported as ONE failing test): pass a glob, `node --test test/*.test.js` (a Node service, 2026-10-18).
- `net.BlockList` checks an IPv4 address against IPv6 rules in IPv4-mapped form, so `::ffff:0:0/96` in the same list blocks ALL of IPv4 (8.8.8.8 reported private): keep separate v4 and v6 lists. For an SSRF guard, validate inside the `lookup` option of `http(s).request` so the checked address is the connected one (no DNS-rebinding window), and check IP-literal hostnames yourself because Node skips `lookup` for them (the request helper, test "private range coverage", 2026-10-19).
- A `busy = (async () => { ... finally { busy = null } })()` single-flight guard JAMS FOREVER when a run awaits nothing: the async body runs synchronously to completion, so `finally` clears `busy` BEFORE the assignment stores the already-settled promise, and every later call returns that stale promise and does no work. Assign first, clear after: `if (!busy) busy = run().finally(() => { busy = null; })`. Caught only because the new test went red on its first run (a delivery queue, 2026-10-20).
- A perturbation sweep that shells out to the test runner needs a per-case timeout (`subprocess.run(..., timeout=120)`): removing a loop's exit condition (for example "drop the queue row on success") turns the suite into an infinite loop, and without a timeout the sweep stalls until the hung child is killed by PID. A timeout counts as red (2026-10-20).
