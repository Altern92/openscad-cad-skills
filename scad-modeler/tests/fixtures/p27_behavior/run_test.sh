#!/usr/bin/env bash
# P27 (Fable calculation audit) on check_behavior.py: AC-13 imported STL is part of the render cache key,
# AC-14 the angle echo uses the worst |value| over every match (a mirrored copy echoes the same name)
set -uo pipefail
B="$SCAD_MODELER_SCRIPTS/check_behavior.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"
fail=0
mk() { python3 -c "import trimesh; m=trimesh.creation.box(extents=[20,20,10]); m.apply_translation([10,10,15+$1]); m.export('servo.stl')"; }
cat > assembly.scad <<'S'
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
if (PART == "a") cube([20, 20, 10]);
if (PART == "b") import("servo.stl");
S
echo '{"bodies": {"a": {"render": [{"MODE": "part", "PART": "a"}]}, "b": {"render": [{"MODE": "part", "PART": "b"}]}}, "joints": [{"a": "a", "b": "b", "max_gap": 0.3, "why": "sits on top"}]}' > behavior.json
mk 0; o=$(python3 "$B" --project-dir . 2>&1); r=$?
[ $r -eq 0 ] || { echo "AC-13 baseline: b on a should pass: $o" >&2; fail=1; }
mk 50; o=$(python3 "$B" --project-dir . 2>&1); r=$?
[ $r -ne 0 ] || { echo "AC-13: moved imported STL, cache returned the old render: $o" >&2; fail=1; }
mk 0
cat > assembly.scad <<'S'
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
module side(tilt) { echo(UB_TILT = tilt); }
side(5);                      // right
mirror([1, 0, 0]) side(40);   // left copy swings 40 deg
if (PART == "a") cube([20, 20, 10]);
if (PART == "b") translate([0, 0, 10]) cube([20, 20, 10]);
S
echo '{"bodies":{"a":{"render":[{"MODE":"part","PART":"a"}]},"b":{"render":[{"MODE":"part","PART":"b"}]}},"joints":[{"a":"a","b":"b","max_gap":0.3,"why":"x","angle":{"echo":"UB_TILT","max_deg":15,"source":"datasheet"}}]}' > behavior.json
o=$(python3 "$B" --project-dir . 2>&1); r=$?
[ $r -ne 0 ] && grep -q "40" <<< "$o" || { echo "AC-14: second echo (40 deg) ignored (rc $r): $o" >&2; fail=1; }
exit $fail
