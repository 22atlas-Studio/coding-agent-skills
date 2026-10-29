# Ring 0 laws

Generic form of the ten standing laws. Laws 4, 7 and 8 are nudges: remind, do not block. The others are blocks. A hook that cannot see the output yet is a reminder after the fact, not a gate.

1. Never write an em dash (U+2014) or an en dash (U+2013) in any output: code, comments, docs, commits, chat, or filenames. Use `-` or `:`. When scanning JSON, also match the escaped form of those two code points.
2. Never append a `Co-Authored-By` or similar attribution trailer to a git commit.
3. Never print a `.env` or other secret file with `tail`, `cat`, `head`, or an equivalent. Confirm one variable with `grep -c '^VAR=' .env` (a plain grep prints the value) and count lines with `wc -l`. Never echo secret values.
4. Nudge, not a block: no dollar figures, pricing, or internal business data in commits, pull requests, status updates, or anything a client reads.
5. "Verified" means the real behavior was exercised end to end against the real artifact (real service, fresh account, real payload). Booting, compiling, a green suite, or "looks right" are proxies. A test built on a fixture you invented from your own assumptions about an external format is not verification.
6. Confirm the exact target before any destructive or hard-to-reverse action: deletes, force push, history rewrites, dropping data, or sending or removing messages other people read.
7. Nudge, not a block: write every commit as if a hostile reviewer reads it. Conventional Commits, factual, no narrative, no internal pricing or business data.
8. Nudge, not a block: do not push a private monorepo to a downstream repository. Deliver only the intended project, from that project's own checkout, after checking its remote.
9. Decide, do not ask, when intent is clear: one recommendation with its reasoning, not a menu. Offer options only when asked, or when a bare command is actually a question about the command.
10. Cross-verify any claim about outward state (deployed, pushed, merged, DNS live, a resource exists) with a fresh read of that state before reporting it.
