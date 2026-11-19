#!/usr/bin/env bash
# P26 / AC-21 (2026-11-19, found revalidating the RC rear axle). The positioned render made one STL per
# parts/*.scad file, so a LAYOUT instance that reuses a part file (mirror copy axle_tube_l, upper_arm_l)
# never reached collisions, contact_geometry or fasteners: the whole left side of an axle went unchecked.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
P="$tmp/p"; mkdir -p "$P/parts"; cd "$P"
cat > layout.scad <<'S'
// origin: base corner; +Z up
LZ = is_undef(LZ) ? 5 : LZ;
LAYOUT = [
    ["base",  [0, 0, 0],    [0, 0, 0]],
    ["peg",   [5, 5, 11],   [0, 0, 0]],
    ["peg_l", [25, 5, LZ],  [0, 0, 0]],
];
module at(n) { for (e = LAYOUT) if (e[0] == n) translate(e[1]) rotate(e[2]) children(); }
S
cat > assembly.scad <<'S'
include <layout.scad>
use <parts/base.scad>
use <parts/peg.scad>
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
module part_by_name(n) {
    if (n == "base") base();
    else if (n == "peg" || n == "peg_l") peg();
    else assert(false, str("Unknown part: ", n));
}
if (MODE == "assembly") { for (e = LAYOUT) at(e[0]) part_by_name(e[0]); }
else if (MODE == "part") { at(PART) part_by_name(PART); }
S
printf '// EXPECTED_BBOX: [40, 20, 10]\n// EXPECTED_THROUGH_HOLES: 0\nmodule base(){cube([40,20,10]);}\nbase();\n' > parts/base.scad
printf '// EXPECTED_BBOX: [10, 10, 10]\n// EXPECTED_THROUGH_HOLES: 0\nmodule peg(){cube([10,10,10]);}\npeg();\n' > parts/peg.scad
fail=0
res() { grep -o "CHECK_RESULT $1=[A-Z]*" <<< "$2" | head -1; }
# the mirror copy peg_l sinks 5 mm into the base: only the instance collides
out=$(bash "$V" --all 2>&1)
[ -s build/positioned/peg_l.stl ] || { echo "AC-21: no positioned STL for LAYOUT instance peg_l" >&2; fail=1; }
[ "$(res collisions "$out")" = "CHECK_RESULT collisions=FAIL" ] && grep -q <<< "$out" "peg_l" \
    || { echo "AC-21: collision of the mirror copy not caught: $(grep -E 'collisions|peg_l' <<< "$out" | head -5)" >&2; fail=1; }
# negative: the copy clears the base by 1 mm -> collisions PASS
sed -i '' 's/? 5 :/? 11 :/' layout.scad
out=$(bash "$V" --all 2>&1)
[ "$(res collisions "$out")" = "CHECK_RESULT collisions=PASS" ] \
    || { echo "AC-21: resting copy not PASS: $(grep -E 'collisions|peg_l' <<< "$out" | head -5)" >&2; fail=1; }
# AC-3b: motion_sweep names are exact too -- "peg" must neither match two STLs nor cover the copy peg_l
echo '{"static":["base","peg_l"],"contacts":[],"motion":[{"id":"spin","range_deg":[0,10],"step_deg":5,"drivers":[{"part":"peg","type":"revolute","axis":[0,0,1],"origin":[10,10,0],"ratio":1.0}]}]}' > joints.json
out=$(bash "$V" --all 2>&1)
grep -q <<< "$out" "matches no STL" && { echo "AC-3b: exact static names rejected: $(grep -E 'mechanics|matches' <<< "$out" | head -3)" >&2; fail=1; }
echo '{"static":["base"],"contacts":[],"motion":[{"id":"spin","range_deg":[0,10],"step_deg":5,"drivers":[{"part":"peg","type":"revolute","axis":[0,0,1],"origin":[10,10,0],"ratio":1.0}]}]}' > joints.json
out=$(bash "$V" --all 2>&1)
[ "$(res mechanics "$out")" = "CHECK_RESULT mechanics=FAIL" ] && grep -q <<< "$out" "peg_l" \
    || { echo "AC-3b: copy peg_l covered by the name peg: $(grep -E 'mechanics|peg_l' <<< "$out" | head -3)" >&2; fail=1; }
[ $fail -eq 0 ] && echo "PASS: layout_instances"
exit $fail
