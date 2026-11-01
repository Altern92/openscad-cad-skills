#!/usr/bin/env python3
"""Through-hole count from mesh topology (P12, 2026-11-01).

B class, 16 of 95 incidents: a bore that looks right from above but is blind
or sealed by a thin skin. Bbox, connectivity and printability all pass on it.
EvoCAD (arXiv 2510.11631) scores CAD candidates by Euler characteristic; the
same number answers "how many holes go all the way through":

    chi = V - E + F,  genus = (2 * components - chi) / 2

Measured on Manifold renders of a 40x20x5 plate with two d5 bores: both
through chi=-2 genus 2; one sealed chi=0 genus 1; both sealed chi=2 genus 0.
Enclosed cavities are separate shells of genus 0, so they do not change it.

Genus counts handles, not holes: a through-slot or a ring counts 1, two
crossing bores can count more. Declare the topological number:

    // EXPECTED_THROUGH_HOLES: 2

Usage:
    python3 check_topology.py --stl part.stl --scad part.scad

Exit codes:
    0  pass, or SKIP when the .scad declares nothing (never a guess)
    3  fail -- count differs, or the mesh is not watertight (genus undefined)
    4  usage error
"""
import argparse
import os
import re
import sys

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4
DECL_RE = re.compile(r"^\s*//\s*EXPECTED_THROUGH_HOLES\s*:\s*([0-9]+)")

try:
    import trimesh
except ImportError:
    __import__("mesh_python").reexec()
    print("ERROR: trimesh not installed. Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stl", required=True)
    ap.add_argument("--scad", required=True)
    a = ap.parse_args()
    for p in (a.stl, a.scad):
        if not os.path.isfile(p):
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            return EXIT_USAGE

    expected = None
    with open(a.scad, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = DECL_RE.match(line)
            if m:
                expected = int(m.group(1))
                break
    if expected is None:
        print(f"SKIP: topology, {a.scad} declares no // EXPECTED_THROUGH_HOLES: N")
        return EXIT_OK

    try:
        mesh = trimesh.load(a.stl, force="mesh")
    except Exception as e:
        print(f"ERROR: cannot load mesh {a.stl}: {e}", file=sys.stderr)
        return EXIT_USAGE
    if mesh.is_empty:
        print(f"FAIL: topology, {a.stl} is empty")
        return EXIT_FAIL
    if not mesh.is_watertight:
        print(f"FAIL: topology, genus undefined: mesh not watertight ({a.stl}); "
              f"cannot count through-holes on an open surface")
        return EXIT_FAIL

    chi = int(mesh.euler_number)
    bodies = len(mesh.split(only_watertight=False))
    found = (2 * bodies - chi) // 2
    detail = f"chi={chi}, components={bodies}"
    if found != expected:
        print(f"FAIL: topology, expected {expected} through-hole(s), found {found} ({detail}). "
              f"Fewer = a bore is blind or sealed by a skin; more = an unintended opening or crossing bores.")
        return EXIT_FAIL
    print(f"PASS: topology, {found} through-hole(s) ({detail})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
