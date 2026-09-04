#!/usr/bin/env bash
# Proves motion_sweep.py's gear-ratio sign check (added 2026-09-04) refuses
# to sweep a declared gear_mesh pair whose drivers share the same sign --
# same shape as the real pinion/spur pair (see the real gear_reduction
# example), but with the spur's ratio wrongly left positive. Uses fake STL
# paths deliberately: the sign check must fail BEFORE any mesh is loaded.
set -uo pipefail
EXPECTED_EXIT=3
out=$(python3 "$SCAD_MODELER_SCRIPTS/motion_sweep.py" --joints joints.json fake_a.stl fake_b.stl 2>&1)
actual=$?
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "SAME-sign ratio"; then
    echo "expected 'SAME-sign ratio' in output, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
