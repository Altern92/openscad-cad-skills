#!/usr/bin/env bash
# Proves check_connectivity.py PASSES a two-shell part when the part declares
# "// EXPECTED_BODIES: 2" -- the declared escape hatch from the default-on rule.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=0
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_connectivity.py" --stl part.stl --scad part.scad)
actual=$?
rm -f part.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
