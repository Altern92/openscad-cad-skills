#!/usr/bin/env bash
# Proves check_dimensions.py fails a part whose rendered bbox does not match
# its declared "// EXPECTED_BBOX:" -- geometry that compiles, renders and looks
# right but is the wrong size (here: the literal 30 used instead of the
# declared width parameter 40, the "parameter didn't thread through" shape).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=1
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_dimensions.py" --stl part.stl --scad part.scad 2>&1)
actual=$?
rm -f part.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -qiE "FAIL|mismatch"; then
    echo "expected a mismatch report, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
