#!/usr/bin/env bash
# P20 F1: the Big_CNC Z motor mount leg had no fastener holes at all (found by the user,
# 2026-11-13). The leg here clears the BK12 heads (reliefs) but no declared screw goes through
# it into the plate: "mounts" must turn that into a FAIL, not a silent PASS.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_mount/make_stls.py" "$t" 1 0 || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$here/fasteners.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -q "mount leg -> plate: no declared fastener" || { echo "missing mount FAIL line"; echo "$o"; exit 1; }
# F4: validate_scad.sh runs the same check on build/positioned without an assembly.scad
mkdir -p "$t/p/build/positioned" && cp "$t"/*.stl "$t/p/build/positioned/" && cp "$here/fasteners.json" "$t/p/"
# one clean part, so fasteners is the ONLY failing gate (an empty parts/ fails on its own and hid
# INC-2026-11-18-08); --all is the mode the projects run
mkdir -p "$t/p/parts" && printf '%s\n' "// NO_BBOX: test block" "// NO_THROUGH_HOLES_CHECK: test block" \
    "// NO_JOINT: test block" "// NO_RETENTION: test block" "cube(4);" > "$t/p/parts/blk.scad"
v=$(cd "$t/p" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all 2>&1); vr=$?
# INC-2026-11-18-08: a gate that failed via log_check only (no OVERALL_FAIL) ended in exit 0 and
# "All executed checks passed" -- the verdict must follow every failed check
[ "$vr" -eq 1 ] || { echo "validate_scad.sh exit $vr with a failed fasteners gate, expected 1"; echo "$v" | tail -5; exit 1; }
echo "$v" | grep -q "All executed checks passed" && { echo "validate_scad.sh claims all passed with fasteners=FAIL"; exit 1; }
echo "$v" | grep -q "CHECK_RESULT fasteners=FAIL" || { echo "validate_scad.sh did not run fasteners without assembly.scad"; echo "$v" | grep -i fasten; exit 1; }
exit 0
