"""Translate gitignore-ish globs (with ** support) to compiled regexes.

Used to honor `paths` / `exclude_paths` in security-patterns.json against
POSIX-style repo-relative file paths. Stdlib only.
"""
from __future__ import annotations

import re
from re import Pattern


def glob_to_regex(glob: str) -> Pattern[str]:
    """Compile one glob to an anchored regex.

    Rules:
      - `**`  matches any number of path segments (including zero), i.e. `.*`
      - `*`   matches within a single segment, i.e. `[^/]*`
      - `?`   matches a single non-slash char
      - everything else is matched literally
    """
    i = 0
    out = ["^"]
    n = len(glob)
    while i < n:
        c = glob[i]
        if c == "*":
            if i + 1 < n and glob[i + 1] == "*":
                out.append(".*")
                i += 2
                # swallow a trailing slash after ** so "**/app" matches "app"
                if i < n and glob[i] == "/":
                    i += 1
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    out.append("$")
    return re.compile("".join(out))


def path_matches_any(path: str, globs: list[str]) -> bool:
    """True if `path` matches at least one glob. Empty list -> False."""
    return any(glob_to_regex(g).match(path) for g in globs)
