#!/usr/bin/env bash
# P27 (Fable calculation audit): AC-3 descending range (bad input = rc 4 here), AC-4 declared contact vs min_clearance, AC-5 teeth shortcut
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; M="$SCAD_MODELER_SCRIPTS/motion_sweep.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"; cp "$here"/*.stl "$here"/*.json .
fail=0
run() { o=$(python3 "$M" --joints "$1" "${@:2}" 2>&1); r=$?; }
run asc.json arm.stl post.stl;  [ $r -ne 0 ] || { echo "baseline: ascending swing should FAIL: $o" >&2; fail=1; }
run desc.json arm.stl post.stl; [ $r -ne 0 ] && grep -q "interference" <<< "$o" \
    || { echo "AC-3: descending range_deg passed (rc $r): $o" >&2; fail=1; }
sed 's/"step_deg": 2/"step_deg": -2/' asc.json > negstep.json
run negstep.json arm.stl post.stl; [ $r -eq 4 ] || { echo "AC-3: negative step_deg not bad input (rc $r): $o" >&2; fail=1; }
cp m2_arm.stl arm2.stl; cp m2_pin.stl pin.stl; cp m2_far.stl far.stl
sed 's/"arm"/"arm2"/g' m2_c3.json > c3.json; sed 's/"arm"/"arm2"/g' m2_c0.json > c0.json
run c0.json arm2.stl pin.stl far.stl; [ $r -eq 0 ] || { echo "baseline: hinge at clearance 0 should pass: $o" >&2; fail=1; }
run c3.json arm2.stl pin.stl far.stl; [ $r -eq 0 ] || { echo "AC-4: declared hinge failed min_clearance 0.3 (rc $r): $o" >&2; fail=1; }
sed 's/"min_clearance_mm": 0.3/"min_clearance_mm": 500/' c3.json > c500.json
run c500.json arm2.stl pin.stl far.stl; [ $r -ne 0 ] || { echo "AC-4: undeclared pair escaped min_clearance: $o" >&2; fail=1; }
cp m3_gear.stl gear.stl; cp m3_post.stl post3.stl; sed 's/"post"/"post3"/' m3_t.json > t.json
run t.json gear.stl post3.stl; [ $r -ne 0 ] || { echo "AC-5: teeth shortcut on an asymmetric part passed: $o" >&2; fail=1; }
exit $fail
