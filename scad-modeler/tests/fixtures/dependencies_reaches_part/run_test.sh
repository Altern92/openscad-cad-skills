#!/usr/bin/env bash
# Negative witness for check_dependencies.py: a change that reaches a part file
# must be reported as a STRONGER class than C1, and the part must be NAMED.
#
# The existing fixture (dependencies_change_class) asserts the weak case -- a
# value used only inside a formula, class C1, "no render needed". Both halves are
# needed: if the tool reported C1 for everything, that fixture would still pass
# while the tool told every caller "nothing downstream" and no one re-rendered
# anything. Formal verification calls that a constant assertion.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_dependencies.py" --scad params.scad \
    --change wall --parts-dir parts 2>&1)
actual=$?
if [ "$actual" -ne 0 ]; then
    echo "expected exit 0, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -q "C1" && {
    echo "reported C1 for a change that reaches parts/panel.scad:" >&2
    echo "$out" >&2
    exit 1; }
echo "$out" | grep -qE "C[2345]" || {
    echo "expected an edit class stronger than C1, got:" >&2
    echo "$out" >&2
    exit 1; }
echo "$out" | grep -q "panel" || {
    echo "expected the affected part to be named, got:" >&2
    echo "$out" >&2
    exit 1; }
exit 0
