#!/usr/bin/env bash
# Audit A5 (2026-11-28): an 8 x 30 mm slot passed as a Ø8 hole -- only the inradius (across flats) was compared,
# so a bearing would be free along the slot. A round hole and a hex nut trap (corners/flats = 1.155) still pass.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; cd "$t"
mk() { printf '// EXPECTED_HOLE: [10, 10, 5, "Z", 8.0]\n$fa=2; $fs=0.3;\ndifference() { translate([-10,-10,0]) cube([40,40,10]); translate([10,10,-1]) %s; }\n' "$2" > $1.scad
       "$OPENSCAD" --backend=Manifold --render -o $1.stl $1.scad >/dev/null 2>&1 || { echo "render $1 failed"; exit 1; }; }
mk slot 'hull() { translate([-11,0,0]) cylinder(d=8,h=12); translate([11,0,0]) cylinder(d=8,h=12); }'
mk round 'cylinder(d=8/cos(180/90), h=12, $fn=90)'
mk hex 'cylinder(d=8/cos(30), h=12, $fn=6)'
fail=0
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_features.py" --stl slot.stl --scad slot.scad 2>&1); r=$?
[ $r -eq 1 ] && grep -q "not round: across corners 30.000 mm" <<< "$o" || { echo "slot passed as a hole (rc $r): $o"; fail=1; }
for c in round hex; do
    o=$(python3 "$SCAD_MODELER_SCRIPTS/check_features.py" --stl $c.stl --scad $c.scad 2>&1); r=$?
    [ $r -eq 0 ] || { echo "$c hole failed (rc $r): $o"; fail=1; }
done
exit $fail
