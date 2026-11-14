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
v=$(cd "$t/p" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" 2>&1)
echo "$v" | grep -q "CHECK_RESULT fasteners=FAIL" || { echo "validate_scad.sh did not run fasteners without assembly.scad"; echo "$v" | grep -i fasten; exit 1; }
exit 0
