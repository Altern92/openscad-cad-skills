#!/usr/bin/env bash
# P2 / AC-6 and P12 / AC-11 (2026-11-01): both new checks run inside the one
# validation path, report a CHECK_RESULT line and decide the verdict.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
plate='$fn=48; difference(){ cube([40,20,5]); for (x=[10,30]) translate([x,10,-1]) cylinder(d=5,h=7); }'
mkdir -p "$tmp/ok" "$tmp/std" "$tmp/holes" "$tmp/proj/parts"
printf '// EXPECTED_THROUGH_HOLES: 2\npitch_1u = 44.45;\n%s\n' "$plate" > "$tmp/ok/plate.scad"
printf 'unit_1U = 44.5;\n%s\n' "$plate" > "$tmp/std/plate.scad"
printf '// EXPECTED_THROUGH_HOLES: 3\n%s\n' "$plate" > "$tmp/holes/plate.scad"
printf 'unit_1U = 44.5;\n' > "$tmp/proj/params.scad"
printf '// EXPECTED_THROUGH_HOLES: 2\n%s\n' "$plate" > "$tmp/proj/parts/plate.scad"

out=$(cd "$tmp/ok" && bash "$V" plate.scad 2>&1); rc=$?
[ "$rc" -eq 0 ] || die "single ok: exit $rc"
echo "$out" | grep -q '^CHECK_RESULT scad_lint=PASS' || die "AC-6: no scad_lint=PASS"
echo "$out" | grep -q '^CHECK_RESULT topology=PASS' || die "AC-11: no topology=PASS"

out=$(cd "$tmp/std" && bash "$V" plate.scad 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "AC-6 single: exit $rc, want 1"
echo "$out" | grep -q '^CHECK_RESULT scad_lint=FAIL' || die "AC-6 single: no scad_lint=FAIL"
echo "$out" | grep -q '^CHECK_RESULT topology=SKIP' || die "AC-11: undeclared part not topology=SKIP"

out=$(cd "$tmp/holes" && bash "$V" plate.scad 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "AC-11 single: exit $rc, want 1"
echo "$out" | grep -q '^CHECK_RESULT topology=FAIL' || die "AC-11: no topology=FAIL"

out=$(cd "$tmp/proj" && bash "$V" --all 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "AC-6 --all: exit $rc, want 1"
echo "$out" | grep -q '^CHECK_RESULT scad_lint=FAIL' || die "AC-6 --all: no scad_lint=FAIL"
echo "$out" | grep -q '^CHECK_RESULT topology=PASS' || die "AC-11 --all: no topology=PASS"
exit 0
