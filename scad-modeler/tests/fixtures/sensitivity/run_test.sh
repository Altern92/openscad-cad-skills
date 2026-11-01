#!/usr/bin/env bash
# P13 (2026-11-01): a part that hard-codes a number instead of using the parameter renders
# fine and passes its bbox at the nominal value. `// SENSITIVE_TO: name` re-renders with
# name x1.5 and fails when the geometry does not change.
set -uo pipefail
C="$SCAD_MODELER_SCRIPTS/check_sensitivity.py"; V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
P="$tmp/p"; mkdir -p "$P/parts" "$P/build"
printf 'wall = 4;\nwidth = 20;\n' > "$P/params.scad"
printf 'include <../params.scad>\n// SENSITIVE_TO: wall\n// SENSITIVE_TO: width\ncube([width, 10, wall]);\n' > "$P/parts/good.scad"
printf 'include <../params.scad>\n// SENSITIVE_TO: wall\ncube([width, 10, 4]);\n' > "$P/parts/bad.scad"
printf 'include <../params.scad>\ncube([width, 10, 4]);\n' > "$P/parts/none.scad"
for n in good bad none; do (cd "$P" && openscad -q -o build/$n.stl parts/$n.scad); done
out=$(cd "$P" && python3 "$C" --scad parts/good.scad --stl build/good.stl 2>&1); [ $? -eq 0 ] || die "good part: not PASS"
out=$(cd "$P" && python3 "$C" --scad parts/bad.scad --stl build/bad.stl 2>&1); rc=$?
[ "$rc" -eq 3 ] || die "hard-coded part: exit $rc, want 3"
echo "$out" | grep -q 'wall' || die "param not named"
out=$(cd "$P" && python3 "$C" --scad parts/none.scad --stl build/none.stl 2>&1); [ $? -eq 0 ] && echo "$out" | grep -q '^SKIP' || die "undeclared: not SKIP"
printf 'include <../params.scad>\n// SENSITIVE_TO: no_such_param\ncube(4);\n' > "$P/parts/typo.scad"; (cd "$P" && openscad -q -o build/typo.stl parts/typo.scad)
out=$(cd "$P" && python3 "$C" --scad parts/typo.scad --stl build/typo.stl 2>&1); [ $? -eq 3 ] || die "unknown param: not FAIL"
# wired: single-file mode reports sensitivity=FAIL
printf '// EXPECTED_BBOX: [20, 10, 4]\n// EXPECTED_THROUGH_HOLES: 0\n' | cat - "$P/parts/bad.scad" > "$P/parts/bad2.scad"
out=$(cd "$P" && bash "$V" parts/bad2.scad 2>&1)
echo "$out" | grep -q '^CHECK_RESULT sensitivity=FAIL' || die "validate: no sensitivity=FAIL"
exit 0
