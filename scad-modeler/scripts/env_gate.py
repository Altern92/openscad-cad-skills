#!/usr/bin/env python3
"""Environment gate for validate_scad.sh (P1, 2026-11-01).

Runs BEFORE any check. Without the mesh libraries, OpenSCAD, or a library the
project includes, every later CHECK_RESULT is a statement about the tools, not
the geometry -- on the mini that showed up as connectivity=FAIL, mechanics=FAIL
and render=FAIL ("Can't find include file BOSL2/std.scad"). So: one verdict,
the reason, the fix, and stop.

Usage: env_gate.py [--project-dir .] [--openscad openscad]
Prints `ENV python=<interpreter>` and `CHECK_RESULT env=PASS|FAIL`.
Exit: 0 pass, 5 fail. Stdlib only (it must run under an interpreter that has nothing).
"""
import argparse
import glob
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doctor  # noqa: E402

EXIT_OK, EXIT_ENV = 0, 5
INCLUDE_RE = re.compile(r'^\s*(?:include|use)\s*<\s*([^/>]+)/', re.M)


def included_libraries(project_dir):
    """{library: first .scad file that includes it}, only for libraries doctor knows."""
    found = {}
    for f in sorted(glob.glob(os.path.join(project_dir, "**", "*.scad"), recursive=True)):
        if f"{os.sep}build{os.sep}" in f:
            continue
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for lib in INCLUDE_RE.findall(text):
            if lib in doctor.LIBRARIES and lib not in found:
                found[lib] = os.path.relpath(f, project_dir)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--openscad", default=os.environ.get("OPENSCAD", "openscad"))
    a = ap.parse_args()
    scripts = os.path.dirname(os.path.abspath(__file__))
    print(f"ENV python={sys.executable}")

    problems = []
    missing = [m for m, d in doctor.check_python_deps().items() if d["status"] != "ok"]
    if missing:
        problems.append(f"Python modules missing in {sys.executable}: {', '.join(missing)}\n"
                        f"  fix: bash {scripts}/setup_env.sh   (or set SCAD_PYTHON to an interpreter that has them)")
    if not shutil.which(a.openscad):
        problems.append(f"OpenSCAD not found ({a.openscad})\n"
                        f"  fix: install OpenSCAD and put it on PATH, or set OPENSCAD=/path/to/openscad")
    _, libs = doctor.check_libraries()
    for lib, scad in included_libraries(a.project_dir).items():
        if libs[lib]["status"] != "ok":
            problems.append(f"library {lib} is included by {scad} but is {libs[lib]['status']}"
                            f" ({libs[lib]['note'] or 'not in any OpenSCAD library path'})\n"
                            f"  fix: install {lib} into ~/Documents/OpenSCAD/libraries (macOS) or set OPENSCADPATH")

    if problems:
        print("CHECK_RESULT env=FAIL")
        for p in problems:
            print("ENV_FAIL: " + p)
        print("STOP: no check result below would be about the geometry. Fix the environment and re-run.")
        return EXIT_ENV
    print("CHECK_RESULT env=PASS")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
