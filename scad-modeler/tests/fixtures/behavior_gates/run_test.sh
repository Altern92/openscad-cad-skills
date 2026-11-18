#!/usr/bin/env bash
# P23 (2026-11-18, INC-2026-11-18-01): assembly behaviour -- holds / moves / stands.
# One project, several behavior.json variants; every gate has a failing case.
set -uo pipefail
B="$SCAD_MODELER_SCRIPTS/check_behavior.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp assembly.scad inc.scad "$tmp/"; cd "$tmp"
G="$OLDPWD/good.json"
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
run() { out=$(python3 "$B" --project-dir . --behavior "$1" "${@:2}" 2>&1); rc=$?; }
edit() { python3 - "$G" "$1" > "$tmp/v.json" <<PY
import json, sys
d = json.load(open(sys.argv[1])); exec(sys.argv[2]); print(json.dumps(d))
PY
}

run "$G"; [ "$rc" -eq 0 ] || die "good: exit $rc, want 0"
echo "$out" | grep -q 'HOLDS: PASS' || die "good: no HOLDS PASS"
echo "$out" | grep -q 'MOVES: PASS' || die "good: no MOVES PASS"
echo "$out" | grep -q 'STANDS: PASS' || die "good: no STANDS PASS"
echo "$out" | grep -q '2 pose' || die "good: pose count not printed"

# AC-1 body in no joint
edit 'd["joints"] = [j for j in d["joints"] if j["b"] != "arm"]'; run v.json; [ "$rc" -eq 3 ] || die "AC-1: exit $rc"
echo "$out" | grep -q "arm.*not held" || die "AC-1: arm not named"
# AC-2 floating arm (the rod end that was never modelled)
run "$G" -D GAP=2; [ "$rc" -eq 3 ] || die "AC-2: exit $rc"
echo "$out" | grep -q "post <-> arm.*gap 2.00" || die "AC-2: gap not reported"
# AC-2b a body of two pieces: the far piece is not held even though the post itself is
run "$G" -D STRAY=5; [ "$rc" -eq 3 ] || die "AC-2b: exit $rc"
echo "$out" | grep -q "post: separate piece" || die "AC-2b: stray piece not named"
run "$G" -D CHAIN=1; [ "$rc" -eq 0 ] || die "AC-2b: piece held through the post rejected (exit $rc)"
# AC-3 gap cap
edit 'd["joints"][1]["max_gap"] = 2.5'; run v.json -D GAP=2; [ "$rc" -eq 3 ] || die "AC-3: exit $rc"
echo "$out" | grep -q "bridges it" || die "AC-3: cap message missing"
# AC-4 detached group: post+arm joined to each other, never to the base standing on the ground
edit 'd["joints"] = d["joints"][1:]'; run v.json; [ "$rc" -eq 3 ] || die "AC-4: exit $rc"
echo "$out" | grep -q "detached.*arm" || die "AC-4: detached group not named"
# AC-7 interference inside the sweep (arm hits the column at A=45 only)
edit 'd["poses"]["A"] = [0, 45]; d["clearance"]["pairs"] = []'; run v.json; [ "$rc" -eq 3 ] || die "AC-7: exit $rc"
echo "$out" | grep -q "arm <-> column.*interfere.*A=45" || die "AC-7: interference not at A=45"
# AC-8 clearance under min at one pose
edit 'd["poses"]["A"] = [0, 30]; d["clearance"]["pairs"][0]["min"] = 50'; run v.json; [ "$rc" -eq 3 ] || die "AC-8: exit $rc"
echo "$out" | grep -q "arm <-> column.*< 50" || die "AC-8: clearance not reported"
# AC-9 ground body off the ground
edit 'd["ground"]["z"] = -8'; run v.json; [ "$rc" -eq 3 ] || die "AC-9: exit $rc"
echo "$out" | grep -q "foot.*ground" || die "AC-9: not named"
# AC-9b ground.at that matches no pose is a FAIL, never a vacuous pass
edit 'd["ground"]["at"] = {"A": 99}'; run v.json; [ "$rc" -eq 3 ] || die "AC-9b: exit $rc"
echo "$out" | grep -q "matches no pose" || die "AC-9b: not reported"
edit 'd["ground"]["at"] = {"A": 0}; d["ground"]["z"] = -8'; run v.json; [ "$rc" -eq 3 ] || die "AC-9c: ground.at pose not checked"
# AC-10 mass centre outside the support (a 5x5 foot under one corner of the 40x40 base)
run "$G" -D FOOT=5; [ "$rc" -eq 3 ] || die "AC-10: exit $rc"
echo "$out" | grep -q "mass centre.*outside" || die "AC-10: not reported"
# AC-11 usage errors
edit 'd["joints"][0]["a"] = "nope"'; run v.json; [ "$rc" -eq 4 ] || die "AC-11 unknown body: exit $rc"
echo '{' > bad.json; run bad.json; [ "$rc" -eq 4 ] || die "AC-11 bad json: exit $rc"
# cached renders follow an included file: lifting the arm there must re-render and FAIL
echo 'GAP0 = 2;' > inc.scad; run "$G"; [ "$rc" -eq 3 ] || die "cache: include change not seen (exit $rc)"
echo 'GAP0 = 0;' > inc.scad
# AC-11 wiring: validate_scad.sh reports the gate (FAIL here: the floating arm via a broken joint)
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
cp "$G" behavior.json; out=$(bash "$V" --all 2>&1)
echo "$out" | grep -q '^CHECK_RESULT behavior=PASS' || die "validate: no behavior=PASS"
edit 'd["joints"][1]["max_gap"] = 5'; cp v.json behavior.json; out=$(bash "$V" --all 2>&1)
echo "$out" | grep -q '^CHECK_RESULT behavior=FAIL' || die "validate: no behavior=FAIL"
rm behavior.json; out=$(bash "$V" --all 2>&1)
echo "$out" | grep -q '^CHECK_RESULT behavior=SKIP' || die "validate: no behavior=SKIP"
exit 0
