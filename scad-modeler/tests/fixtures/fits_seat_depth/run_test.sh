#!/usr/bin/env bash
# P32 (2026-11-28): bearing seat depth. A 7 mm wide bearing in a 7 mm deep O22 seat: OK; in a 5 mm seat (2 mm of the
# outer ring unsupported, sticking out): FAIL "seat"; no seat_depth_mm declared: the depth is not checked.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
C="$SCAD_MODELER_SCRIPTS/check_fits.py"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
mk() { mkdir -p "$t/$1/build/positioned"; python3 "$here/make.py" "$t/$1/build/positioned" "$2" || exit 1
       echo "{\"contacts\": [{\"pair\": [\"bearing\", \"housing\"], \"fit\": {\"peg\": \"bearing\", \"hole\": \"housing\", \"clearance_mm\": 0.02, \"axis\": [0,0,1]$3}}]}" > "$t/$1/joints.json"; }
mk ok 7 ', "at": [0,0,8.5], "seat_depth_mm": 7'; mk short 5 ', "at": [0,0,9.5], "seat_depth_mm": 7'; mk none 5 ', "at": [0,0,9.5]'
o=$(python3 "$C" --project-dir "$t/ok" 2>&1); r=$?
[ $r -eq 0 ] && grep -Eq "seat (6\.9|7\.0)" <<< "$o" || { echo "ok: want exit 0 + 'seat 7.0', got $r"; echo "$o"; exit 1; }
o=$(python3 "$C" --project-dir "$t/short" 2>&1); r=$?
[ $r -eq 3 ] && grep -Eq "FAIL: .*seat (4\.9|5\.0) mm < seat_depth_mm 7" <<< "$o" || { echo "short: want FAIL seat 5.0 < 7, got $r"; echo "$o"; exit 1; }
o=$(python3 "$C" --project-dir "$t/none" 2>&1); r=$?
[ $r -eq 0 ] || { echo "none: want exit 0 (depth not declared), got $r"; echo "$o"; exit 1; }
exit 0
