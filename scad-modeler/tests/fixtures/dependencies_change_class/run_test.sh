#!/usr/bin/env bash
# Pins the two things check_dependencies.py must get right:
#   1. a parameter feeding a formula is traced to that formula (an edge)
#   2. a change with no downstream part is classed C1, so the caller is told
#      "no render needed" instead of being told nothing
# Both are advisory by the script's own docstring, which is fine -- but
# silently losing the edge, or mislabelling the class, would hand the caller a
# confident and wrong scope.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_dependencies.py" --scad params.scad --change post_d 2>&1)
actual=$?
if [ "$actual" -ne 0 ]; then
    echo "expected exit 0, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -q "post_d->derived_gap" || {
    echo "the edge post_d->derived_gap was not reported:" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q "C1" || {
    echo "expected edit class C1 for a change with no downstream part:" >&2; echo "$out" >&2; exit 1; }
# The script must keep saying it is advisory. If that caveat ever disappears,
# a caller could read the subset as permission to skip the full validation.
echo "$out" | grep -qi "advisory" || {
    echo "the advisory caveat is gone from the output:" >&2; echo "$out" >&2; exit 1; }
exit 0
