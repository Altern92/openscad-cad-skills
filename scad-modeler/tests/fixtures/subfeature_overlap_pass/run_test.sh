#!/usr/bin/env bash
# Proves check_subfeature_overlap.py passes two named sub-modules that are clear
# of each other.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=0
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
exit 0
