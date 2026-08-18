#!/usr/bin/env python3
"""Check exported STL bounding box against expected dimensions declared in SCAD.

Catches the failure mode visual inspection and assert()s in params.scad both
miss: geometry that renders and *looks* right (proportions look plausible) but
is subtly the wrong size -- a wrong -D override, a units slip, a parameter that
didn't thread through correctly. Rendering + eyeballing a preview won't catch a
part that's 5% off in one dimension; comparing the actual STL bounding box
against a stated expectation will.

Reads `// EXPECTED_BBOX: [x, y, z]` from the SCAD source file (declare it near
the top, next to the part's own dimension variables) and compares to the
rendered STL's actual bounding box. If the SCAD file has no such comment, this
prints a note and exits 0 (opt-in, not required for every part -- e.g. odd-
shaped parts where a bounding box isn't a meaningful sanity check).

Requires only `trimesh` (confirmed: unlike check_collisions.py, this script's
mesh.bounds/mesh.is_empty do NOT need scipy or python-fcl -- tested in a venv
with trimesh alone). Install with:
    pip install trimesh

Usage:
    python3 check_dimensions.py --stl build/part.stl --scad parts/part.scad
    python3 check_dimensions.py --stl build/part.stl --scad parts/part.scad \\
        --abs-tol 0.5 --rel-tol 0.01

Tolerance per axis = max(--abs-tol, --rel-tol * expected_dimension) -- a flat
mm floor for small parts, a percentage for large ones where mesh tessellation
error alone can exceed a fixed mm value. Defaults (0.3mm / 1%) confirmed to
correctly pass a exact match, fail a deliberate 1mm mismatch, and pass a
200mm part within its wider absolute tolerance -- see this skill's
references/setup-notes.md.
"""
import argparse
import os
import re
import sys

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: pip install trimesh", file=sys.stderr)
    sys.exit(1)

BBOX_RE = re.compile(
    r'^\s*//\s*EXPECTED_BBOX\s*:\s*\[\s*'
    r'([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*\]'
)


def parse_expected_from_scad(scad_path):
    try:
        with open(scad_path, 'r', encoding='utf-8') as f:
            for line in f:
                m = BBOX_RE.match(line)
                if m:
                    return [float(m.group(1)), float(m.group(2)), float(m.group(3))]
    except OSError as e:
        print(f"ERROR: cannot read SCAD file {scad_path}: {e}", file=sys.stderr)
        sys.exit(1)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stl', required=True)
    parser.add_argument('--scad', required=True)
    parser.add_argument('--abs-tol', type=float, default=0.3)
    parser.add_argument('--rel-tol', type=float, default=0.01)
    args = parser.parse_args()

    if not os.path.isfile(args.stl):
        print(f"ERROR: STL file not found: {args.stl}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.scad):
        print(f"ERROR: SCAD file not found: {args.scad}", file=sys.stderr)
        sys.exit(1)

    expected = parse_expected_from_scad(args.scad)
    if expected is None:
        print(f"WARNING: no '// EXPECTED_BBOX: [x, y, z]' line in {args.scad}; skipping.")
        return 0

    mesh = trimesh.load(args.stl, force="mesh")
    if mesh.is_empty:
        print(f"ERROR: STL is empty or invalid: {args.stl}", file=sys.stderr)
        sys.exit(1)

    bounds = mesh.bounds
    actual = bounds[1] - bounds[0]

    tolerances = [max(args.abs_tol, args.rel_tol * abs(e)) for e in expected]

    errors = []
    for i, axis in enumerate(['X', 'Y', 'Z']):
        diff = abs(actual[i] - expected[i])
        if diff > tolerances[i]:
            errors.append(
                f"{axis}: expected {expected[i]:.3f} mm, got {actual[i]:.3f} mm "
                f"(diff {diff:.3f} mm > tol {tolerances[i]:.3f} mm)"
            )

    if errors:
        print(f"FAIL: {os.path.basename(args.stl)} bbox mismatch:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"OK: {os.path.basename(args.stl)} bbox {actual} within tolerances {tolerances}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
