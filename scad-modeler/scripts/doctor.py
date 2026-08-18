#!/usr/bin/env python3
"""Detect what this machine can actually do, instead of asserting paths.

Why this exists
---------------
Both skills used to state machine-specific facts as if they were universal --
"a full BOSL2 is installed at ~/Documents/OpenSCAD/libraries/BOSL2", "a working
gridfinity clone exists at Docs/03_.../". On any other machine, or after any
reinstall, those lines are confidently wrong, and an agent reading them will
build on a false premise.

Worse, a directory existing under the right name is not evidence a library
works. This exact trap is on record in references/setup-notes.md: a folder named
`BOSL2` once contained a single stray `gears.scad`, `include <BOSL2/std.scad>`
failed to resolve, and the failure only surfaced mid-render. So every library
here is checked by looking for the entry-point file it must have, not by
checking the folder exists.

Run this before trusting anything environmental, and re-run it after changing
machines. The output also states the highest confidence tier the environment
can support -- see openscad-cad/references/confidence-tiers.md.

Usage:
    python3 doctor.py             # human-readable report
    python3 doctor.py --json      # machine-readable, for scripting

Exit codes:
    0  everything needed for full validation is present
    2  degraded -- core works, some checks unavailable (says which)
    3  missing something critical (no OpenSCAD at all)
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys

EXIT_OK, EXIT_DEGRADED, EXIT_CRITICAL = 0, 2, 3

# Library -> the file that must exist for it to be a real, working install.
# Checking the folder alone is what let a one-file fake BOSL2 pass before.
LIBRARIES = {
    "BOSL2": "std.scad",
    "MCAD": "involute_gears.scad",
    "NopSCADlib": "core.scad",
    "Round-Anything": "polyround.scad",
    "dotSCAD": "src/line2d.scad",
}

PY_DEPS = {
    "trimesh": "mesh loading; needed by every STL-side check",
    "shapely": "section contours; needed by check_features.py",
    "scipy": "trimesh's own mesh checks; needed by check_collisions.py",
    "networkx": "trimesh graph ops",
    "manifold3d": "mesh booleans; without it a declared press fit cannot be "
                  "measured against its range",
}


def find_openscad():
    for cand in filter(None, [os.environ.get("OPENSCAD"), "openscad",
                              "openscad-nightly", "OpenSCAD"]):
        path = shutil.which(cand)
        if path:
            return path
    for app in ("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
                "/Applications/OpenSCAD-nightly.app/Contents/MacOS/OpenSCAD"):
        if os.path.isfile(app):
            return app
    return None


def probe_openscad(path):
    info = {"path": path, "version": None, "manifold": False, "summary": False}
    try:
        r = subprocess.run([path, "--version"], capture_output=True, text=True,
                           timeout=30)
        info["version"] = (r.stdout + r.stderr).strip().splitlines()[0] if (
            r.stdout or r.stderr) else None
    except Exception as e:
        info["version"] = f"could not run: {e}"
    try:
        r = subprocess.run([path, "--help"], capture_output=True, text=True,
                           timeout=30)
        helptext = (r.stdout + r.stderr).lower()
        info["manifold"] = "backend" in helptext
        info["summary"] = "--summary" in helptext
        info["summary_options"] = None
        for line in (r.stdout + r.stderr).splitlines():
            if "--summary" in line and "arg" in line:
                info["summary_options"] = line.strip()
                break
    except Exception:
        pass
    return info


def library_search_paths():
    """OpenSCAD's documented library locations, plus OPENSCADPATH."""
    paths = []
    env = os.environ.get("OPENSCADPATH")
    if env:
        paths += [p for p in env.split(os.pathsep) if p]
    home = os.path.expanduser("~")
    system = platform.system()
    if system == "Darwin":
        paths.append(os.path.join(home, "Documents", "OpenSCAD", "libraries"))
    elif system == "Windows":
        paths.append(os.path.join(home, "Documents", "OpenSCAD", "libraries"))
    else:
        paths += [os.path.join(home, ".local", "share", "OpenSCAD", "libraries"),
                  "/usr/share/openscad/libraries"]
    return [p for p in paths if os.path.isdir(p)]


def check_libraries():
    roots = library_search_paths()
    found = {}
    for name, marker in LIBRARIES.items():
        entry = {"status": "missing", "path": None, "note": ""}
        for root in roots:
            d = os.path.join(root, name)
            if not os.path.isdir(d):
                continue
            entry["path"] = d
            if os.path.isfile(os.path.join(d, marker)):
                n = sum(len([f for f in fs if f.endswith(".scad")])
                        for _, _, fs in os.walk(d))
                entry["status"] = "ok"
                entry["note"] = f"{n} .scad files"
            else:
                entry["status"] = "incomplete"
                entry["note"] = (f"directory exists but {marker} is missing -- "
                                 f"this is NOT a working install")
            break
        found[name] = entry
    return roots, found


def check_python_deps():
    out = {}
    for mod, why in PY_DEPS.items():
        try:
            __import__(mod)
            out[mod] = {"status": "ok", "why": why}
        except Exception:
            out[mod] = {"status": "missing", "why": why}
    if out.get("trimesh", {}).get("status") == "ok":
        try:
            from trimesh.collision import CollisionManager  # noqa: F401
            out["python-fcl"] = {"status": "ok",
                                 "why": "collision detection behind trimesh"}
        except Exception:
            out["python-fcl"] = {"status": "missing",
                                 "why": "collision detection behind trimesh"}
    return out


def find_calibration():
    for cand in ("printer_profile.json",
                 os.path.join("calibration", "printer_profile.json"),
                 os.path.expanduser("~/.config/openscad-skills/printer_profile.json")):
        if os.path.isfile(cand):
            return cand
    return None


def highest_tier(scad, deps, calib):
    """See openscad-cad/references/confidence-tiers.md."""
    if not scad:
        return 0, "no OpenSCAD binary -- nothing can be rendered or exported"
    if deps.get("trimesh", {}).get("status") != "ok":
        return 1, "trimesh missing -- no dimensional check is possible"
    feature_ok = deps.get("shapely", {}).get("status") == "ok"
    if not feature_ok:
        return 2, "shapely missing -- bores cannot be measured, envelope only"
    if not calib:
        return 2, ("no calibration profile -- fits cannot be promised, only "
                   "geometry")
    if deps.get("python-fcl", {}).get("status") != "ok":
        return 3, "python-fcl missing -- assemblies cannot be checked"
    return 4, "static assembly checking available; motion sweep not implemented"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    scad_path = find_openscad()
    scad = probe_openscad(scad_path) if scad_path else None
    roots, libs = check_libraries()
    deps = check_python_deps()
    calib = find_calibration()
    headless = (platform.system() == "Linux" and not os.environ.get("DISPLAY"))
    xvfb = shutil.which("xvfb-run")
    tier, tier_why = highest_tier(scad, deps, calib)

    report = {"openscad": scad, "library_roots": roots, "libraries": libs,
              "python": deps, "calibration_profile": calib,
              "headless_linux": headless, "xvfb_run": xvfb,
              "max_tier": tier, "max_tier_reason": tier_why}

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("OpenSCAD")
        if scad:
            print(f"  path      {scad['path']}")
            print(f"  version   {scad['version']}")
            print(f"  Manifold  {'yes' if scad['manifold'] else 'no (older build)'}")
            print(f"  --summary {'yes' if scad['summary'] else 'no'}"
                  + (f"  [{scad['summary_options']}]" if scad.get("summary_options") else ""))
        else:
            print("  NOT FOUND -- install it before anything else.")
            print("  macOS: brew install --cask openscad@snapshot")
            print("  Debian/Ubuntu: sudo apt-get install -y openscad")

        if headless:
            print(f"\nHeadless Linux: PNG renders need xvfb-run "
                  f"({'found' if xvfb else 'MISSING -- apt-get install -y xvfb'})")

        print("\nLibraries" + (f"  (searched: {', '.join(roots)})" if roots
                               else "  (no OpenSCAD library directory found)"))
        for name, e in libs.items():
            mark = {"ok": "ok      ", "incomplete": "INCOMPLETE",
                    "missing": "-       "}[e["status"]]
            print(f"  {mark} {name:<16}{e['note'] or ''}")
            if e["status"] == "incomplete":
                print(f"           at {e['path']}")

        print("\nPython packages")
        for mod, e in deps.items():
            print(f"  {'ok      ' if e['status'] == 'ok' else 'MISSING '} "
                  f"{mod:<14}{e['why']}")

        print(f"\nCalibration profile: {calib or 'none -- fits are uncalibrated'}")
        print(f"\nHighest supportable tier: {tier} -- {tier_why}")

    if not scad:
        return EXIT_CRITICAL
    degraded = any(e["status"] != "ok" for e in deps.values()) or \
        any(e["status"] == "incomplete" for e in libs.values()) or \
        (headless and not xvfb)
    return EXIT_DEGRADED if degraded else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
