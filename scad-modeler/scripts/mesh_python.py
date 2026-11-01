"""Re-run a checker under the scad-modeler interpreter when a dependency import fails.

validate_scad.sh and check_rules.py pick the interpreter via resolve_python.sh; a checker
run directly with the system python3 did not, and told the user to `pip install` into
the wrong Python although the venv existed (S-5, GenKit audit 2026-11-01). Same order as
resolve_python.sh: $SCAD_PYTHON, then ~/.local/share/scad-modeler/venv/bin/python.
"""
import os
import sys


def reexec():
    """Call from an ImportError guard. Returns only if there is nothing better to run."""
    venv = os.path.expanduser("~/.local/share/scad-modeler/venv/bin/python")
    py = os.environ.get("SCAD_PYTHON") or (venv if os.access(venv, os.X_OK) else None)
    if not py or os.environ.get("SCAD_MESH_REEXEC") == "1":
        return
    os.environ["SCAD_MESH_REEXEC"] = "1"   # never loop if that interpreter lacks it too
    os.execv(py, [py] + sys.argv)
