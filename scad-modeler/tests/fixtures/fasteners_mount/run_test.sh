#!/usr/bin/env bash
# P20 F2/F3: STLs from a Python script (no OpenSCAD). Leg with screw holes but no head reliefs
# over the plate's BK12 bolt heads -> head blocked FAIL; with reliefs -> PASS.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
mkdir "$t/a" "$t/b"
python3 "$here/make_stls.py" "$t/a" 0 1 || exit 1
python3 "$here/make_stls.py" "$t/b" 1 1 || exit 1
oa=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$here/fasteners_full.json" "$t"/a/*.stl 2>&1); ra=$?
ob=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$here/fasteners_full.json" "$t"/b/*.stl 2>&1); rb=$?
[ "$ra" -eq 3 ] && grep -q <<< "$oa" "BK12 bolt 1.*" && grep -q <<< "$oa" "head blocked .* by leg" \
    || { echo "no reliefs: expected exit 3 with 'head blocked ... by leg', got $ra"; echo "$oa"; exit 1; }
[ "$rb" -eq 0 ] || { echo "reliefs + holes: expected exit 0, got $rb"; echo "$ob"; exit 1; }
grep -q <<< "$ob" "mount leg -> plate: 2 fastener" || { echo "PASS report lacks the mount line"; echo "$ob"; exit 1; }
exit 0
