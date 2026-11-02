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

The bound is a worst case (whole extent = one faceted circle), so at $fn=64 a
180 mm part gets ~0.22 mm of slack. When the extents are known to be planar or
axis-aligned circles with $fn % 4 == 0, declare a tighter value:

    // EXPECTED_BBOX_TOL: 0.01          (or [tx, ty, tz])

Per axis it becomes max(min(declared, derived), 0.005 mm) -- the declaration
can only TIGHTEN the gate, never loosen it (2026-11-02, audit §5 #7).

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
    minkowski_sphere_deficit,
    resolve_special_vars,
)

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 4

try:
    import trimesh
except ImportError:
    __import__("mesh_python").reexec()
    print("ERROR: trimesh not installed. Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)

BBOX_RE = re.compile(
    r'^\s*//\s*EXPECTED_BBOX\s*:\s*\[\s*'
    r'([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*\]'
)

# `// EXPECTED_BBOX_TOL: 0.01` -- an optional, TIGHTENING-only tolerance.
# Why (2026-11-02 audit, §5 #7): the derived bound assumes the worst case that a
# whole axis extent is one faceted circle of the part's own size, so at $fn=64 a
# 180 mm part gets 0.219 mm of slack -- a 0.2 mm modelling error hides inside it.
# Measured on all 11 GenKit fixtures ($fn=64, extents set by planes or by
# circles whose vertices land on the axes): real bbox error 0.00000 mm. Whoever
# knows the extent is planar/axis-aligned (the generator does) declares it.
# It can never LOOSEN the gate: the result is min(declared, derived), floored at
# NUMERIC_FLOOR_MM. Scalar or [x, y, z].
_NUM = r'([0-9.eE+\-]+)'
BBOX_TOL_RE = re.compile(
    r'^\s*//\s*EXPECTED_BBOX_TOL\s*:\s*(?:\[\s*' + _NUM + r'\s*,\s*' + _NUM
    + r'\s*,\s*' + _NUM + r'\s*\]|' + _NUM + r')'
)


def parse_declared_tol(scad_path):
    """[tx, ty, tz] from `// EXPECTED_BBOX_TOL:` or None."""
    try:
        with open(scad_path, 'r', encoding='utf-8') as f:
            for line in f:
                m = BBOX_TOL_RE.match(line)
                if m:
                    if m.group(4) is not None:
                        return [float(m.group(4))] * 3
                    return [float(m.group(1)), float(m.group(2)), float(m.group(3))]
    except (OSError, ValueError):
        return None
    return None


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
        # A minkowski() sum with a faceted sphere sets the axis extent by the
        # SPHERE's radius and $fn, not the part's, so bbox_error_bound() alone
        # under-reports it by an order of magnitude (0.0040 mm vs the measured
        # 0.0214 mm on server_rack_modular_v4/v8 parts/node.scad). Added as a
        # separate term rather than a higher floor so that a part without
        # minkowski() keeps the tight tolerance it was validated against
        # (INCIDENTS.md, 2026-09-12).
        mink = minkowski_sphere_deficit(args.scad)
        # Added ON TOP of the existing bound, not folded into the max(): the
        # two errors are independent and they add. max() drops the float32
        # storage allowance entirely whenever the tessellation bound exceeds
        # it, which is exactly what happens here -- the term came out at
        # 0.02139 mm against a measured 0.02141 mm, so the check still failed
        # by 0.00002 mm on a part that is 0.08% off nominal (INCIDENTS.md,
        # 2026-09-12). A part without minkowski() gets mink = 0 and keeps the
        # tolerance it was validated against.
        tolerances = [max(bbox_error_bound(e, fn, fa, fs), args.floor) + mink
                      for e in expected]
        facets = [fragments_for_r(abs(e) / 2.0, fn, fa, fs) for e in expected]
        basis = (f"tessellation bound, $fn={fn:g} $fa={fa:g} $fs={fs:g} "
                 f"({source}); facets/axis {facets}, floor {args.floor} mm"
                 + (f"; +{mink:.4f} mm minkowski-sphere term" if mink > 0 else ""))
        declared = parse_declared_tol(args.scad)
        if declared is not None:
            looser = [i for i in range(3) if declared[i] > tolerances[i]]
            tolerances = [max(min(declared[i], tolerances[i]), args.floor)
                          for i in range(3)]
            basis = (f"declared EXPECTED_BBOX_TOL {declared} (tightening only; "
                     f"capped by the {basis})")
            if looser:
                print("NOTE: EXPECTED_BBOX_TOL is looser than the derived bound on "
                      f"{', '.join('XYZ'[i] for i in looser)} -- the derived bound is "
                      "used there (a declaration can only tighten the gate).")

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
