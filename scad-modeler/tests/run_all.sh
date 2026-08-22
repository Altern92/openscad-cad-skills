#!/usr/bin/env bash
# Persisted regression suite for scad-modeler's own checker scripts (added
# 2026-08-22). Every new checker built this project has, until now, been
# tested once against a synthetic fixture in a scratch directory that gets
# deleted right after the commit -- real, but throwaway, verification.
# Independent research (deep-research pass, 2026-08-22) explicitly flagged
# this as worth fixing: "deterministic regression fixtures ... run
# automatically ... to instantly catch any change that unexpectedly alters
# validation behavior." This is that: each fixtures/<name>/ directory is a
# self-contained, committed reproduction (usually of a REAL incident from
# INCIDENTS.md) with its own run_test.sh that renders whatever .scad it
# needs, runs the checker under test, and compares the exit code against
# what that fixture is supposed to prove.
#
# Usage: bash tests/run_all.sh
#
# Not wired into validate_scad.sh -- this tests the SKILL's own scripts,
# not a user's project. Run it after changing any checker in scripts/.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SCAD_MODELER_SCRIPTS="$SCRIPT_DIR/../scripts"

pass=0
fail=0
failed_names=()

for dir in "$SCRIPT_DIR"/fixtures/*/; do
    name="$(basename "$dir")"
    if [ ! -f "$dir/run_test.sh" ]; then
        continue
    fi
    echo "--- $name ---"
    if (cd "$dir" && bash run_test.sh); then
        echo "PASS: $name"
        pass=$((pass + 1))
    else
        echo "FAIL: $name"
        fail=$((fail + 1))
        failed_names+=("$name")
    fi
    echo ""
done

echo "======================================"
echo "Regression suite: $pass passed, $fail failed."
if [ "$fail" -gt 0 ]; then
    echo "Failed: ${failed_names[*]}"
    exit 1
fi
exit 0
