#!/usr/bin/env bash
# P17a (2026-11-01, external audit): `python3 doctor.py` started by the system python3
# (no trimesh) reported tier 1 while the mesh venv supports tier 2. doctor.py must judge
# the interpreter the checkers actually run with (resolve_python.sh), not its own.
set -uo pipefail
R="$SCAD_MODELER_SCRIPTS/resolve_python.sh"
mesh_py=$(bash "$R" --print)
sys_py=/usr/bin/python3
[ -x "$sys_py" ] || { echo "SKIP: no /usr/bin/python3"; exit 0; }
[ "$mesh_py" != "$sys_py" ] || { echo "SKIP: no separate mesh interpreter"; exit 0; }
tier() { "$1" -c 'import json,sys; print(json.load(sys.stdin)["max_tier"])'; }
clean_path=$(printf '%s' "$PATH" | tr ':' '\n' | grep -v scad-modeler-shim | paste -sd: -)
want=$("$mesh_py" "$SCAD_MODELER_SCRIPTS/doctor.py" --json 2>/dev/null | tier "$mesh_py")
got=$(PATH="$clean_path" "$sys_py" "$SCAD_MODELER_SCRIPTS/doctor.py" --json 2>/dev/null | tier "$mesh_py")
[ "$got" = "$want" ] || { echo "doctor via system python3 says tier $got, mesh interpreter says $want" >&2; exit 1; }
exit 0
