#!/usr/bin/env bash
# P8 agent eval (2026-11-01): a one-part project whose assembly only places that part
# was failed as "MODE/PART switch did not take effect" -- with one part, part bbox ==
# assembly bbox is correct, not a broken switch. The tripwire must still fire for 2+ parts.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" | tail -30 >&2; exit 1; }
P="$tmp/p"; mkdir -p "$P/parts"
printf '// EXPECTED_BBOX: [20, 10, 4]\n// EXPECTED_THROUGH_HOLES: 0\nmodule a() { cube([20, 10, 4]); }\na();\n' > "$P/parts/a.scad"
cat > "$P/assembly.scad" <<'S'
use <parts/a.scad>
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
module place(n) { if (n == "a") translate([0, 0, 20]) rotate([180, 0, 0]) a(); else assert(false); }
if (MODE == "assembly") place("a"); else place(PART);
S
out=$(cd "$P" && bash "$V" --all 2>&1)
echo "$out" | grep -q "MODE/PART switch did not take effect" && die "single part: tripwire fired"
echo "$out" | grep -q '^CHECK_RESULT mechanics=FAIL' && die "single part: mechanics=FAIL"
echo "$out" | grep -q '^CHECK_RESULT collisions=SKIP' || die "single part: collisions not SKIP (nothing to collide with)"
# two parts and a switch that ignores -D: still caught
printf '// EXPECTED_BBOX: [20, 10, 4]\n// EXPECTED_THROUGH_HOLES: 0\nmodule b() { cube([20, 10, 4]); }\nb();\n' > "$P/parts/b.scad"
printf '{"contacts": [{"pair": ["a", "b"], "joint_type": "glued"}]}\n' > "$P/joints.json"
cat > "$P/assembly.scad" <<'S'
use <parts/a.scad>
use <parts/b.scad>
MODE = "assembly";
a(); translate([0, 0, 4]) b();
S
out=$(cd "$P" && bash "$V" --all 2>&1)
echo "$out" | grep -q "MODE/PART switch did not take effect" || die "two parts, broken switch: tripwire silent"
exit 0
