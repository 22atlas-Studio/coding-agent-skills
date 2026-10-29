#!/usr/bin/env bash
# Cases for pre-tool-law-inject.sh, taken from the phase-2 hook harness.
# Law 3 blocks a tail/cat/head of a dotenv file.
# Laws 4, 7 and 8 nudge (exit 0, stderr present) on a push to a non-origin remote.
# Exit 0 = every case matched, 1 = at least one case failed.

set -uo pipefail

PASS=0
FAIL=0
HOOK="$(cd "$(dirname "$0")/.." && pwd)/pre-tool-law-inject.sh"

check() {
    local label="$1"
    local expected_exit="$2"
    local expect_stderr="$3"
    local actual_exit="$4"
    local actual_stderr="$5"
    local exit_ok=0
    local stderr_ok=0

    [ "$actual_exit" -eq "$expected_exit" ] && exit_ok=1
    if [ "$expect_stderr" = "yes" ]; then
        [ -n "$actual_stderr" ] && stderr_ok=1
    else
        [ -z "$actual_stderr" ] && stderr_ok=1
    fi

    if [ "$exit_ok" -eq 1 ] && [ "$stderr_ok" -eq 1 ]; then
        echo "PASS  $label  (exit=$actual_exit)"
        PASS=$((PASS + 1))
    else
        echo "FAIL  $label"
        echo "       expected exit=$expected_exit got=$actual_exit"
        echo "       expected stderr=$expect_stderr"
        FAIL=$((FAIL + 1))
    fi
}

run() {
    local label="$1" expected="$2" expect_stderr="$3" command="$4"
    local input stderr exit_code
    input=$(python3 -c 'import json,sys; print(json.dumps({"tool_input":{"command":sys.argv[1]}}))' "$command")
    stderr=$(echo "$input" | bash "$HOOK" 2>&1 >/dev/null) || exit_code=$?
    exit_code=${exit_code:-0}
    check "$label" "$expected" "$expect_stderr" "$exit_code" "$stderr"
}

run "tail .env -> exit 2 blocked (law 3)" 2 yes "tail .env"
run "cat /tmp/project/.env -> exit 2 blocked (law 3)" 2 yes "cat /tmp/project/.env"
run "head .env.local -> exit 2 blocked (law 3)" 2 yes "head -5 .env.local"
run "git push downstream master -> exit 0 with stderr nudge" 0 yes "git push downstream master"
run "git push origin master -> exit 0 silent" 0 no "git push origin master"
run "ls -la -> exit 0 silent" 0 no "ls -la"
run "grep -c of one env var -> exit 0 silent" 0 no "grep -c '^VAR=' .env"
run "git push client-remote main -> exit 0 with stderr nudge" 0 yes "git push client-remote main"

echo "Results: $PASS passed  $FAIL failed  ($((PASS + FAIL)) total)"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
