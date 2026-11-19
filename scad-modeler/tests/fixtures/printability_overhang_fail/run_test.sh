#!/usr/bin/env bash
# Proves check_printability.py flags a genuinely steep overhang (77 deg
# from vertical, well past the 45 deg default) and, via --min-wall 0,
# isolates that verdict from the separate wall-thickness check.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=3
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_printability.py" --stl part.stl --min-wall 0 2>&1)
actual=$?
rm -f part.stl
# P26 / AC-19: exit 3 alone could come from any failure; the overhang must be the reason
if [ "$actual" -eq "$EXPECTED_EXIT" ] && grep -q <<< "$out" "UNSUPPORTED OVERHANG"; then
    exit 0
fi
echo "$out" >&2
echo "expected exit $EXPECTED_EXIT, got $actual" >&2
exit 1
