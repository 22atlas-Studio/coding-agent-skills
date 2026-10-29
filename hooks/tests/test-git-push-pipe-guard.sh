#!/bin/bash
# Self-check for the git-push pipe guard in pre-tool-git-safety.sh.
# Usage: bash test-git-push-pipe-guard.sh [path-to-hook]
# Exit 0 = every case matched, 1 = at least one case failed.

HOOK="${1:-$(cd "$(dirname "$0")/.." && pwd)/pre-tool-git-safety.sh}"
fail=0

run() {
  local want="$1" cmd="$2" got
  python3 -c 'import json,sys; print(json.dumps({"tool_input":{"command":sys.argv[1]}}))' "$cmd" \
    | bash "$HOOK" >/dev/null 2>&1
  got=$?
  if [ "$got" = "$want" ]; then echo "ok   [$got] $cmd"; else echo "FAIL [$got want $want] $cmd"; fail=1; fi
}

# Blocked: a pipe after git push hides its exit code.
run 2 'git push origin master | tee out'
run 2 'git push 2>&1 | grep -v remote'
run 2 'git -C /tmp/repo push origin x:master | cat'
run 2 'git -c push.default=current push | tee out'
run 2 'git --no-pager push | tee out'
run 2 'cd /tmp && git push origin master | cat'
run 2 'git -c core.sshCommand="ssh -i /tmp/key" push | tee out'
run 2 'git -C "/tmp/my repo" push | tee out'
run 2 'git --git-dir /tmp/repo/.git push | tee out'
run 2 "git -C '/tmp/a;b' push | cat"
run 2 'git push origin master |& tee out'
run 2 'ENV_PREFIX=x git push origin master | cat'
run 2 "git push origin 'unbalanced | cat"
# shellcheck disable=SC2016  # the hook must see the literal $(pwd), not an expanded path
run 2 'git -C $(pwd) push | tee out'
run 2 '(git push origin master) | cat'
run 2 '{ git push origin master; } | cat'
run 2 'if true; then git push origin master; fi | cat'
run 2 "$(printf 'git\tpush origin master | cat')"
run 2 'git push origin master; git log | cat'
run 2 '/usr/bin/git push origin master | tee out'

# Allowed: no pipe on the push itself, or git push only appears as text.
run 0 'git push origin master'
run 0 'git push origin master || echo failed'
run 0 'git push origin master > /tmp/push.log 2>&1'
run 0 "grep 'git push' notes.md | sort"
run 0 "grep -n -e 'safety\|git push' notes.md | sed -n 1p"
run 0 'git log --oneline | cat'

# Control: the hook's older dangerous-pattern block still fires.
run 2 "git reset --$(printf 'h%s' ard)"

exit $fail
