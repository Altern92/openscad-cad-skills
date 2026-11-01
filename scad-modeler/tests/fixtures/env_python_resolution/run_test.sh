#!/usr/bin/env bash
# P1 / AC-1, AC-2 (2026-11-01): the checks must run under the interpreter that
# HAS the mesh libraries, not whatever `python3` the agent's shell happens to
# find. On the mini /usr/bin/python3 has no trimesh, and validate_scad.sh then
# reported connectivity=FAIL / mechanics=FAIL -- a missing module dressed up as
# a geometry failure. Order: SCAD_PYTHON > ~/.local/share/scad-modeler/venv > python3.
set -uo pipefail
R="$SCAD_MODELER_SCRIPTS/resolve_python.sh"
[ -f "$R" ] || { echo "missing $R" >&2; exit 1; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/a" "$tmp/home/.local/share/scad-modeler/venv/bin"
printf '#!/bin/sh\necho fake-a\n' > "$tmp/a/python"; chmod +x "$tmp/a/python"
printf '#!/bin/sh\necho fake-venv\n' > "$tmp/home/.local/share/scad-modeler/venv/bin/python"
chmod +x "$tmp/home/.local/share/scad-modeler/venv/bin/python"

# AC-2: SCAD_PYTHON wins over the venv
got=$(SCAD_PYTHON="$tmp/a/python" HOME="$tmp/home" bash "$R" --print)
[ "$got" = "$tmp/a/python" ] || { echo "AC-2: expected $tmp/a/python, got '$got'" >&2; exit 1; }

# AC-1: no SCAD_PYTHON -> the standard venv
got=$(env -u SCAD_PYTHON HOME="$tmp/home" bash "$R" --print)
[ "$got" = "$tmp/home/.local/share/scad-modeler/venv/bin/python" ] || { echo "AC-1: expected venv, got '$got'" >&2; exit 1; }

# AC-1: once sourced, a bare `python3` (what every caller uses) IS that interpreter
got=$(env -u SCAD_PYTHON HOME="$tmp/home" bash -c ". '$R' && python3")
[ "$got" = "fake-venv" ] || { echo "AC-1: sourced python3 ran '$got', not the venv" >&2; exit 1; }

# a REAL venv must stay a venv through the shim: a symlinked venv python in
# another directory loses pyvenv.cfg and silently falls back to the base
# interpreter's site-packages (caught 2026-11-01: trimesh "missing" again)
/usr/bin/env python3 -m venv "$tmp/realvenv" || { echo "cannot create venv" >&2; exit 1; }
got=$(SCAD_PYTHON="$tmp/realvenv/bin/python" bash -c ". '$R' && python3 -c 'import sys; print(sys.prefix)'")
want=$(cd "$tmp/realvenv" && pwd -P)
[ "$(cd "$got" 2>/dev/null && pwd -P)" = "$want" ] || { echo "real venv: sys.prefix '$got', want $want" >&2; exit 1; }

# the shim must REPLACE whatever sits at shim/python3, never write through it.
# 2026-11-01: an older shim left python3 as a symlink to the venv python; the
# next run's `printf > shim/python3` followed it and overwrote uv's CPython
# binary with the wrapper -> every uv tool on the machine looped forever.
printf 'SENTINEL' > "$tmp/sentinel"
TMPDIR="$tmp/t" SCAD_PYTHON="$tmp/a/python" bash -c ". '$R'" ; mkdir -p "$tmp/t"
TMPDIR="$tmp/t" SCAD_PYTHON="$tmp/a/python" bash -c ". '$R'"
shim=$(ls -d "$tmp/t"/scad-modeler-shim-* | head -1)
rm -f "$shim/python3"; ln -s "$tmp/sentinel" "$shim/python3"
TMPDIR="$tmp/t" SCAD_PYTHON="$tmp/a/python" bash -c ". '$R'"
[ "$(cat "$tmp/sentinel")" = "SENTINEL" ] || { echo "shim wrote THROUGH a symlink into its target" >&2; exit 1; }
[ ! -L "$shim/python3" ] || { echo "shim/python3 is still a symlink" >&2; exit 1; }

# neither -> plain python3 from PATH
got=$(env -u SCAD_PYTHON HOME="$tmp/empty" bash "$R" --print)
[ "$got" = "$(command -v python3)" ] || { echo "fallback: expected $(command -v python3), got '$got'" >&2; exit 1; }
exit 0
