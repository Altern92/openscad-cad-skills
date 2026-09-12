#!/usr/bin/env bash
# Proves check_assumptions.py FAILS when a Critical row is still Open, while
# allowing an Ordinary row in the same state. The Ordinary row is deliberate:
# a check that fails on every open row would be unusable, and the distinction
# between Critical and Ordinary is the whole point of the table.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_assumptions.py" --calc calculations.md 2>&1)
actual=$?
if [ "$actual" -ne 1 ]; then
    echo "expected exit 1, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -q "2 CRITICAL" || {
    echo "expected exactly 2 unresolved Critical rows, got:" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q "D3" && {
    echo "the Ordinary/Open row must not be reported as unresolved" >&2; echo "$out" >&2; exit 1; }
exit 0
