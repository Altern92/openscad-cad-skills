#!/usr/bin/env bash
# Proves check_features.py fails when a hole's diameter and centre both shift
# (keeping the near wall at the same distance from the declared axis point).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=1
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_features.py" --stl part.stl --scad part.scad 2>&1)
actual=$?
rm -f part.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -qi "axis offset"; then
    echo "expected 'axis offset' in report, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0

