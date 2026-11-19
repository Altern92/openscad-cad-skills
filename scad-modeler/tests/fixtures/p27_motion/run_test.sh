#!/usr/bin/env bash
# P27 (Fable calculation audit): AC-3 descending range (bad input = rc 4 here), AC-4 declared contact vs min_clearance, AC-5 teeth shortcut
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; M="$SCAD_MODELER_SCRIPTS/motion_sweep.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"; cp "$here"/*.stl "$here"/*.json .
fail=0
run() { o=$(python3 "$M" --joints "$1" "${@:2}" 2>&1); r=$?; }
run asc.json arm.stl post.stl;  [ $r -ne 0 ] || { echo "baseline: ascending swing should FAIL: $o" >&2; fail=1; }
run desc.json arm.stl post.stl; [ $r -ne 0 ] && grep -q "interference" <<< "$o" \
    || { echo "AC-3: descending range_deg passed (rc $r): $o" >&2; fail=1; }
sed 's/"step_deg": 2/"step_deg": -2/' asc.json > negstep.json
run negstep.json arm.stl post.stl; [ $r -eq 4 ] || { echo "AC-3: negative step_deg not bad input (rc $r): $o" >&2; fail=1; }
cp m2_arm.stl arm2.stl; cp m2_pin.stl pin.stl; cp m2_far.stl far.stl
sed 's/"arm"/"arm2"/g' m2_c3.json > c3.json; sed 's/"arm"/"arm2"/g' m2_c0.json > c0.json
run c0.json arm2.stl pin.stl far.stl; [ $r -eq 0 ] || { echo "baseline: hinge at clearance 0 should pass: $o" >&2; fail=1; }
# P27b: a declared contact keeps the motion's min_clearance unless it states its own (exempting every declared
# pair hid near-misses elsewhere on the same two bodies -- Fable review of P27)
run c3.json arm2.stl pin.stl far.stl; [ $r -ne 0 ] || { echo "AC-4b: declared hinge silently exempt from 0.3 mm: $o" >&2; fail=1; }
python3 -c "import json; d=json.load(open('c3.json')); d['contacts'][0]['min_clearance_mm']=0.0; json.dump(d, open('c3own.json','w'))"
run c3own.json arm2.stl pin.stl far.stl; [ $r -eq 0 ] || { echo "AC-4: hinge with its own min_clearance 0 failed (rc $r): $o" >&2; fail=1; }
sed 's/"min_clearance_mm": 0.3/"min_clearance_mm": 500/' c3own.json > c500.json
run c500.json arm2.stl pin.stl far.stl; [ $r -ne 0 ] || { echo "AC-4: undeclared pair escaped min_clearance: $o" >&2; fail=1; }
cp m3_gear.stl gear.stl; cp m3_post.stl post3.stl; sed 's/"post"/"post3"/' m3_t.json > t.json
run t.json gear.stl post3.stl; [ $r -ne 0 ] || { echo "AC-5: teeth shortcut on an asymmetric part passed: $o" >&2; fail=1; }
# AC-5b: a 1x1x2 mm nub on a 120 mm disc breaks the symmetry (random samples missed it); a plain disc keeps it
OPENSCAD=${OPENSCAD:-openscad}
printf 'cylinder(d=120, h=6, $fn=60);\n' > disc.scad
printf 'union() { cylinder(d=120, h=6, $fn=60); translate([59, -0.5, 5.5]) cube([1, 1, 2.5]); }\n' > nub.scad
printf 'rotate([0, 0, 100]) translate([58.5, -3, 6.5]) cube([3, 6, 3]);\n' > post4.scad
for f in disc nub post4; do "$OPENSCAD" --backend=Manifold -o $f.stl $f.scad >/dev/null 2>&1; done
mj() { echo '{"static": ["post4"], "motion": [{"id": "spin", "range_deg": [0, 360], "step_deg": 1, "drivers": [{"part": "'$1'", "type": "revolute", "axis": [0, 0, 1], "origin": [0, 0, 0], "ratio": 1'$2'}]}]}' > $1$3.json; }
mj nub "" ""; run nub.json nub.stl post4.stl; [ $r -ne 0 ] || { echo "AC-5b baseline: nub must hit the post: $o" >&2; fail=1; }
mj nub ', "teeth": 20' t; run nubt.json nub.stl post4.stl; [ $r -ne 0 ] || { echo "AC-5b: teeth shortcut hid the nub: $o" >&2; fail=1; }
mj disc ', "teeth": 20' t; run disct.json disc.stl post4.stl
[ $r -eq 0 ] && grep -q "gear periodicity: sweeping" <<< "$o" || { echo "AC-5: symmetric disc lost its shortcut (rc $r): $o" >&2; fail=1; }
exit $fail
