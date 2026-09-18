#!/usr/bin/env bash
# Runs every test suite in the repo.
#
# jest only matches tests/**/*.test.js. Three suites are named test_*.js /
# test_*.py and were never run by `npm test`, which hid a genuinely failing
# test. This script runs all of them and fails if any one fails.
set -uo pipefail
cd "$(dirname "$0")/.."

status=0
run() {
  printf '\n=== %s\n' "$1"
  shift
  if "$@"; then
    printf '    ok\n'
  else
    printf '    FAILED\n'
    status=1
  fi
}

run "jest"                  npx jest --passWithNoTests
run "text game AI (node)"   node tests/test_text_game_ai_validation.js
run "source sync (python)"  python3 tests/test_source_sync.py
run "generated source (py)" python3 tests/test_text_game_generated_source.py

printf '\n'
if [ "$status" -eq 0 ]; then
  echo "All suites passed."
else
  echo "One or more suites FAILED."
fi
exit "$status"
