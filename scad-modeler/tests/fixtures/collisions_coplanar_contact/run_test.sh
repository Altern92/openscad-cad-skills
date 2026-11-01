#!/usr/bin/env bash
# P16 (2026-11-01, external audit E1, reproduced on the mini): a flat lid resting on an
# open box's rim (zero-volume face contact) was reported as "penetration depth 40.000 mm"
# -- FCL's per-contact depth on coplanar faces is the face extent, not a depth. The
# boolean intersection bounds the real depth: empty = touch, else <= its smallest extent.
set -uo pipefail
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
C="$SCAD_MODELER_SCRIPTS/check_collisions.py"
box='difference(){ cube([60,40,30]); translate([2,2,2]) cube([56,36,30]); }'
printf '%s\n' "$box" > "$tmp/b.scad"; openscad -q -o "$tmp/body.stl" "$tmp/b.scad"
# screw holes in the lid matter: a plain slab gives depth 0, the holed lid gave 40.000
printf 'translate([0,0,30]) difference(){ cube([60,40,1.5]); for (x=[6,54], y=[6,34]) translate([x,y,-1]) cylinder(d=3,h=4,$fn=16); }\n' > "$tmp/l.scad"; openscad -q -o "$tmp/lid.stl" "$tmp/l.scad"
printf 'translate([0,0,29]) cube([60,40,1.5]);\n' > "$tmp/s.scad"; openscad -q -o "$tmp/sunk.stl" "$tmp/s.scad"
j='{"contacts":[{"pair":["body","%s"],"joint_type":"resting","expected_interference_mm":[0.0,0.05],"derivation":"lid rests on the rim","multi_region_ok":true}]}'
printf "$j" lid > "$tmp/j1.json"; printf "$j" sunk > "$tmp/j2.json"

out=$(python3 "$C" --expected-contacts "$tmp/j1.json" "$tmp/body.stl" "$tmp/lid.stl" 2>&1); rc=$?
[ "$rc" -eq 0 ] || { echo "resting lid: exit $rc, want 0" >&2; echo "$out" >&2; exit 1; }

# the bound must not hide a real overlap: lid sunk 1 mm into the walls
out=$(python3 "$C" --expected-contacts "$tmp/j2.json" "$tmp/body.stl" "$tmp/sunk.stl" 2>&1); rc=$?
[ "$rc" -eq 3 ] || { echo "sunk lid: exit $rc, want 3" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -Eq 'penetration depth (is )?(0\.9[0-9]*|1\.0[0-9]*) mm' || { echo "sunk lid: depth not ~1 mm" >&2; echo "$out" >&2; exit 1; }
exit 0
