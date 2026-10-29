#!/usr/bin/env bash
# PreToolUse hook: Enforce command-level Ring 0 laws on Bash tool calls.
# Law #3: Never tail/cat/head a .env or secret file (transcript leak).
# Laws 4, 7 and 8: nudge on a git push to a remote other than origin.
# These are reminders, not blocks. Exit 0 either way.
#
# Exit 0 = allow (stderr is shown as non-blocking note).
# Exit 2 = block; Claude must choose a different command.
# FAIL OPEN: any internal error -> exit 0.
#
# Additive alongside pre-tool-git-safety.sh -- does not duplicate its patterns.

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

# Fail open: could not extract command
if [ -z "$COMMAND" ]; then
    exit 0
fi

# --- Law #3: block tail/cat/head on .env files ---
# Match: word boundary (tail|cat|head) anywhere in command + path containing .env
# This catches: `tail -20 .env`, `cat /path/to/.env`, `head .env.local`, etc.
if echo "$COMMAND" | grep -qP '\b(tail|cat|head)\b' && \
   echo "$COMMAND" | grep -qP '\.env'; then
    echo "Law #3 blocked: never tail/cat/head a .env or secret file -- it leaks secrets into the transcript.
Use: grep -c '^VAR=' .env    (confirm one variable without printing it)
     wc -l .env              (count lines without reading content)
Command was: $COMMAND" >&2
    exit 2
fi

# --- Laws #4/#7/#8: nudge on git push to a non-origin remote ---
# Match: git push <remote> where remote is present, not a flag (-u, --force etc.),
# and not 'origin'.
if echo "$COMMAND" | grep -qP '\bgit\s+push\b'; then
    # Extract the token after 'push' (skip flags starting with -)
    REMOTE=$(echo "$COMMAND" | python3 -c "
import sys, re
cmd = sys.stdin.read().strip()
# Find 'git push' then collect the next non-flag token
m = re.search(r'\bgit\s+push\s+((?:-\S+\s+)*?)(\S+)', cmd)
if m:
    candidate = m.group(2)
    # Must not start with - (flag), must not be a URL pattern
    if candidate and not candidate.startswith('-') and not candidate.startswith('http') and not candidate.startswith('git@'):
        print(candidate)
    else:
        print('')
else:
    print('')
" 2>/dev/null || echo "")

    if [ -n "$REMOTE" ] && [ "$REMOTE" != "origin" ]; then
        echo "Nudge (laws 4, 7 and 8, not a block): a push to a remote other than origin may be a downstream repository. Confirm this checkout is that project, the commits are conventional, and they contain no pricing or internal business data." >&2
        exit 0
    fi
fi

exit 0
