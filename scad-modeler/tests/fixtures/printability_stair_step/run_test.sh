#!/usr/bin/env bash
# P38 rest (AC-I2): stair stepping INFO with --layer. 10 deg ramp at layer 0.4 prints INFO with step
# width layer/tan(10)=2.3 mm (exit 0); a flat top + 45 deg chamfer prints none.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
P="$SCAD_MODELER_SCRIPTS/check_printability.py"
"$OPENSCAD" --backend=Manifold --render -o fail.stl fail.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o pass.stl pass.scad >/dev/null 2>&1
fo=$(python3 "$P" --stl fail.stl --min-wall 0 --layer 0.4 2>&1); frc=$?
po=$(python3 "$P" --stl pass.stl --min-wall 0 2>&1); prc=$?
rm -f fail.stl pass.stl
if [ "$frc" -eq 0 ] && grep -q <<< "$fo" "INFO: STAIR STEPPING" && grep -q <<< "$fo" "step width 2.3 mm" \
   && grep -q <<< "$fo" "layer 0.4 mm" \
   && [ "$prc" -eq 0 ] && ! grep -q <<< "$po" "STAIR STEPPING"; then exit 0; fi
echo "fail case rc=$frc:"; echo "$fo"; echo "pass case rc=$prc:"; echo "$po"
exit 1
