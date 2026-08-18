#!/usr/bin/env python3
"""Check an exported STL's bounding box against dimensions declared in SCAD.

Catches the failure mode visual inspection and assert()s in params.scad both
miss: geometry that renders and *looks* right but is subtly the wrong size --
a wrong -D override, a units slip, a parameter that didn't thread through.

Reads `// EXPECTED_BBOX: [x, y, z]` from the SCAD source (declare it near the
top, next to the part's dimension variables) and compares it to the rendered
STL's actual bounding box. No such comment = prints a note and exits 0
(opt-in, not required for every part).

TOLERANCE (changed -- read this before re-tightening or loosening it)
---------------------------------------------------------------------
The tolerance is now DERIVED from the model's own facet resolution instead of
the former flat `max(0.3mm, 1%)`. That old default was not a tessellation
tolerance at all: at $fa=2/$fs=0.3 the real per-axis mesh error is on the order
of 0.003 mm at 20 mm and 0.03 mm at 200 mm, so `max(0.3mm, 1%)` was 10x-65x too
loose and would pass a part that was genuinely the wrong size.

Per axis:  tol = max(bbox_error_bound(expected_dim), 0.005 mm)

where bbox_error_bound() is OpenSCAD's inscribed-polygon shortfall bound for a
curved surface of that size (see scad_tessellation.py for the derivation and
for why the bound, not the typical value, is the right quantity here). $fn/$fa/
$fs are read from the SCAD file, following include/use one level so that the
usual "declared in params.scad" layout resolves.

WHAT THIS CHECK CANNOT DO
-------------------------
A bounding box is nearly blind to the inscribed-polygon *across-flats* deficit
that makes holes too tight, because OpenSCAD puts a vertex at angle 0 and the
bbox therefore touches the ideal radius on any axis where a vertex lands. This
check verifies overall envelope only. Fit-critical round features need a
feature-level check plus the compensation in
openscad-cad/references/patterns.scad -- do not read a green bbox check as
evidence that a bore will fit.

Requires only `trimesh` (mesh.bounds/mesh.is_empty do not need scipy or
python-fcl). Install with:  pip install trimesh

Usage:
    python3 check_dimensions.py --stl build/part.stl --scad parts/part.scad
    python3 check_dimensions.py --stl build/part.stl --scad parts/part.scad \\
        --fa 2 --fs 0.3                 # override facet resolution
    python3 check_dimensions.py --stl build/part.stl --scad parts/part.scad \\
        --abs-tol 0.3 --rel-tol 0.01    # opt back into a flat tolerance

Exit codes:
    0  pass (or skipped -- no EXPECTED_BBOX declared)
    1  bbox mismatch
    4  usage/runtime error (missing file, unreadable mesh, trimesh absent)
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scad_tessellation import (  # noqa: E402
    NUMERIC_FLOOR_MM,
    bbox_error_bound,
    fragments_for_r,
    resolve_special_vars,
)

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 4

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: pip install trimesh", file=sys.stderr)
    sys.exit(EXIT_USAGE)

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
        sys.exit(EXIT_USAGE)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stl', required=True)
    parser.add_argument('--scad', required=True)
    parser.add_argument('--fn', type=float, default=None, help='override $fn')
    parser.add_argument('--fa', type=float, default=None, help='override $fa')
    parser.add_argument('--fs', type=float, default=None, help='override $fs')
    parser.add_argument('--abs-tol', type=float, default=None,
                        help='flat absolute tolerance; disables the derived one')
    parser.add_argument('--rel-tol', type=float, default=None,
                        help='flat relative tolerance; disables the derived one')
    parser.add_argument('--floor', type=float, default=NUMERIC_FLOOR_MM,
                        help=f'numeric floor in mm (default {NUMERIC_FLOOR_MM})')
    args = parser.parse_args()

    if not os.path.isfile(args.stl):
        print(f"ERROR: STL file not found: {args.stl}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if not os.path.isfile(args.scad):
        print(f"ERROR: SCAD file not found: {args.scad}", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    expected = parse_expected_from_scad(args.scad)
    if expected is None:
        print(f"WARNING: no '// EXPECTED_BBOX: [x, y, z]' line in {args.scad}; skipping.")
        return EXIT_OK

    try:
        mesh = trimesh.load(args.stl, force="mesh")
    except Exception as e:
        print(f"ERROR: cannot load mesh {args.stl}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if mesh.is_empty:
        print(f"ERROR: STL is empty or invalid: {args.stl}", file=sys.stderr)
        sys.exit(EXIT_USAGE)

    actual = mesh.bounds[1] - mesh.bounds[0]

    flat_mode = args.abs_tol is not None or args.rel_tol is not None
    if flat_mode:
        abs_tol = args.abs_tol if args.abs_tol is not None else 0.0
        rel_tol = args.rel_tol if args.rel_tol is not None else 0.0
        tolerances = [max(abs_tol, rel_tol * abs(e)) for e in expected]
        basis = f"flat tolerance max({abs_tol} mm, {rel_tol:.3%})"
    else:
        fn, fa, fs, source = resolve_special_vars(args.scad, args.fn, args.fa, args.fs)
        tolerances = [max(bbox_error_bound(e, fn, fa, fs), args.floor) for e in expected]
        facets = [fragments_for_r(abs(e) / 2.0, fn, fa, fs) for e in expected]
        basis = (f"tessellation bound, $fn={fn:g} $fa={fa:g} $fs={fs:g} "
                 f"({source}); facets/axis {facets}, floor {args.floor} mm")

    errors = []
    for i, axis in enumerate(['X', 'Y', 'Z']):
        diff = abs(actual[i] - expected[i])
        if diff > tolerances[i]:
            errors.append(
                f"{axis}: expected {expected[i]:.3f} mm, got {actual[i]:.3f} mm "
                f"(diff {diff:.4f} mm > tol {tolerances[i]:.4f} mm)"
            )

    if errors:
        print(f"FAIL: {os.path.basename(args.stl)} bbox mismatch [{basis}]:")
        for err in errors:
            print(f"  - {err}")
        print("  Fix the model or the EXPECTED_BBOX declaration -- do not widen the")
        print("  tolerance to make this pass. Use --abs-tol only for a part whose")
        print("  declared bbox is deliberately a rounded nominal.")
        return EXIT_MISMATCH

    tol_str = ", ".join(f"{t:.4f}" for t in tolerances)
    print(f"OK: {os.path.basename(args.stl)} bbox "
          f"[{actual[0]:.3f}, {actual[1]:.3f}, {actual[2]:.3f}] "
          f"within [{tol_str}] mm ({basis})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
