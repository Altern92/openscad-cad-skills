#!/usr/bin/env bash
# P29: a gear's declared driver axis must be its real axis (AC-1), and a gear_mesh with "module" must sit at
# BOSL2 gear_dist() (AC-2). Real case: examples/gear_reduction sat 0.345 mm too close and a further 1.2 mm passed.
set -uo pipefail
M="$SCAD_MODELER_SCRIPTS/motion_sweep.py"; OPENSCAD=${OPENSCAD:-openscad}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"; fail=0
hdr='include <BOSL2/std.scad>
include <BOSL2/gears.scad>'
printf '%s\nspur_gear(mod=1, teeth=11, thickness=6, shaft_diam=5, backlash=0.15, gear_spin=-90);\n' "$hdr" > pinion.scad
printf '%s\nspur_gear(mod=1, teeth=66, thickness=6, shaft_diam=5, backlash=0.15, gear_spin=-90+180/66);\n' "$hdr" > spur0.scad
printf '%s\ndifference() { spur_gear(mod=1, teeth=66, thickness=6, shaft_diam=5, backlash=0.15, gear_spin=-90+180/66); translate([2, -1, -5]) cube([3, 2, 10]); }\n' "$hdr" > keyed0.scad
for f in pinion spur0 keyed0; do "$OPENSCAD" --backend=Manifold -o $f.stl $f.scad >/dev/null 2>&1 || { echo "render $f failed" >&2; exit 1; }; done
D=38.8453   # gear_dist(mod=1, 11, 66) with auto profile shift (0.357 on the pinion); gear_spin -90 / -90+180/66 = teeth interleave
place() { python3 -c "import sys,trimesh; m=trimesh.load(sys.argv[1]); m.apply_translation([float(sys.argv[3]),0,0]); m.export(sys.argv[2])" "$1" "$2" "$3"; }
joints() {  # $1 out, $2 spur part, $3 spur origin x, $4 extra contact fields
  cat > "$1" <<J
{"static": [], "contacts": [{"pair": ["pinion", "$2"], "joint_type": "gear_mesh", "expected_interference_mm": [0, 0.05], "multi_region_ok": true $4}],
 "motion": [{"id": "stage", "range_deg": [0, 360], "step_deg": 3, "min_clearance_mm": 0.0, "drivers": [
  {"part": "pinion", "type": "revolute", "axis": [0,0,1], "origin": [0,0,0], "ratio": 1.0, "teeth": 11},
  {"part": "$2", "type": "revolute", "axis": [0,0,1], "origin": [$3,0,0], "ratio": -0.16667, "teeth": 66}]}]}
J
}
run() { o=$(python3 "$M" --joints "$1" "${@:2}" 2>&1); r=$?; }
place spur0.stl spur.stl $D
joints ok.json spur $D ', "module": 1'
run ok.json pinion.stl spur.stl; [ $r -eq 0 ] || { echo "correct pair must pass (rc $r): $o" >&2; fail=1; }
place spur0.stl spur_close.stl 37.6453; mv spur_close.stl spur.stl
run ok.json pinion.stl spur.stl; [ $r -eq 3 ] && grep -q "real axis is" <<< "$o" || { echo "AC-1: spur 1.2 mm off its declared axis not failed (rc $r): $o" >&2; fail=1; }
place spur0.stl spur.stl 38.5; joints d385.json spur 38.5 ', "module": 1'
run d385.json pinion.stl spur.stl; [ $r -eq 3 ] && grep -q "centre distance pinion<->spur: axes are" <<< "$o" || { echo "AC-2: 38.5 mm without profile shift not failed (rc $r): $o" >&2; fail=1; }
place spur0.stl spur.stl $D; joints nomod.json spur $D ''
run nomod.json pinion.stl spur.stl; [ $r -eq 0 ] && grep -q "NOT CHECKED: centre distance" <<< "$o" || { echo "AC-2: no module must say NOT CHECKED and pass (rc $r): $o" >&2; fail=1; }
place keyed0.stl keyed.stl $D; joints keyed.json keyed $D ', "module": 1'
run keyed.json pinion.stl keyed.stl; grep -q "NOT CHECKED: axis" <<< "$o" && ! grep -q "FAIL.*axis" <<< "$o" || { echo "AC-1: keyed gear must be NOT CHECKED, not failed (rc $r): $o" >&2; fail=1; }
# P29b (fresh review): boundary cases, keyed gear still distance-checked, helical, missing teeth, bad input, tilt
place spur0.stl spur.stl 38.9453; joints near.json spur $D ', "module": 1'
run near.json pinion.stl spur.stl; [ $r -eq 3 ] && grep -q "real axis is" <<< "$o" || { echo "P29b: spur 0.1 mm off its axis not failed (rc $r): $o" >&2; fail=1; }
place spur0.stl spur.stl 38.8753; joints tiny.json spur 38.8753 ', "module": 1'
run tiny.json pinion.stl spur.stl; ! grep -q "FAIL: gear axis" <<< "$o" || { echo "P29b: 0.03 mm (inside tolerance) failed: $o" >&2; fail=1; }
place keyed0.stl keyed.stl 38.70; joints keyedbad.json keyed 38.70 ', "module": 1'
run keyedbad.json pinion.stl keyed.stl; [ $r -eq 3 ] && grep -q "centre distance pinion<->keyed: axes are" <<< "$o" || { echo "P29b: keyed gear at a wrong distance passed (rc $r): $o" >&2; fail=1; }
sed 's/, "teeth": 66//' ok.json > noteeth.json; place spur0.stl spur.stl $D
run noteeth.json pinion.stl spur.stl; grep -q "NOT CHECKED: centre distance pinion<->spur -- both need" <<< "$o" || { echo "P29b: gear without teeth skipped silently (rc $r): $o" >&2; fail=1; }
joints badps.json spur $D ', "module": 1, "profile_shift": 0'
run badps.json pinion.stl spur.stl; [ $r -eq 4 ] && grep -q '"profile_shift" must be' <<< "$o" || { echo "P29b: bad profile_shift not a usage error (rc $r): $o" >&2; fail=1; }
python3 -c "import sys,trimesh,numpy as np; m=trimesh.load('spur0.stl'); m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(1.5),[0,1,0])); m.apply_translation([float(sys.argv[1]),0,0]); m.export('spur.stl')" $D
run ok.json pinion.stl spur.stl; [ $r -eq 3 ] && grep -q "tilted" <<< "$o" || { echo "P29b: spur tilted 1.5 deg not failed (rc $r): $o" >&2; fail=1; }
printf '%s\nspur_gear(mod=1, teeth=13, thickness=6, shaft_diam=4, helical=20, gear_spin=-90);\n' "$hdr" > h1.scad
printf '%s\nspur_gear(mod=1, teeth=30, thickness=6, shaft_diam=4, helical=-20, gear_spin=-90+180/30);\n' "$hdr" > h20.scad
for f in h1 h20; do "$OPENSCAD" --backend=Manifold -o $f.stl $f.scad >/dev/null 2>&1; done
HD=$(printf '%s\necho(H=gear_dist(mod=1, teeth1=13, teeth2=30, helical=20));\n' "$hdr" > hd.scad; "$OPENSCAD" -o hd.echo hd.scad >/dev/null 2>&1; sed -n 's/.*H = //p' hd.echo)
place h20.stl h2.stl $HD
cat > hel.json <<J
{"static": [], "contacts": [{"pair": ["h1", "h2"], "joint_type": "gear_mesh", "expected_interference_mm": [0, 5], "multi_region_ok": true, "module": 1, "helical": 20}],
 "motion": [{"id": "s", "range_deg": [0, 10], "step_deg": 5, "min_clearance_mm": 0.0, "drivers": [
  {"part": "h1", "type": "revolute", "axis": [0,0,1], "origin": [0,0,0], "ratio": 1.0, "teeth": 13},
  {"part": "h2", "type": "revolute", "axis": [0,0,1], "origin": [$HD,0,0], "ratio": -0.43333, "teeth": 30}]}]}
J
run hel.json h1.stl h2.stl; grep -q "OK: centre distance h1<->h2" <<< "$o" || { echo "P29b: helical pair at gear_dist(helical=20) not OK (rc $r): $o" >&2; fail=1; }
exit $fail
