#!/bin/bash
# PreToolUse hook: Block dangerous git commands
# Source: aihero.dev - "This Hook Stops Claude Code Running Dangerous Git Commands"

INPUT=$(cat)

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Exit early if not a git command
if ! echo "$COMMAND" | grep -qE "git[[:space:]]"; then
  exit 0
fi

DANGEROUS_PATTERNS=(
  "git reset --hard"
  "git clean -fd"
  "git clean -f"
  "git branch -D"
  "git checkout \."
  "git restore \."
  "push --force"
  "reset --hard"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: '$COMMAND' matches dangerous pattern '$pattern'. The user has prevented you from doing this." >&2
    exit 2
  fi
done

# A pipe after `git push` replaces the push's exit code with the filter's, so a
# failed push reads as success (CLAUDE.md no-pipe rule; 5 recorded git push
# strikes, 2 on 2026-10-15 alone). Contract: in one command line, a `git` token,
# a later `push` token and then a `|` or `|&` token blocks the call, whatever
# shell structure sits between them (groups, if/fi, `;`), because the rule is to
# filter in a SEPARATE call. shlex respects quotes, so `git push` inside a quoted
# grep pattern and `||` stay allowed. False blocks (`git push; git log | cat`,
# a piped `git log --grep push`) fail safe. This is a tripwire for habit, not a
# sandbox: `bash -c '...'` payloads, `eval` and `$GIT` variables are not parsed.
# Cases: test-git-push-pipe-guard.sh
PUSH_PIPE=$(COMMAND="$COMMAND" python3 - <<'PYEOF'
import os, re, shlex
cmd = os.environ.get("COMMAND", "")
try:
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    toks = list(lex)
except ValueError:
    # Unbalanced quotes: fall back to a plain pattern match.
    print(1 if re.search(r"\bgit\b[^|]*\bpush\b[^|]*\|(?!\|)", cmd) else 0)
    raise SystemExit
seen_git = seen_push = False
for t in toks:
    if os.path.basename(t) == "git":
        seen_git = True
    elif t == "push" and seen_git:
        seen_push = True
    elif t in ("|", "|&") and seen_push:
        print(1)
        raise SystemExit
print(0)
PYEOF
)
if [ "$PUSH_PIPE" = "1" ]; then
  echo "BLOCKED: a pipe after 'git push' masks its exit code. Run the push bare, echo \$?, and filter output in a separate command." >&2
  exit 2
fi

# `git worktree prune` from WSL unlinks live Codex worktrees whose gitdir is a
# Windows path (C:/Users/...): WSL cannot resolve it, so git calls them prunable.
# The written rule against it was broken the next day, so this is the mechanical
# half. A dry run stays allowed;
# remove real entries one at a time with `git worktree remove` after checks.
if echo "$COMMAND" | grep -qE '(^|[^[:alnum:]_-])worktree[[:space:]]+prune([[:space:]]|$|;|&|\|)'; then
  if ! echo "$COMMAND" | grep -qE 'worktree[[:space:]]+prune[^;&|]*[[:space:]](-n|--dry-run)([[:space:]]|$|;|&|\|)'; then
    echo "BLOCKED: 'git worktree prune' unlinks live worktrees whose gitdir is a Windows path (a Linux checkout treats them as prunable). Run 'git worktree prune --dry-run -v', translate every Windows gitdir to its local mount path and ls it, then remove dead entries one at a time with 'git worktree remove'." >&2
    exit 2
  fi
fi

exit 0
