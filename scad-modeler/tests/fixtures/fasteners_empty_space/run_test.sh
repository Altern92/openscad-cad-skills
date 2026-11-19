#!/usr/bin/env bash
# P26 / AC-7 (Fable audit e8): every fastener test asked that something is ABSENT (head room, free shank),
# so a screw declared at [200, 200, 200], far from any part, came back OK. A screw must seat its head on
# material and pass through a part.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"
# 20 mm block with a 2.5 mm pilot hole from the top centre
printf 'difference(){ cube([20,20,20]); translate([10,10,5]) cylinder(d=2.5, h=16, $fn=24); }\n' > block.scad
"$OPENSCAD" --backend=Manifold --render -o block.stl block.scad >/dev/null 2>&1
fail=0
run() { echo "$1" > fasteners.json; o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners fasteners.json block.stl 2>&1); r=$?; }
run '{"fasteners":[{"name":"M3 in thin air","start":[200,200,200],"axis":[0,0,-1],"d":3,"length":12}]}'
[ $r -ne 0 ] && grep -q <<< "$o" "empty space" && grep -q <<< "$o" "seats on nothing" \
    || { echo "AC-7: screw in empty space passed (rc $r): $o" >&2; fail=1; }
run '{"fasteners":[{"name":"M3 into block","start":[10,10,20],"axis":[0,0,-1],"d":3,"length":12,"into":"block"}]}'
[ $r -eq 0 ] || { echo "AC-7: real screw into the block failed (rc $r): $o" >&2; fail=1; }
exit $fail
