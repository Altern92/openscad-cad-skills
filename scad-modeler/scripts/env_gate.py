#!/usr/bin/env python3
"""Environment gate for validate_scad.sh (P1, 2026-11-01).

Runs BEFORE any check. Without the mesh libraries, OpenSCAD, or a library the
project includes, every later CHECK_RESULT is a statement about the tools, not
the geometry -- on the mini that showed up as connectivity=FAIL, mechanics=FAIL
and render=FAIL ("Can't find include file BOSL2/std.scad"). So: one verdict,
the reason, the fix, and stop.

Library lock (P14, 2026-11-01): BOSL2 2.0.782 dropped worm_gear_thickness(), and
the steering gearbox rendered a wrong output_gear with only a WARNING. A project
`libs.lock` pins each library it includes -- `BOSL2 2.0.750` (version.scad) or
`NopSCADlib tree:<12 hex>` (sha256 of its *.scad files) -- and a different
installed library is env=FAIL. No libs.lock, no version check.

Usage: env_gate.py [--project-dir .] [--openscad openscad] [--write-lock | --libs-json]
Prints `ENV python=<interpreter>` and `CHECK_RESULT env=PASS|FAIL`.
--write-lock writes libs.lock for the libraries the project includes, then gates.
--libs-json prints {"lib": "version"} for included libraries and exits (for the state file).
Exit: 0 pass, 5 fail. Stdlib only (it must run under an interpreter that has nothing).
"""
import argparse
import glob
import hashlib
import json
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


VERSION_RE = re.compile(r"BOSL_VERSION\s*=\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]")


def library_identity(lib, path):
    """'2.0.750' for BOSL2 (its version.scad), else 'tree:<12 hex>' over *.scad paths + contents."""
    if lib == "BOSL2":
        try:
            m = VERSION_RE.search(open(os.path.join(path, "version.scad"), encoding="utf-8").read())
            if m:
                return ".".join(m.groups())
        except OSError:
            pass
    h = hashlib.sha256()
    for f in sorted(glob.glob(os.path.join(path, "**", "*.scad"), recursive=True)):
        h.update(os.path.relpath(f, path).encode() + b"\0")
        with open(f, "rb") as fh:
            h.update(fh.read())
    return "tree:" + h.hexdigest()[:12]


def read_lock(project_dir):
    lock = {}
    try:
        for line in open(os.path.join(project_dir, "libs.lock"), encoding="utf-8"):
            parts = line.split("#")[0].split()
            if len(parts) == 2:
                lock[parts[0]] = parts[1]
    except OSError:
        return None
    return lock


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--openscad", default=os.environ.get("OPENSCAD", "openscad"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write-lock", action="store_true")
    g.add_argument("--libs-json", action="store_true")
    a = ap.parse_args()
    scripts = os.path.dirname(os.path.abspath(__file__))
    _, libs = doctor.check_libraries()
    used = included_libraries(a.project_dir)
    ident = {lib: library_identity(lib, libs[lib]["path"]) for lib in used if libs[lib]["status"] == "ok"}
    if a.libs_json:
        print(json.dumps(ident, separators=(",", ":"), sort_keys=True))
        return EXIT_OK
    if a.write_lock:
        with open(os.path.join(a.project_dir, "libs.lock"), "w", encoding="utf-8") as fh:
            fh.write("# library versions this project was validated with (env_gate.py --write-lock)\n")
            for lib in sorted(ident):
                fh.write(f"{lib} {ident[lib]}\n")
    print(f"ENV python={sys.executable}")

    problems = []
    missing = [m for m, d in doctor.check_python_deps().items() if d["status"] != "ok"]
    if missing:
        problems.append(f"Python modules missing in {sys.executable}: {', '.join(missing)}\n"
                        f"  fix: bash {scripts}/setup_env.sh   (or set SCAD_PYTHON to an interpreter that has them)")
    if not shutil.which(a.openscad):
        problems.append(f"OpenSCAD not found ({a.openscad})\n"
                        f"  fix: install OpenSCAD and put it on PATH, or set OPENSCAD=/path/to/openscad")
    for lib, scad in used.items():
        if libs[lib]["status"] != "ok":
            problems.append(f"library {lib} is included by {scad} but is {libs[lib]['status']}"
                            f" ({libs[lib]['note'] or 'not in any OpenSCAD library path'})\n"
                            f"  fix: install {lib} into ~/Documents/OpenSCAD/libraries (macOS) or set OPENSCADPATH")
    for lib, want in (read_lock(a.project_dir) or {}).items():
        have = ident.get(lib)
        if have is None:
            have = library_identity(lib, libs[lib]["path"]) if libs.get(lib, {}).get("status") == "ok" else "missing"
        if have != want:
            problems.append(f"library {lib} is {have} at {libs.get(lib, {}).get('path')}, but libs.lock wants {want}\n"
                            f"  fix: install {lib} {want} first on the library path (git checkout in the clone), "
                            f"or re-validate and re-lock with --write-lock if the change is intended")

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
