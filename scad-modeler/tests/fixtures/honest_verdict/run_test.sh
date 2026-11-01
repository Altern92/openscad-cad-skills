#!/usr/bin/env bash
# P15 (2026-11-01, external audit M4/M5b/M8 re-measured on the mini): a run must not
# say "passed" when the size or the holes were never checked, when a required plan
# is missing, or when a check could not determine its answer.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
cube='cube([20, 10, 5]);'
decl='// EXPECTED_BBOX: [20, 10, 5]\n// EXPECTED_THROUGH_HOLES: 0\n'

# AC-1/AC-2/AC-4: undeclared single part fails and names both lines
mkdir -p "$tmp/bare"; printf '%s\n' "$cube" > "$tmp/bare/p.scad"
out=$(cd "$tmp/bare" && bash "$V" p.scad 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "AC-1: undeclared part exit $rc, want 1"
echo "$out" | grep -q '^CHECK_RESULT declarations=FAIL' || die "AC-1: no declarations=FAIL"
echo "$out" | grep -q 'EXPECTED_BBOX' || die "AC-1: missing line not named"
echo "$out" | grep -q 'EXPECTED_THROUGH_HOLES' || die "AC-2: missing line not named"

# AC-3: empty reason counts as missing
mkdir -p "$tmp/empty"; printf '// NO_BBOX:\n// EXPECTED_THROUGH_HOLES: 0\n%s\n' "$cube" > "$tmp/empty/p.scad"
out=$(cd "$tmp/empty" && bash "$V" p.scad 2>&1); rc=$?
echo "$out" | grep -q '^CHECK_RESULT declarations=FAIL' || die "AC-3: empty NO_BBOX reason accepted"

# AC-3 + AC-8: declared (one by escape with a reason) passes, honest last line
mkdir -p "$tmp/ok"; printf '// NO_BBOX: organic shape, size checked by eye\n// EXPECTED_THROUGH_HOLES: 0\n%s\n' "$cube" > "$tmp/ok/p.scad"
out=$(cd "$tmp/ok" && bash "$V" p.scad 2>&1); rc=$?
[ "$rc" -eq 0 ] || die "AC-3: declared part exit $rc, want 0"
echo "$out" | grep -q '^CHECK_RESULT declarations=PASS' || die "AC-3: no declarations=PASS"
echo "$out" | tail -1 | grep -q '^All executed checks passed (' || die "AC-8: last line not honest"
echo "$out" | grep -q '^All validations passed' && die "AC-8: old claim still printed"

# AC-5: 3 parts, no plan.md -> plan=FAIL; AC-6: no envelope -> SKIP
mkdir -p "$tmp/three/parts"
for n in a b c; do printf "$decl%s\n" "$cube" > "$tmp/three/parts/$n.scad"; done
out=$(cd "$tmp/three" && bash "$V" --all 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "AC-5: 3 parts no plan exit $rc, want 1"
echo "$out" | grep -q '^CHECK_RESULT plan=FAIL' || die "AC-5: no plan=FAIL"
echo "$out" | grep -q '^CHECK_RESULT service_envelope=SKIP' || die "AC-6: envelope not SKIP"
echo "$out" | grep -q '^CHECK_RESULT declarations=PASS' || die "AC-1 --all: no declarations=PASS"

# AC-5: 2 parts, no plan.md -> plan=SKIP, not PASS
rm "$tmp/three/parts/c.scad"
out=$(cd "$tmp/three" && bash "$V" --all 2>&1); rc=$?
echo "$out" | grep -q '^CHECK_RESULT plan=SKIP' || die "AC-5: 2 parts no plan not SKIP"

# AC-7: joints.json declares motion, no assembly.scad -> mechanics INCONCLUSIVE -> exit 2
cat > "$tmp/three/joints.json" <<'J'
{"contacts": [{"pair": ["a", "b"], "joint_type": "bolted"}], "motion": [{"part": "a", "axis": [0,0,1], "pivot": [0,0,0], "range_deg": [0, 90], "step_deg": 30}]}
J
out=$(cd "$tmp/three" && bash "$V" --all 2>&1); rc=$?
echo "$out" | grep -q '^CHECK_RESULT mechanics=INCONCLUSIVE' || die "AC-7 setup: mechanics not INCONCLUSIVE"
[ "$rc" -eq 2 ] || die "AC-7: inconclusive run exit $rc, want 2"
echo "$out" | tail -1 | grep -q '^NOT VERIFIED:' || die "AC-7: last line not NOT VERIFIED"
grep -q '"verdict":"INCONCLUSIVE"' "$tmp/three/build/.validation_state.json" || die "AC-7: state verdict"
exit 0
