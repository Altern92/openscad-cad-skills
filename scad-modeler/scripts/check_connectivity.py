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

    actual = mesh.body_count

    if actual != expected:
        print(f"FAIL: {os.path.basename(args.stl)} has {actual} disconnected "
              f"bod{'y' if actual == 1 else 'ies'}, expected {expected}:")
        for i, part in enumerate(mesh.split(only_watertight=False)):
            size = part.bounds[1] - part.bounds[0]
            print(f"  - body {i}: bounds {part.bounds.tolist()}, "
                  f"size {size.tolist()}, volume {part.volume if part.is_volume else 'n/a'}")
        print("  -> if this is intentional, declare it: // EXPECTED_BODIES: "
              f"{actual}. If not, something doesn't physically touch what it "
              "should -- check the geometry that changed most recently.")
        return EXIT_MISMATCH

    print(f"OK: {os.path.basename(args.stl)} is {actual} connected "
          f"bod{'y' if actual == 1 else 'ies'} (expected {expected}).")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
