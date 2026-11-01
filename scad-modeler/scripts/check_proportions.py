#!/usr/bin/env python3
"""Proportions from the source, checked on the mesh (P6, 2026-11-01).

openscad-organic's only check was "render and look". A figurine whose head is
half too wide looks plausible in a thumbnail; INCIDENTS 2026-09-09 (replica from
one artwork photo) is the case. Write the proportions you researched BEFORE
modelling, one per line, and they become numbers:

    // PROPORTION: z/x = 2.6 +- 0.05          bbox extents x, y, z
    // PROPORTION: w_x@0.9 / x = 0.55 +- 0.1  width along x of the slice at 90 % of the height

Terms: x, y, z (bbox extents) and w_x@F / w_y@F (extent of the horizontal
section at fraction F of the height, measured from the bottom).

Usage:
    python3 check_proportions.py --scad figure.scad --stl figure.stl

Exit codes:
    0  pass, or SKIP when nothing is declared
    3  fail -- a ratio outside its tolerance, or a slice that hits no material
    4  usage error
"""
import argparse
import os
import re
import sys

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4
TERM = r"(x|y|z|w_[xy]@(?:0?\.\d+|1(?:\.0*)?))"
DECL_RE = re.compile(r"^[ \t]*//[ \t]*PROPORTION[ \t]*:[ \t]*" + TERM + r"\s*/\s*" + TERM +
                     r"\s*=\s*([0-9.]+)\s*(?:\+-|±)\s*([0-9.]+)", re.M)
ANY_RE = re.compile(r"^[ \t]*//[ \t]*PROPORTION[ \t]*:(.*)$", re.M)

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def measure(mesh, term):
    lo, hi = mesh.bounds
    ext = hi - lo
    if term in ("x", "y", "z"):
        return float(ext["xyz".index(term)])
    axis, frac = term[2], float(term.split("@")[1])
    z = lo[2] + frac * ext[2]
    z = min(max(z, lo[2] + 1e-6), hi[2] - 1e-6)
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return None
    b = sec.bounds
    return float(b[1][0 if axis == "x" else 1] - b[0][0 if axis == "x" else 1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scad", required=True)
    ap.add_argument("--stl", required=True)
    a = ap.parse_args()
    for p in (a.scad, a.stl):
        if not os.path.isfile(p):
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            return EXIT_USAGE
    src = open(a.scad, encoding="utf-8", errors="replace").read()
    decls = DECL_RE.findall(src)
    if len(decls) != len(ANY_RE.findall(src)):
        bad = [l.strip() for l in ANY_RE.findall(src) if not DECL_RE.search("// PROPORTION:" + l)]
        print(f"FAIL: proportions, unreadable line(s): {bad} -- form: `// PROPORTION: z/x = 2.6 +- 0.05`")
        return EXIT_FAIL
    if not decls:
        print(f"SKIP: proportions, {a.scad} declares no // PROPORTION:")
        return EXIT_OK
    mesh = trimesh.load(a.stl, force="mesh")
    fails, oks = [], []
    for num, den, val, tol in decls:
        n, d = measure(mesh, num), measure(mesh, den)
        label = f"{num}/{den} = {val} +- {tol}"
        if n is None or d is None or d == 0:
            fails.append(f"{label}: slice hits no material")
            continue
        got = n / d
        (oks if abs(got - float(val)) <= float(tol) else fails).append(f"{label}: measured {got:.3f}")
    for f in fails:
        print(f"FAIL: proportions, {a.scad}: {f}")
    if fails:
        return EXIT_FAIL
    print(f"PASS: proportions, {a.scad}: " + "; ".join(oks))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
