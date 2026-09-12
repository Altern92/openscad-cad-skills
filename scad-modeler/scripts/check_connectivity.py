#!/usr/bin/env python3
"""Check that a rendered STL is a single connected body (unless declared otherwise).

Why this exists
----------------
Real incident (INCIDENTS.md, 2026-08-19): a fix for a collision between a
bearing tower's support legs and a worm gear's teeth increased the legs'
radius from 7mm to 15mm. That solved the collision -- but nobody re-checked
whether the legs, at their NEW radius, still physically touched the upper
bearing disc they were supposed to hold up. They didn't: the disc (9mm
radius) and the legs' new inner edge (12mm radius) left a permanent 3mm gap.
`gearbox_frame.stl` rendered, exported, and passed every existing check --
because none of them look for this failure mode:

  - check_dimensions.py only checks the overall bounding box. A part can be
    two disconnected islands and still have exactly the right envelope --
    the floating piece was WITHIN the same bbox as the connected whole.
  - check_collisions.py checks interference BETWEEN separate STL files. It
    has no way to notice that ONE file's own geometry silently split into
    two unconnected solids.

The tool to catch this (a mesh connected-component count) existed in trimesh
all along and was used manually, once, after the bug was already found by
eye -- not run automatically as part of validation. This script makes that
check a standard, default-on step (see validate_scad.sh) instead of
something that has to be remembered.

DECLARING AN EXCEPTION
-----------------------
Most single-part files should render as exactly ONE connected body -- that's
the default expectation, no declaration needed. If a part is intentionally
multiple disconnected bodies in one STL (rare -- e.g. a small loose spacer
printed alongside its housing to save a print job), declare it explicitly:

    // EXPECTED_BODIES: 2

Requires: trimesh only (mesh.body_count / mesh.split() don't need scipy or
python-fcl). Install with: pip install trimesh

Usage:
    python3 check_connectivity.py --stl build/part.stl --scad parts/part.scad

Exit codes:
    0  pass (single connected body, or matches a declared EXPECTED_BODIES)
    1  body count mismatch
    4  usage/runtime error
"""
import argparse
import os
import re
import sys

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 4

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: pip install trimesh", file=sys.stderr)
    sys.exit(EXIT_USAGE)

BODIES_RE = re.compile(r'^\s*//\s*EXPECTED_BODIES\s*:\s*([0-9]+)')

# Cap the printed body list: a shattered mesh can have thousands of components
# and flooding the caller with 3000+ lines buries the verdict (and costs the
# caller's context, which is its own failure mode).
MAX_BODIES_SHOWN = 20

# Below this, an edge is a sliver rather than geometry. 1e-3 mm is 1 micron --
# three orders of magnitude finer than any FDM feature and finer than the
# resolution a slicer's grid keeps, so anything under it is an artefact.
DEGENERATE_EDGE_MM = 1e-3


def parse_expected_bodies(scad_path):
    try:
        with open(scad_path, "r", encoding="utf-8") as f:
            for line in f:
                m = BODIES_RE.match(line)
                if m:
                    return int(m.group(1))
    except OSError as e:
        print(f"ERROR: cannot read SCAD file {scad_path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    return 1  # default: a printed part should be a single connected body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stl", required=True)
    parser.add_argument("--scad", required=True)
    args = parser.parse_args()

    for path in (args.stl, args.scad):
        if not os.path.isfile(path):
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            return EXIT_USAGE

    expected = parse_expected_bodies(args.scad)

    try:
        mesh = trimesh.load(args.stl, force="mesh")
    except Exception as e:
        print(f"ERROR: cannot load mesh {args.stl}: {e}", file=sys.stderr)
        return EXIT_USAGE
    if mesh.is_empty:
        print(f"ERROR: STL is empty or invalid: {args.stl}", file=sys.stderr)
        return EXIT_USAGE

    # ONE source of truth: the same list is counted AND printed. Counting with
    # mesh.body_count while printing mesh.split() let those two disagree -- a
    # mesh that shattered into 3122 slivers was reported as "2 disconnected
    # bodies", and the suggested EXPECTED_BODIES: 2 would have been wrong.
    parts = mesh.split(only_watertight=False)

    # Split the components by what they physically ARE, not just how many there
    # are. trimesh reports a component's volume WITH ITS WINDING SIGN, and an
    # ENCLOSED CAVITY comes out as a watertight shell with NEGATIVE volume.
    # Measured on server_rack_modular_v4/scad/parts/back_panel.stl: four
    # 4.6x1.7x4.6 shells, signed volume -35.972 (= the magnet pocket's own
    # 35.972 mm^3), each centroid inside the part with 0.65mm of material on
    # every side. The part is ONE valid solid; those four shells are its
    # internal cavities. Counting them as "bodies" reported 5 where the truth
    # is 1, on five separate panel parts -- a standing false FAIL.
    material, voids, degenerate = [], [], []
    for p in parts:
        try:
            v = float(p.volume)
        except Exception:
            degenerate.append(p)
            continue
        if v != v:  # NaN
            degenerate.append(p)
        elif v > 0:
            material.append(p)
        elif v < 0:
            voids.append(p)
        else:
            degenerate.append(p)

    actual = len(material)

    if actual != expected:
        print(f"FAIL: {os.path.basename(args.stl)} has {actual} disconnected "
              f"bod{'y' if actual == 1 else 'ies'}, expected {expected}:")
        for i, part in enumerate(material[:MAX_BODIES_SHOWN]):
            size = part.bounds[1] - part.bounds[0]
            print(f"  - body {i}: bounds {part.bounds.tolist()}, "
                  f"size {size.tolist()}, volume {part.volume if part.is_volume else 'n/a'}")
        if actual > MAX_BODIES_SHOWN:
            print(f"  - ... and {actual - MAX_BODIES_SHOWN} more material components")
        if degenerate:
            print(f"  - NOTE: {len(degenerate)} further component(s) are degenerate "
                  "(zero or undefined volume) -- usually an unbounded pattern or a "
                  "failed boolean, not separate printable pieces; prefer fixing the "
                  "geometry over declaring EXPECTED_BODIES)")
        print("  -> if this is intentional, declare it: // EXPECTED_BODIES: "
              f"{actual}. If not, something doesn't physically touch what it "
              "should -- check the geometry that changed most recently.")
        return EXIT_MISMATCH

    print(f"OK: {os.path.basename(args.stl)} is {actual} connected "
          f"bod{'y' if actual == 1 else 'ies'} (expected {expected}).")

    # Degenerate geometry, reported because it silently poisons every
    # ray-based measurement taken on this mesh. Measured 2026-09-12 on
    # server_rack_modular/scad/build/frame_module.stl: watertight, ONE
    # connected body, every volume-based check clean -- and a shortest edge of
    # 0.00003 mm. check_printability.py then read a "0.014 mm wall" off it,
    # which is 30x below anything the model declares and was reported as a
    # FAIL. The same part with a healthy mesh (base.stl, shortest edge
    # 0.296 mm) reads a min wall of 0.252 mm, which matches its geometry.
    # A mesh with sub-micron edges can also confuse a slicer, so this is worth
    # naming even where no numeric check has tripped yet.
    try:
        min_edge = float(mesh.edges_unique_length.min())
    except Exception:
        min_edge = None
    if min_edge is not None and min_edge < DEGENERATE_EDGE_MM:
        n_degen = int((mesh.edges_unique_length < DEGENERATE_EDGE_MM).sum())
        print(f"     note: DEGENERATE GEOMETRY -- shortest edge {min_edge:.6f} mm, "
              f"{n_degen} edge(s) below {DEGENERATE_EDGE_MM} mm. Measurements that "
              "cast rays (printability wall/overhang) read nonsense across such a "
              "sliver, and a slicer may too. Usually a boolean that produced a "
              "zero-area face; find it before trusting any thin-wall number.")
    if voids:
        # Not a failure: an enclosed cavity is legitimate geometry (a magnet
        # pocket, an air chamber, a captured nut). It is reported because a
        # cavity nobody meant to leave is invisible in every other check and
        # in the render -- the part looks solid from outside.
        sizes = sorted(
            {tuple(round(float(x), 3) for x in (v.bounds[1] - v.bounds[0])) for v in voids}
        )
        print(f"     note: {len(voids)} enclosed internal cavity/cavities "
              f"(size(s) {sizes}) -- verify these are intended (magnet or nut "
              "pocket, air gap); they cannot be seen from outside.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
