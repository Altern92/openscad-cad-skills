#!/usr/bin/env bash
# P32 gears (AC-G1/G2/G3): "kind":"bevel" -> axes intersect (<=0.05 mm) and meet at the shaft angle (+-0.1 deg);
# "kind":"worm" -> axes perpendicular and common-normal distance = BOSL2 worm_dist() (+-0.05 mm).
# No kind on non-parallel axes keeps "NOT CHECKED". RC steering_reduction_gearbox declares its worm/bevel pairs as plain
# gear_mesh (no kind) so it stays NOT CHECKED until the project adds "kind" -- that project is deliberately not edited.
set -uo pipefail
M="$SCAD_MODELER_SCRIPTS/motion_sweep.py"; OPENSCAD=${OPENSCAD:-openscad}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"; fail=0
hdr='include <BOSL2/std.scad>
include <BOSL2/gears.scad>'
printf '%s\nbevel_gear(teeth=12, mate_teeth=20, mod=2, anchor="apex", shaft_diam=5);\n' "$hdr" > b1.scad
printf '%s\nbevel_gear(teeth=20, mate_teeth=12, mod=2, anchor="apex", orient=RIGHT, shaft_diam=5);\n' "$hdr" > b2.scad
printf '%s\nrotate([0,90,0]) worm(mod=1, d=10, l=20, starts=1);\n' "$hdr" > w0.scad
printf '%s\nworm_gear(mod=1, teeth=20, worm_diam=10);\n' "$hdr" > g.scad
printf '%s\necho(D=worm_dist(d=10, starts=1, teeth=20, mod=1));\n' "$hdr" > wd.scad
for f in b1 b2 w0 g wd; do "$OPENSCAD" --backend=Manifold -o $f.$([ $f = wd ] && echo echo || echo stl) $f.scad >/dev/null 2>&1 || { echo "render $f failed" >&2; exit 1; }; done
WD=$(sed -n 's/.*D = //p' wd.echo)
# place <in.stl> <out.stl> <dx> <dy> <dz> <rot about y, deg>
place() { python3 -c "
import sys,trimesh,numpy as np; m=trimesh.load(sys.argv[1])
m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(float(sys.argv[6])),[0,1,0]))
m.apply_translation([float(x) for x in sys.argv[3:6]]); m.export(sys.argv[2])" "$@"; }
# bj <out> <extra contact fields> <gear2 origin y> <rot deg>: gear 1 axis +z, gear 2 axis -x rotated about y
bj() {
  ax=$(python3 -c "import math,sys; t=math.radians(float(sys.argv[1])); print([round(math.cos(t),6),0,round(-math.sin(t),6)])" "$4")
  cat > "$1" <<J
{"static": [], "contacts": [{"pair": ["b1", "b2"], "joint_type": "gear_mesh", "expected_interference_mm": [0, 500], "multi_region_ok": true $2}],
 "motion": [{"id": "s", "range_deg": [0, 10], "step_deg": 5, "min_clearance_mm": 0.0, "drivers": [
  {"part": "b1", "type": "revolute", "axis": [0,0,1], "origin": [0,0,0], "ratio": 1.0, "teeth": 12},
  {"part": "b2", "type": "revolute", "axis": $ax, "origin": [0,$3,0], "ratio": -0.6, "teeth": 20}]}]}
J
}
run() { o=$(python3 "$M" --joints "$1" "${@:2}" 2>&1); r=$?; }
expect_fail() { [ $r -eq 3 ] && grep -q "$3" <<< "$o" || { echo "$2 (rc $r): $o" >&2; fail=1; }; }
cp b2.stl b2_ok.stl
bj ok.json ', "kind": "bevel", "module": 2' 0 0
cp b2_ok.stl b2.stl; run ok.json b1.stl b2.stl
grep -q "OK: bevel axes b1<->b2" <<< "$o" && [ $r -eq 0 ] || { echo "G1: correct bevel pair not OK (rc $r): $o" >&2; fail=1; }
place b2_ok.stl b2.stl 0 0.3 0 0; bj off.json ', "kind": "bevel", "module": 2' 0.3 0
run off.json b1.stl b2.stl; expect_fail "$o" "G1: bevel axes 0.3 mm apart not failed" "bevel axes b1<->b2: .*do not intersect"
place b2_ok.stl b2.stl 0 0 0 2; bj ang.json ', "kind": "bevel", "module": 2' 0 2
run ang.json b1.stl b2.stl; expect_fail "$o" "G1: bevel shaft angle 88 vs 90 not failed" "bevel axes b1<->b2: .*shaft angle"
bj ang2.json ', "kind": "bevel", "module": 2, "shaft_angle": 88' 0 2
run ang2.json b1.stl b2.stl; [ $r -eq 0 ] && grep -q "OK: bevel axes" <<< "$o" || { echo "G1: declared shaft_angle 88 must pass (rc $r): $o" >&2; fail=1; }
bj nokind.json ', "module": 2' 0 0; cp b2_ok.stl b2.stl
run nokind.json b1.stl b2.stl; [ $r -eq 0 ] && grep -q "NOT CHECKED: centre distance b1<->b2 -- the axes are not parallel" <<< "$o" || { echo "G3: no kind must stay NOT CHECKED (rc $r): $o" >&2; fail=1; }
# worm: gear axis +z at origin, worm axis +x offset along y
wj() {  # $1 out, $2 worm y, $3 extra
  cat > "$1" <<J
{"static": [], "contacts": [{"pair": ["worm", "wgear"], "joint_type": "gear_mesh", "kind": "worm", "module": 1, "worm_diam": 10, "expected_interference_mm": [0, 500], "multi_region_ok": true $3}],
 "motion": [{"id": "s", "range_deg": [0, 10], "step_deg": 5, "min_clearance_mm": 0.0, "drivers": [
  {"part": "worm", "type": "revolute", "axis": [1,0,0], "origin": [0,$2,0], "ratio": 20.0, "teeth": 1},
  {"part": "wgear", "type": "revolute", "axis": [0,0,1], "origin": [0,0,0], "ratio": -1.0, "teeth": 20}]}]}
J
}
cp g.stl wgear.stl
place w0.stl worm.stl 0 $WD 0 0; wj w_ok.json $WD ''
run w_ok.json worm.stl wgear.stl; [ $r -eq 0 ] && grep -q "OK: worm centre distance worm<->wgear" <<< "$o" || { echo "G2: correct worm pair not OK (rc $r): $o" >&2; fail=1; }
W2=$(python3 -c "print($WD+0.2)"); place w0.stl worm.stl 0 $W2 0 0; wj w_bad.json $W2 ''
run w_bad.json worm.stl wgear.stl; expect_fail "$o" "G2: worm centre distance +0.2 mm not failed" "worm centre distance worm<->wgear: .*worm_dist"
place w0.stl worm.stl 0 $WD 0 2; python3 - <<'PY'
import json,math; j=json.load(open("w_ok.json")); t=math.radians(2)
j["motion"][0]["drivers"][0]["axis"]=[round(math.cos(t),6),0,round(-math.sin(t),6)]; json.dump(j,open("w_tilt.json","w"))
PY
run w_tilt.json worm.stl wgear.stl; expect_fail "$o" "G2: worm axes 88 deg not failed" "perpendicular"
# worm STL displaced 0.2 mm (along y) while joints.json keeps the correct origin: mesh must be checked against the axis
place w0.stl worm.stl 0 $W2 0 0; run w_ok.json worm.stl wgear.stl; expect_fail "$o" "G2b: worm STL 0.2 mm off declared axis not failed" "worm 'worm'.*off the declared axis"
# worm_dist() unavailable (OPENSCAD unusable): 90 deg test still runs and the result is degraded (exit 2), not a silent pass
place w0.stl worm.stl 0 $WD 0 0; o=$(OPENSCAD=/nonexistent/openscad python3 "$M" --joints w_ok.json worm.stl wgear.stl 2>&1); r=$?
[ $r -eq 2 ] && grep -q "worm_dist() unavailable" <<< "$o" || { echo "G2c: worm_dist unavailable must be exit 2 (rc $r): $o" >&2; fail=1; }
place w0.stl worm.stl 0 $WD 0 2; o=$(OPENSCAD=/nonexistent/openscad python3 "$M" --joints w_tilt.json worm.stl wgear.stl 2>&1); r=$?
[ $r -eq 3 ] && grep -q "perpendicular" <<< "$o" || { echo "G2d: tilted worm must FAIL even without worm_dist (rc $r): $o" >&2; fail=1; }
exit $fail
