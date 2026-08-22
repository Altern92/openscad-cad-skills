#!/usr/bin/env bash
# Proves check_printability.py's wall-thickness ray-cast measures a
# uniform 0.3mm shell correctly (well below the 0.8mm default minimum),
# isolated from the overhang check via --overhang-deg 90 (disables it --
# see check_overhang()'s "bad = theta < 90-overhang_deg" logic).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=3
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
python3 "$SCAD_MODELER_SCRIPTS/check_printability.py" --stl part.stl --overhang-deg 90
actual=$?
rm -f part.stl
if [ "$actual" -eq "$EXPECTED_EXIT" ]; then
    exit 0
fi
echo "expected exit $EXPECTED_EXIT, got $actual" >&2
exit 1
