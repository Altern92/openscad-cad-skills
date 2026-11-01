#!/usr/bin/env bash
# Create the interpreter the env gate asks for (P1, 2026-11-01):
#   ~/.local/share/scad-modeler/venv  (override: SCAD_VENV=/path)
# Installs exactly what doctor.py checks, so the gate and this script can't
# disagree about the list. Safe to re-run: an already complete venv is left alone.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V="${SCAD_VENV:-$HOME/.local/share/scad-modeler/venv}"
command -v uv >/dev/null || { echo "ERROR: uv not found. Install it: brew install uv (or https://docs.astral.sh/uv/)" >&2; exit 1; }

missing() {  # modules doctor.py reports as not ok, under the venv interpreter
    "$V/bin/python" "$SCRIPT_DIR/doctor.py" --json 2>/dev/null | "$V/bin/python" -c \
        "import json,sys; print(' '.join(m for m,d in json.load(sys.stdin)['python'].items() if d['status']!='ok'))" || true
}

[ -x "$V/bin/python" ] || uv venv -q --python 3.12 "$V"
if [ -z "$(missing)" ]; then
    echo "already complete: $V"
    exit 0
fi
# doctor.py import names -> pip names; python-fcl is checked only once trimesh imports
pkgs=$("$V/bin/python" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); import doctor; print(' '.join({'yaml': 'pyyaml'}.get(m, m) for m in doctor.PY_DEPS), 'python-fcl')")
# shellcheck disable=SC2086
uv pip install -q --python "$V/bin/python" $pkgs
left=$(missing)
[ -z "$left" ] || { echo "ERROR: still missing after install: $left" >&2; exit 1; }
echo "installed into $V: $pkgs"
echo "validate_scad.sh picks this venv up automatically (no SCAD_PYTHON needed)."
