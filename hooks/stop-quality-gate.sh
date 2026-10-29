#!/usr/bin/env bash
# Stop hook: runs lint + typecheck + tests before Claude finishes.
# Catches quality issues so Claude can self-correct before presenting results.
# Runs: linter -> typecheck -> tests (short-circuits on first failure category).

set -euo pipefail

INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "")
STOP_HOOK_ACTIVE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stop_hook_active', False))" 2>/dev/null || echo "False")

# Prevent infinite loops
if [ "$STOP_HOOK_ACTIVE" = "True" ]; then
    exit 0
fi

if [ -z "$CWD" ]; then
    exit 0
fi

# Walk up to find project root
find_project_root() {
    local dir="$1"
    local depth=0
    while [ "$depth" -lt 6 ] && [ "$dir" != "/" ]; do
        if [ -f "$dir/pyproject.toml" ] || [ -f "$dir/setup.py" ] || [ -f "$dir/requirements.txt" ]; then
            echo "python:$dir"
            return 0
        fi
        if [ -f "$dir/package.json" ]; then
            echo "node:$dir"
            return 0
        fi
        dir=$(dirname "$dir")
        depth=$((depth + 1))
    done
    echo "none:"
}

RESULT=$(find_project_root "$CWD")
PROJECT_TYPE="${RESULT%%:*}"
PROJECT_DIR="${RESULT#*:}"

if [ "$PROJECT_TYPE" = "none" ] || [ -z "$PROJECT_DIR" ]; then
    exit 0
fi

ERRORS=""

# --- LINT ---
case "$PROJECT_TYPE" in
    python)
        if [ -f "$PROJECT_DIR/.venv/bin/ruff" ]; then
            LINT_OUT=$(cd "$PROJECT_DIR" && .venv/bin/ruff check . --no-fix 2>&1 | tail -15) || true
            if echo "$LINT_OUT" | grep -qE "^Found [1-9]"; then
                ERRORS="$ERRORS\n[LINT] ruff found issues:\n$LINT_OUT"
            fi
        fi
        ;;
    node)
        # Only run eslint if config exists (v9 flat config or legacy)
        if [ -f "$PROJECT_DIR/node_modules/.bin/eslint" ] && \
           { [ -f "$PROJECT_DIR/eslint.config.js" ] || [ -f "$PROJECT_DIR/eslint.config.mjs" ] || \
            [ -f "$PROJECT_DIR/.eslintrc.js" ] || [ -f "$PROJECT_DIR/.eslintrc.json" ] || [ -f "$PROJECT_DIR/.eslintrc.yml" ]; }; then
            LINT_OUT=$(cd "$PROJECT_DIR" && timeout 15 npx eslint . --quiet 2>&1 | tail -15) || true
            # Only flag actual lint errors, not config issues
            if echo "$LINT_OUT" | grep -qE "^\s+[0-9]+ error"; then
                ERRORS="$ERRORS\n[LINT] eslint found issues:\n$LINT_OUT"
            fi
        fi
        ;;
esac

# --- TYPECHECK ---
case "$PROJECT_TYPE" in
    python)
        if [ -f "$PROJECT_DIR/.venv/bin/mypy" ]; then
            TYPE_OUT=$(cd "$PROJECT_DIR" && timeout 30 .venv/bin/mypy . --no-error-summary 2>&1 | grep -E "error:" | head -10) || true
            if [ -n "$TYPE_OUT" ]; then
                ERRORS="$ERRORS\n[TYPECHECK] mypy errors:\n$TYPE_OUT"
            fi
        fi
        ;;
    node)
        if [ -f "$PROJECT_DIR/tsconfig.json" ]; then
            TYPE_OUT=$(cd "$PROJECT_DIR" && timeout 20 npx tsc --noEmit 2>&1 | grep -E "error TS" | head -10) || true
            if [ -n "$TYPE_OUT" ]; then
                TYPE_COUNT=$(echo "$TYPE_OUT" | wc -l)
                ERRORS="$ERRORS\n[TYPECHECK] $TYPE_COUNT tsc error(s):\n$TYPE_OUT"
            fi
        fi
        ;;
esac

# --- TESTS ---
case "$PROJECT_TYPE" in
    python)
        if [ -d "$PROJECT_DIR/.venv" ] && "$PROJECT_DIR/.venv/bin/python" -m pytest --version &>/dev/null; then
            PYTEST_TARGET="$PROJECT_DIR/tests"
            [ ! -d "$PYTEST_TARGET" ] && PYTEST_TARGET="$PROJECT_DIR"
            TEST_OUT=$("$PROJECT_DIR/.venv/bin/python" -m pytest "$PYTEST_TARGET" --tb=short -q 2>&1 | tail -20) || TEST_EXIT=$?
            if [ "${TEST_EXIT:-0}" -ne 0 ] && [ "${TEST_EXIT:-0}" -ne 5 ]; then
                ERRORS="$ERRORS\n[TESTS] pytest failures:\n$TEST_OUT"
            fi
        fi
        ;;
    node)
        if [ -f "$PROJECT_DIR/vitest.config.ts" ] || [ -f "$PROJECT_DIR/vitest.config.js" ]; then
            TEST_OUT=$(cd "$PROJECT_DIR" && timeout 60 npx vitest run --reporter=verbose 2>&1 | tail -20) || TEST_EXIT=$?
            if [ "${TEST_EXIT:-0}" -ne 0 ]; then
                ERRORS="$ERRORS\n[TESTS] vitest failures:\n$TEST_OUT"
            fi
        elif grep -q '"test"' "$PROJECT_DIR/package.json" 2>/dev/null; then
            TEST_OUT=$(cd "$PROJECT_DIR" && timeout 60 npm test 2>&1 | tail -20) || TEST_EXIT=$?
            if [ "${TEST_EXIT:-0}" -ne 0 ]; then
                ERRORS="$ERRORS\n[TESTS] test failures:\n$TEST_OUT"
            fi
        fi
        ;;
esac

# All clear
if [ -z "$ERRORS" ]; then
    exit 0
fi

# Block and feed errors back to Claude
cat <<EOF
{"decision": "block", "reason": "Quality gate failed. Fix before finishing:\n$ERRORS"}
EOF
