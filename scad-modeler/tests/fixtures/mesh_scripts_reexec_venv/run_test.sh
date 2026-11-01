#!/usr/bin/env bash
# S-5 (GenKit handoff docs/12; GenKit audit 2026-11-01): run directly with the system
# python3, the mesh checkers printed "trimesh not installed. Run: pip install ..." although
# the scad-modeler venv existed -- validate_scad.sh and check_rules.py resolve it, a direct
# call did not. Each checker must re-exec under the resolved interpreter instead.
set -uo pipefail
S="$SCAD_MODELER_SCRIPTS"
SYS=/usr/bin/python3
[ -x "$SYS" ] || { echo "SKIP: no $SYS"; exit 0; }
"$SYS" -c 'import trimesh' 2>/dev/null && { echo "SKIP: system python3 already has trimesh, nothing to prove"; exit 0; }
[ -x "$(bash "$S/resolve_python.sh" --print)" ] || { echo "no venv interpreter" >&2; exit 1; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
fail=0
for f in check_collisions check_connectivity check_dimensions check_printability check_sensitivity \
         check_proportions check_topology check_subfeature_overlap motion_sweep check_features; do
    [ -f "$S/$f.py" ] || continue
    out=$(cd "$tmp" && env -u SCAD_PY PATH=/usr/bin:/bin "$SYS" "$S/$f.py" --help 2>&1)
    if echo "$out" | grep -qi "not installed"; then echo "$f: still asks for pip under system python3" >&2; fail=1; fi
done
printf 'cube([10,10,2]);' > "$tmp/a.scad"; openscad -q -o "$tmp/a.stl" "$tmp/a.scad"
out=$(cd "$tmp" && env -u SCAD_PY PATH=/usr/bin:/bin:/opt/homebrew/bin "$SYS" "$S/check_printability.py" --stl a.stl 2>&1)
echo "$out" | grep -qi "not installed" && { echo "check_printability real run: still asks for pip" >&2; fail=1; }
exit $fail
