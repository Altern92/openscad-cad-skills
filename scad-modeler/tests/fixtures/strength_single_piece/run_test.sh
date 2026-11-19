#!/usr/bin/env bash
# P26 / AC-8, AC-9 (Fable audit e9). Every section piece within `reach` was unioned into one beam, so an
# unloaded sibling prong 25 mm away "carried" the load (356 -> 5 MPa), and stations ran 5-95 %, so a bar
# stopping 4.5 mm short of both ends passed. A bare-list fasteners.json crashed the gate (AttributeError).
set -uo pipefail
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; mkdir -p "$tmp/build/positioned"
python3 - "$tmp/build/positioned" <<'PY'
import sys, trimesh
d = sys.argv[1]
box = lambda lo, hi: trimesh.creation.box(bounds=[lo, hi])
rod = box([0, -1, -1], [30, 1, 1])
rod.export(f"{d}/rod.stl")
# unloaded prong 25 mm ABOVE the rod (parallel-axis term makes a unioned section look stiff), joined at the root
trimesh.boolean.union([rod, box([0, -1, 24], [30, 1, 26]), box([-3, -1, -1], [0.5, 1, 26])]).export(f"{d}/fork.stl")
box([4.5, -1, -1], [95.5, 1, 1]).export(f"{d}/short.stl")   # 100 mm span: the 5 % station (5 mm) landed on it
PY
cd "$tmp"; fail=0
cp build/positioned/rod.stl build/positioned/rod_l.stl   # AC-3b: a mirror copy must not make "rod" ambiguous
case_() { printf '{"name":"%s","part":"%s","support":[0,0,0],"at":[%s,0,0],"force_N":[0,0,-%s],"material":"PETG Basic"}' "$1" "$2" "$3" "$4"; }
echo "{\"cases\":[$(case_ rod rod 30 5),$(case_ fork fork 30 5),$(case_ short short 100 0.01)]}" > loads.json
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir . 2>&1); r=$?
grep -q <<< "$o" "matches 2" && { echo "AC-3b: part name rod matched its copy rod_l: $o" >&2; fail=1; }
grep -q <<< "$o" "FAIL load rod" || { echo "baseline: lone 2x2 rod should fail: $o" >&2; fail=1; }
grep -q <<< "$o" "FAIL load fork" || { echo "AC-8: sibling prong carried the load: $(grep fork <<< "$o")" >&2; fail=1; }
grep -A1 "FAIL load short" <<< "$o" | grep -q "no material" || { echo "AC-8: bar short of both ends passed: $(grep -A1 short <<< "$o")" >&2; fail=1; }
rm loads.json; echo '[{"name":"s","start":[0,0,0],"axis":[0,0,-1],"d":3,"length":5}]' > fasteners.json
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir . 2>&1); r=$?
! grep -q <<< "$o" "Traceback" && [ $r -eq 2 ] || { echo "AC-9: bare-list fasteners.json (rc $r): $o" >&2; fail=1; }
exit $fail
