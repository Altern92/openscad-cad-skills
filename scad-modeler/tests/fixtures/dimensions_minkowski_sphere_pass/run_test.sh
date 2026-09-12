#!/usr/bin/env bash
# Proves check_dimensions.py tolerates the bounding-box shortfall that a
# minkowski() fillet with a coarse sphere necessarily produces, and reports
# the term it added rather than hiding it.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=0
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_dimensions.py" --stl part.stl --scad part.scad 2>&1)
actual=$?
rm -f part.stl

if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "minkowski-sphere term"; then
    echo "expected the tolerance basis to name the minkowski-sphere term, got:" >&2
    echo "$out" >&2
    exit 1
fi
# The rendered size must still be within the reported tolerance -- guards
# against the term being applied without actually covering the shortfall.
if ! echo "$out" | grep -qE "OK: .* within \[0\\.0[0-9]+, "; then
    echo "expected an OK line with a tolerance >= 0.02mm, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
