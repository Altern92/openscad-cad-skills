#!/usr/bin/env bash
# P38 rest (AC-I1): knife edges. A 30 deg convex wedge edge prints WARN: KNIFE EDGE (exit stays 0);
# a cube with a sharp concave V groove prints none.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
P="$SCAD_MODELER_SCRIPTS/check_printability.py"
"$OPENSCAD" --backend=Manifold --render -o fail.stl fail.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o pass.stl pass.scad >/dev/null 2>&1
fo=$(python3 "$P" --stl fail.stl --min-wall 0 2>&1); frc=$?
po=$(python3 "$P" --stl pass.stl --min-wall 0 2>&1); prc=$?
rm -f fail.stl pass.stl
if [ "$frc" -eq 0 ] && grep -q <<< "$fo" "WARN: KNIFE EDGE" && grep -q <<< "$fo" "30 deg" \
   && [ "$prc" -eq 0 ] && ! grep -q <<< "$po" "KNIFE EDGE"; then exit 0; fi
echo "fail case rc=$frc:"; echo "$fo"; echo "pass case rc=$prc:"; echo "$po"
exit 1
