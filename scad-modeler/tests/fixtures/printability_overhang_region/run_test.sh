#!/usr/bin/env bash
# P38 rule 2: overhang regions. A real ~60 deg overhang FAILs and is reported per region
# (area + centre); a faceted true-45 deg cone and a sub-1mm^2 sliver do not FAIL.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
P="$SCAD_MODELER_SCRIPTS/check_printability.py"
"$OPENSCAD" --backend=Manifold --render -o fail.stl fail.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o pass.stl pass.scad >/dev/null 2>&1
fo=$(python3 "$P" --stl fail.stl --min-wall 0 2>&1); frc=$?
po=$(python3 "$P" --stl pass.stl --min-wall 0 2>&1); prc=$?
rm -f fail.stl pass.stl
if [ "$frc" -eq 3 ] && grep -q <<< "$fo" "UNSUPPORTED OVERHANG" && grep -q <<< "$fo" "region 1" \
   && [ "$prc" -eq 0 ] && ! grep -q <<< "$po" "UNSUPPORTED OVERHANG"; then exit 0; fi
echo "fail case rc=$frc:"; echo "$fo"; echo "pass case rc=$prc:"; echo "$po"
exit 1
