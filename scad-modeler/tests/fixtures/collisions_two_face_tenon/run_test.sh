#!/usr/bin/env bash
# 2026-11-01 (P19 agent eval, clear_span_tenons): a tenon touching both its shoulder face
# and the mortise floor (zero overlap volume) measured "penetration depth 10.000 mm". The
# P16 bound took the smallest extent of the WHOLE intersection's bounding box, and the two
# zero-volume contact sheets, 10 mm apart, span 10 mm. The agent widened the joint by
# 0.1 mm per end to get past it. Zero-volume pieces are touches, not depth.
set -uo pipefail
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
C="$SCAD_MODELER_SCRIPTS/check_collisions.py"
printf 'difference(){ translate([-80,0,0]) cube([20,20,100]); translate([-70,3.8,46.8]) cube([10.01,12.4,6.4]); }\n' > "$tmp/u.scad"
openscad -q -o "$tmp/upright.stl" "$tmp/u.scad"
bar() { printf 'translate([%s,0,0]) union(){ translate([-60,0,45]) cube([120,20,10]); translate([-70,4,47]) cube([10.001,12,6]); }\n' "$1" > "$tmp/b$1.scad"; openscad -q -o "$tmp/bar$2.stl" "$tmp/b$1.scad"; }
bar 0 _touch; bar -0.5 _sunk
j='{"contacts":[{"pair":["upright","%s"],"joint_type":"fixed","expected_interference_mm":[0.0,0.05],"derivation":"tenon bottoms out at the shoulder and mortise floor"}]}'
printf "$j" bar_touch > "$tmp/j1.json"; printf "$j" bar_sunk > "$tmp/j2.json"

out=$(python3 "$C" --expected-contacts "$tmp/j1.json" "$tmp/upright.stl" "$tmp/bar_touch.stl" 2>&1); rc=$?
[ "$rc" -eq 0 ] || { echo "two-face touch: exit $rc, want 0" >&2; echo "$out" | grep -E "depth|FAIL" >&2; exit 1; }

# the fix must not hide a real overlap: bar pushed 0.5 mm into the upright
out=$(python3 "$C" --expected-contacts "$tmp/j2.json" "$tmp/upright.stl" "$tmp/bar_sunk.stl" 2>&1); rc=$?
[ "$rc" -eq 3 ] || { echo "sunk tenon: exit $rc, want 3" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -Eq 'penetration depth (is )?0\.(4[5-9]|5[0-5])[0-9]* mm' || { echo "sunk tenon: depth not ~0.5 mm" >&2; echo "$out" | grep depth >&2; exit 1; }
exit 0
