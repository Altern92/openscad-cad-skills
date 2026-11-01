#!/usr/bin/env bash
# Pick the Python that has the mesh libraries (P1, 2026-11-01).
# Order: $SCAD_PYTHON > ~/.local/share/scad-modeler/venv/bin/python > python3 on PATH.
#
#   . resolve_python.sh          sets SCAD_PY and puts a `python3` shim for it first on PATH,
#                                so every existing `python3 "$SCRIPT_DIR/check_*.py"` call uses it
#   bash resolve_python.sh --print   prints the chosen interpreter
#
# The venv lives outside the repo so the deployed skill (~/.claude/skills -> ~/Skills-plugins-etc)
# and other machines find it too. Create it with scripts/setup_env.sh.

_scad_venv_py="$HOME/.local/share/scad-modeler/venv/bin/python"
if [ -n "${SCAD_PYTHON:-}" ]; then
    SCAD_PY="$SCAD_PYTHON"
elif [ -x "$_scad_venv_py" ]; then
    SCAD_PY="$_scad_venv_py"
else
    SCAD_PY="$(command -v python3)"
fi

if [ "${1:-}" = "--print" ]; then
    echo "$SCAD_PY"
elif [ "$SCAD_PY" != "$(command -v python3)" ]; then
    # one shim dir per interpreter path, so two interpreters never share a shim
    _scad_shim="${TMPDIR:-/tmp}/scad-modeler-shim-$(id -u)-$(printf '%s' "$SCAD_PY" | cksum | cut -d' ' -f1)"
    mkdir -p "$_scad_shim"
    # exec wrapper, not a symlink: a symlinked venv python loses its pyvenv.cfg and its packages
    # temp file + mv REPLACES a stale symlink; `> python3` would write through it into the real interpreter
    printf '#!/bin/sh\nexec "%s" "$@"\n' "$SCAD_PY" > "$_scad_shim/python3.$$"
    chmod +x "$_scad_shim/python3.$$"
    mv -f "$_scad_shim/python3.$$" "$_scad_shim/python3"
    ln -sf python3 "$_scad_shim/python"
    PATH="$_scad_shim:$PATH"
    export PATH SCAD_PY
fi
unset _scad_venv_py _scad_shim
