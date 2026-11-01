#!/usr/bin/env bash
# P15 / AC-9 (2026-11-01, external audit F6): validate_scad.sh's NEXT line said
# `python3 check_rules.py`; started that way, check_rules.py ran its `python3 ...`
# gates with the system interpreter, which has no trimesh -> a false FAIL (R-06).
# Every gate must run with resolve_python.sh sourced, whoever started check_rules.py.
set -uo pipefail
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
sys_py=/usr/bin/python3
[ -x "$sys_py" ] || { echo "SKIP: no /usr/bin/python3"; exit 0; }
"$sys_py" -c 'import yaml' 2>/dev/null || { echo "SKIP: system python3 has no pyyaml"; exit 0; }
if "$sys_py" -c 'import trimesh' 2>/dev/null; then echo "SKIP: system python3 has trimesh, cannot show the bug"; exit 0; fi
cat > "$tmp/m.yaml" <<'Y'
rules:
  - id: R-T
    rule: "gate sees the mesh interpreter"
    applies: "always"
    kind: auto
    gate: "python3 -c 'import trimesh'"
Y
# the suite runner already put the shim first on PATH; a user's shell has none
clean_path=$(printf '%s' "$PATH" | tr ':' '\n' | grep -v scad-modeler-shim | paste -sd: -)
out=$(PATH="$clean_path" "$sys_py" "$SCAD_MODELER_SCRIPTS/check_rules.py" --project-dir "$tmp" --manifest "$tmp/m.yaml" 2>&1); rc=$?
[ "$rc" -eq 0 ] || { echo "gate ran with the system python3 (exit $rc):" >&2; echo "$out" >&2; exit 1; }
exit 0
