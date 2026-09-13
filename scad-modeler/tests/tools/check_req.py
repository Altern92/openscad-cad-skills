#!/usr/bin/env python3
"""check_req.py -- does a built part satisfy the requirements it was given?

Usage: check_req.py <requirements.json> <run_dir> [part_name]

Why this exists instead of a mesh diff. A prose spec cannot pin a whole mesh:
asked to recreate a 4 KB mechanical part from a 15-line brief, agents produce
structurally different but defensible geometry, so "does the mesh match" scores
0/4 even for parts that satisfy every stated requirement. Grading the stated
requirements instead is achievable, and it is what the skill's own checks verify.

requirements.json, one entry per part:

  {
    "jackshaft": {"bbox": [33.595, 33.595, 46.0], "bodies": 1, "hole": true}
  }

  bbox   -- required X/Y/Z extent in mm (tolerance below)
  bodies -- required connected-component count (1 = must be one solid piece)
  hole   -- true if the part must declare // EXPECTED_HOLE

<run_dir> is searched recursively for <part>.stl and <part>.scad; _probe files
are ignored. Exit 0 only if every requirement passes for every part.
"""
import glob
import json
import os
import re
import sys

BBOX_ABS = 0.5     # mm
BBOX_REL = 0.02    # or 2%, whichever is larger
PART_FILE = "{}.scad"


def find(run_dir, part, ext):
    hits = [p for p in glob.glob(os.path.join(run_dir, "**", "*." + ext), recursive=True)
            if "_probe" not in os.path.basename(p)]
    for p in hits:
        if os.path.basename(p) == "{}.{}".format(part, ext):
            return p
    return None


def check(run_dir, part, req):
    try:
        import trimesh
    except ImportError:
        return False, "trimesh not installed"

    stl = find(run_dir, part, "stl")
    if stl is None:
        return False, "R1 no STL produced"
    try:
        mesh = trimesh.load(stl, force="mesh")
    except Exception as exc:                                  # noqa: BLE001
        return False, "R1 STL unreadable (%s)" % str(exc)[:40]

    fails = []
    ext = [float(x) for x in mesh.bounds[1] - mesh.bounds[0]]
    for i, ax in enumerate("XYZ"):
        tol = max(BBOX_ABS, BBOX_REL * req["bbox"][i])
        if abs(ext[i] - req["bbox"][i]) > tol:
            fails.append("R2 %s %.3f vs %.3f (tol %.3f)" % (ax, ext[i], req["bbox"][i], tol))

    bodies = len(mesh.split(only_watertight=False))
    if "bodies" in req and bodies != req["bodies"]:
        fails.append("R3 bodies %d vs %d" % (bodies, req["bodies"]))

    src = find(run_dir, part, "scad")
    text = open(src, encoding="utf-8").read() if src else ""
    if not re.search(r"^\s*//\s*EXPECTED_BBOX", text, re.M):
        fails.append("R4 no // EXPECTED_BBOX declared")
    if req.get("hole") and not re.search(r"^\s*//\s*EXPECTED_HOLE", text, re.M):
        fails.append("R5 no // EXPECTED_HOLE declared")

    return not fails, "; ".join(fails) if fails else "all requirements met"


def main():
    if len(sys.argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    reqs = json.load(open(sys.argv[1], encoding="utf-8"))
    run_dir = sys.argv[2]
    only = sys.argv[3:]

    parts = only or sorted(reqs)
    print("%-20s %-10s %s" % ("part", "verdict", "what differs"))
    print("-" * 78)
    ok = 0
    for part in parts:
        if part not in reqs:
            print("%-20s %-10s %s" % (part, "SKIP", "not in requirements.json"))
            continue
        passed, why = check(run_dir, part, reqs[part])
        ok += passed
        print("%-20s %-10s %s" % (part, "OK" if passed else "DIFFERS", why))
    print()
    print("MET: %d / %d" % (ok, len(parts)))
    return 0 if ok == len(parts) else 1


if __name__ == "__main__":
    sys.exit(main())
