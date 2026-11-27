#!/usr/bin/env bash
# P38 rule 4: bed contact. WARN only: sharp corners on the plate face print a BED CONTACT warning
# (exit stays 0); a rounded footprint prints none.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
P="$SCAD_MODELER_SCRIPTS/check_printability.py"
"$OPENSCAD" --backend=Manifold --render -o warn.stl warn.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o pass.stl pass.scad >/dev/null 2>&1
wo=$(python3 "$P" --stl warn.stl 2>&1); wrc=$?
"$OPENSCAD" --backend=Manifold --render -o small.stl small.scad >/dev/null 2>&1
so=$(python3 "$P" --stl small.stl 2>&1); src=$?
po=$(python3 "$P" --stl pass.stl 2>&1); prc=$?
rm -f small.stl warn.stl pass.stl
if [ "$wrc" -eq 0 ] && grep -q <<< "$wo" "WARN: BED CONTACT" \
   && [ "$prc" -eq 0 ] && ! grep -q <<< "$po" "BED CONTACT" \
   && [ "$src" -eq 0 ] && ! grep -q <<< "$so" "BED CONTACT" && [ "$(grep -c "BED CONTACT" <<< "$wo")" -eq 1 ]; then exit 0; fi
echo "warn case rc=$wrc:"; echo "$wo"; echo "pass case rc=$prc:"; echo "$po"
exit 1
