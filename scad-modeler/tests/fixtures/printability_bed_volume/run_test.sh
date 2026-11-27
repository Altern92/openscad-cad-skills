#!/usr/bin/env bash
# P38 rule 1: build volume. Part bbox vs --bed (default 256^3); a too-big part FAILs and the
# message says when a 90 deg turn would fit; a fitting part passes. --overhang-deg 90 / --min-wall 0
# isolate the verdict from the other checks.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
P="$SCAD_MODELER_SCRIPTS/check_printability.py"
"$OPENSCAD" --backend=Manifold --render -o fail.stl fail.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o pass.stl pass.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o big.stl big.scad >/dev/null 2>&1
fo=$(python3 "$P" --stl fail.stl --bed 100 50 20 --overhang-deg 90 --min-wall 0 2>&1); frc=$?
po=$(python3 "$P" --stl pass.stl --overhang-deg 90 --min-wall 0 2>&1); prc=$?
# default bed is unverified: WARN only (exit 0); an explicit --bed FAILs; --build-axis moves the length onto Z
do=$(python3 "$P" --stl big.stl --overhang-deg 90 --min-wall 0 2>&1); drc=$?
eo=$(python3 "$P" --stl big.stl --bed 256 256 256 --overhang-deg 90 --min-wall 0 2>&1); erc=$?
ao=$(python3 "$P" --stl big.stl --bed 256 256 400 --build-axis 1,0,0 --overhang-deg 90 --min-wall 0 2>&1); arc=$?
rm -f fail.stl pass.stl big.stl
if [ "$frc" -eq 3 ] && grep -q <<< "$fo" "BUILD VOLUME" && grep -q <<< "$fo" "90 deg" \
   && [ "$prc" -eq 0 ] && ! grep -q <<< "$po" "BUILD VOLUME" \
   && [ "$drc" -eq 0 ] && grep -q <<< "$do" "WARN: BUILD VOLUME" && ! grep -q <<< "$do" "FAIL" \
   && [ "$erc" -eq 3 ] && grep -q <<< "$eo" "BUILD VOLUME" \
   && [ "$arc" -eq 0 ] && ! grep -q <<< "$ao" "BUILD VOLUME"; then exit 0; fi
echo "fail case rc=$frc:"; echo "$fo"; echo "pass case rc=$prc:"; echo "$po"; echo "default rc=$drc:"; echo "$do"; echo "explicit rc=$erc:"; echo "$eo"; echo "axis rc=$arc:"; echo "$ao"
exit 1
