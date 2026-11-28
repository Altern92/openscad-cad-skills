#!/usr/bin/env bash
# Audit A6 (2026-11-28): only a zero-width centreline was sampled every 0.25 mm, so a 0.2 mm skin between two
# samples sealed a Ø8 bore unseen, and a Ø1 pinhole passed where a bearing must go. The path is now ray-cast
# (no sampling gap) and an optional "diameter" casts a ring of rays at d/2; an open Ø8 bore still passes.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; cd "$t"
r() { printf '%s\n' "$2" > $1.scad; "$OPENSCAD" --backend=Manifold --render -o $1.stl $1.scad >/dev/null 2>&1 || { echo "render $1 failed"; exit 1; }; }
r skin 'difference(){cube([20,20,20]); translate([-1,10,10]) rotate([0,90,0]) cylinder(d=8,h=11.02,$fn=64); translate([10.22,10,10]) rotate([0,90,0]) cylinder(d=8,h=11,$fn=64);}'
r pin 'difference(){cube([20,20,20]); translate([-1,10,10]) rotate([0,90,0]) cylinder(d=1,h=22,$fn=24);}'
r open 'difference(){cube([20,20,20]); translate([-1,10,10]) rotate([0,90,0]) cylinder(d=8/cos(180/64),h=22,$fn=64);}'
b() { echo '[{"name": "bore", "part": "'$1'", "start": [-5, 10, 10], "end": [18, 10, 10]'"$2"'}]' > $1.json
      o=$(python3 "$SCAD_MODELER_SCRIPTS/check_bore_reachability.py" --bores $1.json $1.stl 2>&1); rc=$?; }
fail=0
b skin ''; [ $rc -eq 3 ] && grep -q "BLOCKED" <<< "$o" || { echo "0.2 mm skin passed (rc $rc): $o"; fail=1; }
b pin ', "diameter": 8'; [ $rc -eq 3 ] && grep -q "narrower than the declared diameter 8" <<< "$o" || { echo "Ø1 pinhole passed as Ø8 (rc $rc): $o"; fail=1; }
b open ', "diameter": 8'; [ $rc -eq 0 ] || { echo "open Ø8 bore failed (rc $rc): $o"; fail=1; }
b pin ''; [ $rc -eq 0 ] && grep -q "no \"diameter\"" <<< "$o" || { echo "pinhole without diameter: centreline only must say so (rc $rc): $o"; fail=1; }
exit $fail
