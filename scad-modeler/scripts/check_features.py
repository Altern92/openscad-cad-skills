#!/usr/bin/env python3
"""Measure round fit-critical features in a rendered STL, flat-to-flat.

Why this exists -- check_dimensions.py cannot do this
-----------------------------------------------------
OpenSCAD builds circles as inscribed polygons and always places a vertex at
angle 0 (verified in upstream primitives.cc). Two consequences:

  * A hole's ACROSS-FLATS size -- the apothem-to-apothem distance a shaft
    actually binds on -- is d*cos(pi/n), not d.
  * The BOUNDING BOX is blind to that. With n divisible by 4 (and $fa=2 gives
    exactly n=180) vertices land on all four axes and the bbox equals the ideal
    diameter, so a bbox check passes a hole that is genuinely too tight.

So a green bbox check is not evidence that a bearing will seat. This script
measures the thing that decides the fit: it slices the mesh perpendicular to a
declared hole axis and reports the minimum distance across the resulting
contour.

How much it matters depends entirely on facet resolution, which is the point:
    Hole    facets  across-flats deficit
    Ø8      $fa=2/$fs=0.3   n=84   0.006 mm   negligible
    Ø8      OpenSCAD defaults n=13 0.233 mm   a failed fit
A part authored without setting $fa/$fs is undersized by a quarter millimetre
and nothing else in the validation chain notices.

DECLARING A HOLE
----------------
In the part's .scad file, next to its dimension variables:

    // EXPECTED_HOLE: [0, 0, 5, "Z", 8.0]

meaning: a point on the hole's axis at (0, 0, 5) in the same coordinates the
STL is exported in, the axis direction, and the target across-flats diameter in
mm. Declare one line per hole; all are checked. No declarations = skipped.

The target is what you want to MEASURE, not what you typed into cylinder(). If
you wrote `cylinder(d=8)` with coarse facets, this reports ~7.77 and fails --
correctly. Fix it with true_hole_d() from
openscad-cad/references/patterns.scad, or by setting $fa/$fs finer.

WHAT THIS DOES NOT DO
---------------------
Geometry only. It says nothing about how the hole prints -- FDM lays holes
down undersized on top of this, by an amount that needs a calibration coupon on
your own printer and material. This check and that offset are separate layers;
see openscad-cad/references/tolerances.md.

Requires: trimesh, shapely, scipy, networkx. Install with:
    pip install trimesh shapely scipy networkx

Usage:
    python3 check_features.py --stl build/part.stl --scad parts/part.scad
    python3 check_features.py --stl build/part.stl --scad parts/part.scad --tol 0.02

Exit codes:
    0  pass (or skipped -- no EXPECTED_HOLE declared)
    1  a hole measured outside tolerance
    4  usage/runtime error, or a declared hole could not be measured
"""
import argparse
import os
import re
import sys

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 4

try:
    import numpy as np
    import trimesh
except ImportError:
    print("ERROR: trimesh/numpy not installed. Run: pip install trimesh shapely scipy networkx",
          file=sys.stderr)
    sys.exit(EXIT_USAGE)

# // EXPECTED_HOLE: [x, y, z, "Z", d]
HOLE_RE = re.compile(
    r'^\s*//\s*EXPECTED_HOLE\s*:\s*\[\s*'
    r'([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*,\s*'
    r'["\']?([XYZxyz])["\']?\s*,\s*([0-9.eE+\-]+)\s*\]'
)

AXES = {"X": [1.0, 0.0, 0.0], "Y": [0.0, 1.0, 0.0], "Z": [0.0, 0.0, 1.0]}


def parse_holes(scad_path):
    holes = []
    try:
        with open(scad_path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                m = HOLE_RE.match(line)
                if m:
                    holes.append({
                        "point": [float(m.group(1)), float(m.group(2)), float(m.group(3))],
                        "axis": m.group(4).upper(),
                        "d": float(m.group(5)),
                        "line": lineno,
                    })
    except OSError as e:
        print(f"ERROR: cannot read SCAD file {scad_path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    return holes


def measure_hole(mesh, point, axis_name, expected_d):
    """Slice perpendicular to the axis and measure the hole containing `point`.

    Returns (across_flats, circumscribed, note) or (None, None, reason).
    across_flats is 2x the shortest distance from the axis to the contour --
    the dimension a shaft binds on. circumscribed is 2x the longest, i.e. what
    the polygon measures across corners.
    """
    normal = np.array(AXES[axis_name], dtype=float)
    origin = np.array(point, dtype=float)

    section = mesh.section(plane_origin=origin, plane_normal=normal)
    if section is None:
        return None, None, "the cutting plane does not intersect the mesh"

    try:
        # to_planar is deprecated in newer trimesh in favour of to_2D.
        flatten = getattr(section, "to_2D", None) or section.to_planar
        planar, to_3d = flatten()
    except Exception as e:
        return None, None, f"could not flatten the section ({e})"

    # Map the declared axis point into the section's 2D frame.
    p2 = (np.linalg.inv(to_3d) @ np.append(origin, 1.0))[:2]

    try:
        from shapely.geometry import Point, Polygon as ShPolygon
    except ImportError:
        return None, None, "shapely not installed (pip install shapely)"

    # Work from the raw closed loops rather than trimesh's polygons_full, which
    # builds an enclosure tree and drags in an rtree dependency. The section of
    # a solid with a bore yields at least two loops containing the axis point --
    # the outer silhouette and the bore. The smallest of them is the bore.
    probe = Point(p2[0], p2[1])
    loops = []
    for loop in planar.discrete:
        pts = np.asarray(loop)[:, :2]
        if len(pts) < 3:
            continue
        try:
            poly = ShPolygon(pts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                continue
        except Exception:
            continue
        loops.append((poly, pts))

    if not loops:
        return None, None, "the section produced no closed contours"

    outer_area = max(p.area for p, _ in loops)
    containing = [(p, pts) for p, pts in loops if p.contains(probe)]
    if not containing:
        return None, None, ("no closed contour encloses that point -- check the "
                            "coordinates and that the axis is right")

    poly, pts = min(containing, key=lambda t: t[0].area)
    if poly.area >= outer_area:
        # The only thing enclosing the point is the part's own silhouette, so
        # there is no cavity here -- measuring it would silently report the
        # distance to the outside wall as if it were a bore.
        return None, None, ("that point is inside the part's outer contour but "
                            "not inside any cavity -- no hole there")

    # Distance to the contour ITSELF, not to its vertices: the inradius is the
    # shortest distance to an edge, and on a polygonised bore the vertices all
    # sit at the circumradius. Measuring to vertices happens to give the right
    # answer only when the cutting plane lands on the mesh's diagonal edges.
    across_flats = 2.0 * float(poly.exterior.distance(probe))
    across_corners = 2.0 * float(np.linalg.norm(pts - p2, axis=1).max())
    return across_flats, across_corners, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stl", required=True)
    parser.add_argument("--scad", required=True)
    parser.add_argument("--tol", type=float, default=0.05,
                        help="allowed across-flats deviation in mm (default 0.05)")
    args = parser.parse_args()

    for path in (args.stl, args.scad):
        if not os.path.isfile(path):
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            return EXIT_USAGE

    holes = parse_holes(args.scad)
    if not holes:
        print(f"WARNING: no '// EXPECTED_HOLE: [x, y, z, \"Z\", d]' line in "
              f"{args.scad}; skipping.")
        return EXIT_OK

    try:
        mesh = trimesh.load(args.stl, force="mesh")
    except Exception as e:
        print(f"ERROR: cannot load mesh {args.stl}: {e}", file=sys.stderr)
        return EXIT_USAGE
    if mesh.is_empty:
        print(f"ERROR: STL is empty or invalid: {args.stl}", file=sys.stderr)
        return EXIT_USAGE

    failures, unmeasured = [], []
    for h in holes:
        label = (f"Ø{h['d']:g} on {h['axis']} at "
                 f"({h['point'][0]:g}, {h['point'][1]:g}, {h['point'][2]:g}) "
                 f"[{os.path.basename(args.scad)}:{h['line']}]")
        flats, corners, reason = measure_hole(mesh, h["point"], h["axis"], h["d"])
        if flats is None:
            unmeasured.append(f"{label}: {reason}")
            continue

        diff = flats - h["d"]
        if abs(diff) > args.tol:
            hint = ""
            if diff < 0 and corners and corners > h["d"] - args.tol:
                # Across corners is on target but across flats is short: the
                # signature of an uncompensated inscribed polygon.
                hint = ("  -> across corners is {:.3f} mm, so this is inscribed-"
                        "polygon undersizing, not a wrong parameter. Use "
                        "true_hole_d() or set $fa/$fs finer.").format(corners)
            failures.append(
                f"{label}: across-flats {flats:.3f} mm, expected {h['d']:.3f} mm "
                f"(off by {diff:+.3f} mm > tol {args.tol:.3f} mm){hint}")
        else:
            print(f"  OK: {label} -- across-flats {flats:.3f} mm "
                  f"(across corners {corners:.3f} mm)")

    if unmeasured:
        print("ERROR: declared holes that could not be measured:")
        for u in unmeasured:
            print(f"  - {u}")
        return EXIT_USAGE

    if failures:
        print(f"FAIL: {os.path.basename(args.stl)} hole geometry:")
        for f in failures:
            print(f"  - {f}")
        return EXIT_MISMATCH

    print(f"OK: {len(holes)} declared hole(s) within {args.tol} mm across-flats.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
