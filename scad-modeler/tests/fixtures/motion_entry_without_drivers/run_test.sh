#!/usr/bin/env bash
# 2026-11-01: a motion entry written as {"part", "axis", "pivot"} (no "drivers") crashed
# motion_sweep.py with KeyError: 'drivers'. mechanics was FAIL, but the only explanation was
# a traceback, so agents read the script's source to learn the format. The failure must name
# the missing field and show the expected shape, without a traceback.
set -uo pipefail
M="$SCAD_MODELER_SCRIPTS/motion_sweep.py"
. "$SCAD_MODELER_SCRIPTS/resolve_python.sh"
PY=$(bash "$SCAD_MODELER_SCRIPTS/resolve_python.sh" --print)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
printf 'cube(5);' > a.scad; openscad -o a.stl a.scad >/dev/null 2>&1
cp a.stl b.stl
echo '{"contacts": [], "motion": [{"part": "b", "axis": [1,0,0], "pivot": [0,0,5], "range_deg": [0, 90]}]}' > joints.json
out=$("$PY" "$M" --joints joints.json a.stl b.stl 2>&1); rc=$?
[ "$rc" -ne 0 ] || { echo "malformed motion entry exited 0" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q Traceback && { echo "malformed motion entry still crashes:" >&2; echo "$out" | tail -3 >&2; exit 1; }
echo "$out" | grep -q '"drivers"' || { echo "message does not name the missing \"drivers\" field" >&2; echo "$out" >&2; exit 1; }
exit 0
