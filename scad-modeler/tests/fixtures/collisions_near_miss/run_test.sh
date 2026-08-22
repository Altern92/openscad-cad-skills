#!/usr/bin/env bash
# Proves a 0.15mm gap (between --touch-tolerance 0.05 and
# --near-miss-tolerance 0.2, both defaults) is surfaced as a non-fatal
# NEAR MISS note, not a failure and not silently ignored.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=0
"$OPENSCAD" --backend=Manifold --render -o box_a.stl box_a.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o box_b.stl box_b.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_collisions.py" box_a.stl box_b.stl)
actual=$?
rm -f box_a.stl box_b.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    exit 1
fi
if ! echo "$out" | grep -q "NEAR MISS"; then
    echo "expected 'NEAR MISS' in output, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
