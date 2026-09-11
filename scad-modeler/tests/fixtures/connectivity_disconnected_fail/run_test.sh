#!/usr/bin/env bash
# Proves check_connectivity.py fails a single printed part that renders as
# several disconnected solids with no EXPECTED_BODIES declaration.
# Direct reproduction of INCIDENTS.md 2026-08-19 (gearbox_frame): the bearing
# disc plus four support legs whose widened radius no longer reached the disc,
# producing 5 shells in one STL that still had a plausible bounding box.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=1
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_connectivity.py" --stl part.stl --scad part.scad 2>&1)
actual=$?
rm -f part.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "disconnected"; then
    echo "expected 'disconnected' in output, got:" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "EXPECTED_BODIES"; then
    echo "expected the EXPECTED_BODIES escape hatch to be named, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
