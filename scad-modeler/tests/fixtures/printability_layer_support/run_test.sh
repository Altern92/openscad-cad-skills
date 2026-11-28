#!/usr/bin/env bash
# Audit A2 (2026-11-28): face normals alone passed a 40 x 40 mm cantilever whose underside is an egg-crate
# of 60 deg pockets (each flat 0.81 mm2 < the region floor), and a 5 mm ledge held only by a V-lip that
# itself hangs in air. Layer support propagation (each layer supported only within layer*tan(overhang)
# of the supported layer below, bridges up to BRIDGE_MAX accepted) FAILs both; a cube, a 4 mm bridge
# between two pillars and a 45 deg chamfered ledge still pass.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; cd "$t"
mk() { printf '%s\n' "$2" > $1.scad; "$OPENSCAD" --backend=Manifold --render -o $1.stl $1.scad >/dev/null 2>&1 || { echo "render $1 failed"; exit 1; }; }
mk egg 'cube([20,40,40]); difference(){ translate([20,0,26]) cube([40,40,14]); for (x=[25:10:55], y=[5:10:35]) translate([x,y,25.99]) linear_extrude(height=7.89, scale=0.9/10.02) square(10.02, center=true); }'
mk vlip 'cube([10,40,20]); translate([10,0,16]) cube([7,40,4]); translate([15,40,16]) rotate([90,0,0]) linear_extrude(40) polygon([[0,0],[2,0],[1,-1.732]]);'
mk cube 'cube(20);'
mk bridge 'cube([4,10,10]); translate([8,0,0]) cube([4,10,10]); translate([0,0,10]) cube([12,10,2]);'
mk chamfer 'cube([10,20,20]); translate([10,0,10]) rotate([-90,0,0]) linear_extrude(20) polygon([[0,0],[10,-10],[0,-10]]);'
fail=0
run() { o=$(python3 "$SCAD_MODELER_SCRIPTS/check_printability.py" --stl $1.stl 2>&1); r=$?; }
for c in egg vlip; do run $c; [ $r -ne 0 ] && grep -q "UNSUPPORTED LAYER" <<< "$o" || { echo "$c passed (rc $r): $(grep -iE 'overhang|bridge|unsupported|OK' <<< "$o")"; fail=1; }; done
for c in cube bridge chamfer; do run $c; grep -q "UNSUPPORTED LAYER" <<< "$o" && { echo "$c false FAIL: $(grep UNSUPPORTED <<< "$o")"; fail=1; }; done
exit $fail
