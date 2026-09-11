#!/usr/bin/env bash
# Proves check_subfeature_overlap.py fails when two named sub-modules of one
# part overlap -- the failure check_collisions.py structurally cannot see.
# Reproduction of INCIDENTS.md 2026-08-19 (tower/cradle, 419mm3).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=3
"$OPENSCAD" --backend=Manifold --render -o box_a.stl box_a.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o box_b.stl box_b.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_subfeature_overlap.py" box_a.stl box_b.stl 2>&1)
actual=$?
rm -f box_a.stl box_b.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -qi "overlap\|FAIL"; then
    echo "expected an overlap report, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
