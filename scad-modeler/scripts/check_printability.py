#!/usr/bin/env python3
"""FDM printability checks on an already-rendered part STL: unsupported
overhang and thin-wall detection. Neither is checked anywhere else in
this skill -- every other check verifies the MODEL is dimensionally and
topologically correct; this checks whether the resulting geometry can
actually be printed on FDM without failing mid-print, independent of
whether it's a "correct" model.

Added 2026-08-22, motivated by a deep-research pass specifically asked
for real, citable precedent (not a restatement of this skill's own
design) for pre-slicing printability validation. Findings, honestly
graded by the research itself:

  - Overhang angle: "Strongest Precedent" -- a direct geometric
    calculation on face normals vs. the build axis, the same technique
    tools like Autodesk Meshmixer's "Overhangs" analysis use.
  - Wall thickness: "Strongest Precedent" -- ray-casting from a surface
    point along its inward normal to the next intersection is a standard,
    simpler alternative to full medial-axis-transform skeletonization for
    this purpose.
  - Minimum feature size (e.g. embossed text width vs. nozzle diameter):
    "No Strong Precedent Found" for a pre-slicing (as opposed to
    slicer-internal) algorithm -- NOT implemented here. Don't add a
    heuristic guess for this without a better-grounded technique; most
    real tools defer this specific check to the slicer itself.

Both checks below reuse only what's already a dependency of this skill
(trimesh) -- wall thickness uses trimesh's ray-triangle intersector
(pyembree accelerates it if installed, but the pure-Python fallback
works and was confirmed directly against a synthetic box).

SCOPE -- what this does NOT check
----------------------------------
- Bridging (unsupported spans between two supported points, as opposed to
  a single unsupported downward face) -- a different geometric question,
  not covered by either check here.
- Minimum feature size (see above).
- Wall-thickness accuracy NEAR AN EDGE where two non-parallel surfaces
  meet (e.g. a flat cap's rim next to a steeply sloped side, a sharp
  fillet transition): the ray-along-face-normal technique can report a
  small "thickness" there that reflects the local edge geometry, not a
  genuine parallel-wall gap -- confirmed directly (a solid, non-hollow
  cone's flat top cap measured a spuriously short "thickness" of
  0.13mm near its rim, purely from the ray grazing the adjacent sloped
  side surface a short distance away). This is most reliable on genuine
  shell/enclosure geometry (confirmed against a real 2mm-wall box:
  measured exactly 2.000mm with no edge artifacts at the box's own
  corners) -- treat a THIN WALL flag on a solid, sharply-tapered, or
  pointed feature with more skepticism than the same flag on a flat panel.
- Anything the slicer itself would catch better with real toolpath
  knowledge (e.g. actual support generation, exact first-layer adhesion).
  This is a coarse, fast, pre-slicing sanity check, not a slicer
  replacement.
- Which orientation is BEST to print in -- only whether the part, AS
  ORIENTED (by convention, +Z is the intended build-up direction, per
  this skill's part-modeling convention -- override with --build-axis if
  a part's local +Z isn't its print-up direction), passes these two
  limits.

Usage:
    python3 check_printability.py --stl build/part.stl
    python3 check_printability.py --stl build/part.stl --overhang-deg 50 \\
        --nozzle-d 0.4 --min-wall 0.8

Exit codes:
    0  pass
    2  degraded (mesh not watertight, or ray-casting failed for some
       samples -- treat as not fully checked)
    3  fail -- overhang or thin-wall violation found
    4  usage error
"""
import argparse
import os
import sys

EXIT_OK, EXIT_DEGRADED, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4


def check_overhang(mesh, build_axis, overhang_deg, baseplate_eps):
    """Flag faces whose normal points more than (90 - overhang_deg) away
    from straight up along build_axis -- i.e. within overhang_deg of
    pointing straight down, matching the common slicer convention
    "needs support past N degrees from vertical". Returns (bad_area_mm2,
    total_downward_area_mm2, worst_angle_deg) or (0.0, 0.0, None) if no
    downward-facing, non-baseplate area exists at all.

    Faces resting directly on the build plate (centroid height along
    build_axis within baseplate_eps of the mesh's own minimum height) are
    excluded from consideration -- they are supported BY THE PLATE, not
    floating, and flagging a part's own flat bottom as "unsupported
    overhang" would be a false positive on every single printable part.
    Confirmed as a real bug during testing: a plain 20mm cube's flat
    bottom face was initially flagged before this exclusion was added.
    """
    import numpy as np
    normals = mesh.face_normals
    areas = mesh.area_faces
    up = np.array(build_axis, dtype=float)
    up = up / np.linalg.norm(up)
    heights = mesh.triangles_center.dot(up)
    min_height = float(heights.min())
    on_baseplate = heights <= (min_height + baseplate_eps)

    # cos(theta) where theta is the angle from straight-DOWN (-up) to the
    # face normal: theta=0 -> normal points straight down (worst, a flat
    # downward ceiling); theta=90 -> normal is horizontal (a vertical
    # wall, always fine regardless of overhang_deg).
    cos_theta = normals.dot(-up)
    downward = (cos_theta > 0) & ~on_baseplate
    if not np.any(downward):
        return 0.0, 0.0, None
    theta_deg = np.degrees(np.arccos(np.clip(cos_theta[downward], -1.0, 1.0)))
    total_down_area = float(areas[downward].sum())
    # "needs support past overhang_deg from vertical" == theta < (90 - overhang_deg)
    bad = theta_deg < (90.0 - overhang_deg)
    bad_area = float(areas[downward][bad].sum()) if np.any(bad) else 0.0
    worst = float(theta_deg.min()) if len(theta_deg) else None
    return bad_area, total_down_area, worst


def check_wall_thickness(mesh, min_wall, sample_cap=1500, seed=0):
    """Sample up to sample_cap face centroids, cast a ray inward along
    each face's own (negated) normal, and record the distance to the
    next surface intersection as the local wall thickness there. Returns
    (min_thickness_found, n_samples, n_below_threshold, n_ray_misses).

    A small epsilon offset along -normal avoids the ray immediately
    re-intersecting its own originating triangle (confirmed necessary:
    without it, self-intersection at distance ~0 dominates the result).
    A ray that hits nothing (e.g. a genuinely open/non-watertight region,
    or a numerical edge case) is counted as a miss, not a false "thick"
    reading, and does not silently pass.
    """
    import numpy as np
    ri = trimesh_ray_intersector(mesh)
    centroids = mesh.triangles_center
    normals = mesh.face_normals
    n = len(centroids)
    if n > sample_cap:
        rng = np.random.default_rng(seed)
        idx = rng.choice(n, size=sample_cap, replace=False)
    else:
        idx = np.arange(n)

    eps = 1e-4
    origins = centroids[idx] - normals[idx] * eps
    directions = -normals[idx]
    locations, index_ray, _index_tri = ri.intersects_location(
        origins, directions, multiple_hits=False)

    hit_for_ray = {}
    for loc, ray_i in zip(locations, index_ray):
        d = float(np.linalg.norm(loc - origins[ray_i]))
        if ray_i not in hit_for_ray or d < hit_for_ray[ray_i]:
            hit_for_ray[ray_i] = d

    n_samples = len(idx)
    n_misses = n_samples - len(hit_for_ray)
    if not hit_for_ray:
        return None, n_samples, 0, n_misses
    thicknesses = list(hit_for_ray.values())
    min_t = min(thicknesses)
    n_below = sum(1 for t in thicknesses if t < min_wall)
    return min_t, n_samples, n_below, n_misses


def trimesh_ray_intersector(mesh):
    import trimesh
    return trimesh.ray.ray_triangle.RayMeshIntersector(mesh)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stl", required=True, help="rendered part STL to check")
    ap.add_argument("--build-axis", default="0,0,1",
                     help="comma-separated build-up direction in the STL's own "
                          "coordinate frame (default 0,0,1 -- this skill's parts "
                          "are modeled with +Z as the intended print-up direction "
                          "unless a part's header comment says otherwise)")
    ap.add_argument("--overhang-deg", type=float, default=45.0,
                     help="max degrees from vertical before a downward face is "
                          "flagged as needing support (default 45, common slicer default)")
    ap.add_argument("--nozzle-d", type=float, default=0.4,
                     help="nozzle diameter in mm, used to derive --min-wall if not "
                          "given directly (default 0.4mm)")
    ap.add_argument("--min-wall", type=float, default=None,
                     help="minimum wall thickness in mm (default: 2x --nozzle-d, "
                          "the commonly cited rule of thumb)")
    ap.add_argument("--wall-samples", type=int, default=1500,
                     help="max face-centroid samples for the wall-thickness ray-cast "
                          "(default 1500 -- caps runtime on a dense mesh)")
    ap.add_argument("--baseplate-eps", type=float, default=0.05,
                     help="mm: a downward face within this height of the mesh's own "
                          "minimum (along --build-axis) is treated as resting on the "
                          "build plate, not a floating overhang (default 0.05mm)")
    args = ap.parse_args()

    try:
        import trimesh
    except ImportError:
        print("ERROR: trimesh not installed. Run: pip install trimesh", file=sys.stderr)
        return EXIT_USAGE

    if not os.path.isfile(args.stl):
        print(f"error: {args.stl} not found", file=sys.stderr)
        return EXIT_USAGE

    try:
        build_axis = tuple(float(x) for x in args.build_axis.split(","))
        if len(build_axis) != 3:
            raise ValueError
    except ValueError:
        print(f"error: --build-axis must be 3 comma-separated numbers, got "
              f"{args.build_axis!r}", file=sys.stderr)
        return EXIT_USAGE

    min_wall = args.min_wall if args.min_wall is not None else 2.0 * args.nozzle_d

    mesh = trimesh.load(args.stl, force="mesh")
    if mesh.is_empty:
        print(f"ERROR: {args.stl} contains no geometry.", file=sys.stderr)
        return EXIT_USAGE

    degraded = False
    if not mesh.is_watertight:
        print(f"DEGRADED: {args.stl} is not watertight -- overhang area is still "
              f"measured (face-normal based, doesn't need watertightness), but "
              f"wall-thickness ray-casting on it is unreliable.")
        degraded = True

    failures = []

    bad_area, total_down_area, worst_angle = check_overhang(
        mesh, build_axis, args.overhang_deg, args.baseplate_eps)
    if total_down_area == 0.0:
        print("Overhang: no downward-facing area at all -- nothing to flag.")
    else:
        pct = 100.0 * bad_area / total_down_area
        print(f"Overhang: {bad_area:.1f} mm^2 of {total_down_area:.1f} mm^2 downward-"
              f"facing area ({pct:.1f}%) exceeds {args.overhang_deg:.0f} deg from "
              f"vertical (worst face {90.0 - worst_angle:.1f} deg from vertical).")
        if bad_area > 0.0:
            failures.append(
                f"UNSUPPORTED OVERHANG: {bad_area:.1f} mm^2 steeper than "
                f"{args.overhang_deg:.0f} deg from vertical (build axis {build_axis}) "
                f"-- will need support material or a different print orientation.")

    if mesh.is_watertight:
        min_t, n_samples, n_below, n_misses = check_wall_thickness(
            mesh, min_wall, sample_cap=args.wall_samples)
        if min_t is None:
            print(f"DEGRADED: wall-thickness ray-cast produced no valid hits "
                  f"out of {n_samples} sample(s) -- treat as not checked.")
            degraded = True
        else:
            print(f"Wall thickness: min {min_t:.3f} mm found across {n_samples} "
                  f"sample(s) ({n_below} below {min_wall:.2f} mm threshold, "
                  f"{n_misses} ray miss(es)).")
            if n_below > 0:
                failures.append(
                    f"THIN WALL: minimum measured thickness {min_t:.3f} mm < "
                    f"required {min_wall:.2f} mm ({n_below}/{n_samples} sample(s) "
                    f"below threshold) -- likely to fail or warp during printing.")
            if n_misses > n_samples * 0.1:
                print(f"DEGRADED: {n_misses}/{n_samples} wall-thickness rays missed "
                      f"entirely -- results may be incomplete.")
                degraded = True
    else:
        print("Wall thickness: SKIPPED (mesh not watertight).")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        print("Fix by changing wall thickness or print orientation at the source "
              "-- do not loosen --overhang-deg/--min-wall just to silence a real "
              "printability problem.")
        return EXIT_FAIL

    if degraded:
        print("DEGRADED: no failures found, but some results are unreliable. "
              "Treat as not checked.")
        return EXIT_DEGRADED

    print("OK: no overhang or thin-wall violation found.")
    return EXIT_OK


if __name__ == "__main__":
    _exit = main()
    try:
        from validation_log import log_run
        _label = {0: "OK", 2: "DEGRADED", 3: "FAIL", 4: "USAGE_ERROR"}.get(_exit, f"exit={_exit}")
        log_run("printability", _exit, "check_printability.py " + " ".join(sys.argv[1:]), _label)
    except Exception:
        pass
    sys.exit(_exit)
