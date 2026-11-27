#!/usr/bin/env bash
# P38 rule 3: bridge span. 8 mm flat ceiling carried both sides = BRIDGE SPAN FAIL; 4 mm = pass
# (Hubs: bridges under 5 mm print unsupported); a one-sided shelf is still an UNSUPPORTED OVERHANG
# (the bridge exemption must not swallow cantilevers).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
P="$SCAD_MODELER_SCRIPTS/check_printability.py"
for n in long short cantilever slab; do "$OPENSCAD" --backend=Manifold --render -o $n.stl $n.scad >/dev/null 2>&1; done
lo=$(python3 "$P" --stl long.stl --min-wall 0 2>&1); lrc=$?
so=$(python3 "$P" --stl short.stl --min-wall 0 2>&1); src=$?
co=$(python3 "$P" --stl cantilever.stl --min-wall 0 2>&1); crc=$?
so2=$(python3 "$P" --stl slab.stl --min-wall 0 2>&1); slrc=$?
rm -f slab.stl long.stl short.stl cantilever.stl
if [ "$lrc" -eq 3 ] && grep -q <<< "$lo" "BRIDGE SPAN" \
   && [ "$src" -eq 0 ] \
   && [ "$crc" -eq 3 ] && grep -q <<< "$co" "UNSUPPORTED OVERHANG" && ! grep -q <<< "$co" "BRIDGE SPAN" \
   && [ "$slrc" -eq 3 ] && grep -q <<< "$so2" "UNSUPPORTED OVERHANG" && ! grep -q <<< "$so2" "BRIDGE SPAN"; then exit 0; fi
echo "long rc=$lrc:"; echo "$lo"; echo "short rc=$src:"; echo "$so"; echo "cantilever rc=$crc:"; echo "$co"; echo "slab rc=$slrc:"; echo "$so2"
exit 1
