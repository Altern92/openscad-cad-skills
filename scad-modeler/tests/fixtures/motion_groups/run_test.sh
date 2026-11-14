#!/usr/bin/env bash
# P21 (INC-2026-11-13-04/-05): a group driver ("parts": [...]) moves every listed part together.
# Sensor in the carriage path -> FAIL naming the pair; sensor beside the path -> PASS with the
# worst clearance and its pair printed.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
mkdir "$t/in" "$t/out"
python3 "$here/make_stls.py" "$t/in" in || exit 1
python3 "$here/make_stls.py" "$t/out" out || exit 1
o1=$(python3 "$SCAD_MODELER_SCRIPTS/motion_sweep.py" --joints "$here/joints_ok.json" "$t"/in/*.stl 2>&1); r1=$?
o2=$(python3 "$SCAD_MODELER_SCRIPTS/motion_sweep.py" --joints "$here/joints_ok.json" "$t"/out/*.stl 2>&1); r2=$?
[ "$r1" -eq 3 ] || { echo "sensor in path: expected exit 3, got $r1"; echo "$o1"; exit 1; }
echo "$o1" | grep -q "home_sensor" || { echo "FAIL report does not name home_sensor"; echo "$o1"; exit 1; }
echo "$o1" | grep -q "carriage_block" || { echo "FAIL report does not name carriage_block"; echo "$o1"; exit 1; }
[ "$r2" -eq 0 ] || { echo "sensor beside path: expected exit 0, got $r2"; echo "$o2"; exit 1; }
echo "$o2" | grep -q "worst clearance .* home_sensor" || { echo "PASS report lacks worst clearance pair"; echo "$o2"; exit 1; }
exit 0
