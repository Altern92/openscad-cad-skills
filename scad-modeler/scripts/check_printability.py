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

P38 additions (2026-11-27): build volume (--bed), overhang REGIONS with a
1 mm^2 area floor and a facet tolerance, bridge span (<= 5 mm), and a
bed-contact WARN. The rules and their thresholds are re-written here (not
copied) from the ideas in earthtojake/text-to-cad
(https://github.com/earthtojake/text-to-cad, MIT, packages/cad printing
rules); no source from it is included in this file. Each threshold below names
its source URL; one marked "unverified" is our own value and only warns.

SCOPE -- what this does NOT check
----------------------------------
- Bridging is a COARSE check (see _bridge_span): a flat ceiling carried on
  two opposite sides; arches, diagonal bridges and cantilevers are not
  classified, a cantilever stays an UNSUPPORTED OVERHANG.
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
        --nozzle-d 0.4 --min-wall 0.8 --bed 220 220 250

Exit codes:
    0  pass
    2  degraded (mesh not watertight, or ray-casting failed for some
       samples -- treat as not fully checked)
    3  fail -- overhang, bridge span, build volume or thin-wall violation found
       (the bed-contact corner WARN never changes the exit code)
    4  usage error
"""
import argparse
import os
import sys

EXIT_OK, EXIT_DEGRADED, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4


# Thresholds. Sources verified 2026-11-27 (page text read).
# 45 deg: Hubs "an overhang can usually be printed up to 45" --
#   https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
# 5 mm bridge: same page, "unless the bridge is less than 5mm" (also
#   https://xometry.pro/en/articles/fdm-design-tips/ "Bridges longer than 5 mm").
BRIDGE_MAX_MM = 5.0
# 5 deg "flat": text-to-cad's own cut-off for a flat (bridge) ceiling; unverified, no guide gives it.
# It only CLASSIFIES: a region that is not flat (or not carried) stays an overhang judged by the
# verified 45 deg rule, and a flat region is already flagged by that rule, so changing this value
# can move a region between "bridge" and "overhang" but never turns a PASS into a FAIL.
FLAT_DEG = 5.0
# 1 mm^2 region floor: text-to-cad's own OVERHANG_AREA_MM2; unverified, no guide gives it.
MIN_REGION_MM2 = 1.0
# 1 deg facet tolerance: our own value for tessellation/STL-rounding noise on faceted curves
# (a 45 deg design must not read 44.99 and FAIL). unverified. A bare cone is already safe
# (inscribed facets are steeper from horizontal); arches and sphere facets are not.
# shortcut: fixed 1 deg, upgrade to a per-facet chord tolerance if coarse $fn parts false-flag.
FACET_TOL_DEG = 1.0
# 256^3: the Bambu Lab X1/P1 plate size, unverified here (no page fetched); Hubs gives 200^3 as
# typical desktop, up to 900x600x900 -- https://www.hubs.com/knowledge-base/3d-printing-geometry-restrictions/
DEFAULT_BED = (256.0, 256.0, 256.0)
# 100 deg: a first-layer corner sharper than this warns. Our own threshold (unverified); the advice
# is Hubs "include a 45 chamfer or radius on all edges touching the build plate" --
#   https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
SHARP_CORNER_DEG = 100.0
# 50 mm: only a footprint with a side this long warns (warping grows with length); our own
# advisory value, unverified.
WARP_MIN_SIDE_MM = 50.0
# 80 %: carried edges at each end must cover this share of the region's length along the other
# axis for it to count as a bridge (else it is a cantilever/partial support); our own value, unverified.
CARRIED_COVER = 0.8
# P38 rest (2026-11-27), all three informational/warning only, none changes the exit code:
# 45 deg knife edge: a convex edge whose two faces close at less than this. text-to-cad's own
# KNIFE_DEG; Hubs' 45 deg is only context (an overhang limit, not an edge rule). unverified.
KNIFE_DEG = 45.0
# 20 deg stair-step: an up-facing slope shallower than this (from horizontal) shows layer steps.
# our own value (text-to-cad uses its own SHALLOW_DEG); unverified. Below 0.5 deg = flat, no step.
STAIR_DEG = 20.0
STAIR_FLAT_DEG = 0.5
# 0.2 mm layer height: common FDM default, our own; unverified (set --layer).
DEFAULT_LAYER_MM = 0.2


def _regions(mesh, mask):
    """Connected components (shared-edge) of the faces selected by mask."""
    import numpy as np
    import trimesh
    idx = np.flatnonzero(mask)
    if not len(idx):
        return []
    adj = mesh.face_adjacency
    keep = mask[adj[:, 0]] & mask[adj[:, 1]]
    return [np.asarray(c) for c in
            trimesh.graph.connected_components(adj[keep], nodes=idx, min_len=1)]


def _bridge_span(mesh, faces, up):
    """Span (mm) of a flat down-facing region carried on two opposite sides, else None.
    A region edge is 'carried' when the face across it lies below the ceiling (a wall going
    down); an edge whose neighbour is above it is open. A direction counts as a bridge when
    carried edges touch both ends of the region's extent along it.
    shortcut: extent of the region's bounding box along two in-plane axes, so a diagonal or
    L-shaped bridge is overestimated; upgrade to text-to-cad's per-point span (meshops_printing
    `span`, ~70 lines) if a real part false-fails."""
    import numpy as np
    inr = np.zeros(len(mesh.faces), bool)
    inr[faces] = True
    adj = mesh.face_adjacency
    cross = inr[adj[:, 0]] ^ inr[adj[:, 1]]
    other = np.where(inr[adj[:, 0]], adj[:, 1], adj[:, 0])[cross]
    ev = mesh.vertices[mesh.face_adjacency_edges[cross]]   # (n, 2, 3) edge end points
    mid = ev.mean(axis=1)
    h = mesh.triangles_center.dot(up)
    carried = h[other] < h[faces].mean() - 1e-4
    if not carried.any():
        return None
    pts, evc = mid[carried], ev[carried]
    u = np.cross(up, [1.0, 0, 0] if abs(up[0]) < 0.9 else [0, 1.0, 0])
    u /= np.linalg.norm(u)
    reg = mesh.triangles[faces].reshape(-1, 3)
    spans = []
    for ax in (u, np.cross(up, u)):
        lo, hi = reg.dot(ax).min(), reg.dot(ax).max()
        ob = np.cross(up, ax)
        olo, ohi = reg.dot(ob).min(), reg.dot(ob).max()
        p, qe = pts.dot(ax), evc.dot(ob)
        ok = True
        for end in (p <= lo + 0.1 * (hi - lo), p >= hi - 0.1 * (hi - lo)):
            # shortcut: min..max of the carried points, so two posts at the far corners count as
            # full cover; upgrade to a union of edge intervals if such a part false-passes.
            ok = ok and end.any() and (qe[end].max() - qe[end].min()) >= CARRIED_COVER * (ohi - olo)
        if ok:
            spans.append(hi - lo)
    return float(min(spans)) if spans else None


def check_overhang(mesh, build_axis, overhang_deg, baseplate_eps):
    """Flag downward faces within overhang_deg of pointing straight down
    (theta < 90 - overhang_deg - FACET_TOL_DEG, theta = angle between the
    face normal and straight down), group them into connected REGIONS,
    drop regions under MIN_REGION_MM2, and split off flat ceilings carried
    on two sides as bridges (<= BRIDGE_MAX_MM is fine, longer is reported
    separately). Bridges are only classified while the overhang check is on
    (overhang_deg < 90). Returns a dict: total_down_area, worst_angle,
    regions [(area, centre)], bridges [(area, span, centre)], small (count
    of ignored regions).

    Faces resting directly on the build plate (centroid height along
    build_axis within baseplate_eps of the mesh's own minimum height) are
    excluded -- they are supported BY THE PLATE. Confirmed as a real bug
    during testing: a plain 20mm cube's flat bottom face was initially
    flagged before this exclusion was added.
    """
    import numpy as np
    normals = mesh.face_normals
    areas = mesh.area_faces
    up = np.array(build_axis, dtype=float)
    up = up / np.linalg.norm(up)
    heights = mesh.triangles_center.dot(up)
    on_baseplate = heights <= (heights.min() + baseplate_eps)

    cos_theta = normals.dot(-up)
    downward = (cos_theta > 0) & ~on_baseplate
    out = dict(total_down_area=0.0, worst_angle=None, regions=[], bridges=[], small=0)
    if not np.any(downward):
        return out
    theta = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))
    out["total_down_area"] = float(areas[downward].sum())
    out["worst_angle"] = float(theta[downward].min())
    flagged = downward & (theta < (90.0 - overhang_deg - FACET_TOL_DEG))

    def centre(c):
        return (mesh.triangles_center[c] * areas[c][:, None]).sum(axis=0) / areas[c].sum()

    if overhang_deg < 90.0:
        for c in _regions(mesh, flagged & (theta < FLAT_DEG)):
            span = _bridge_span(mesh, c, up)
            if span is not None:
                flagged[c] = False
                if areas[c].sum() >= MIN_REGION_MM2:
                    out["bridges"].append((float(areas[c].sum()), span, centre(c)))
    out["faces"] = np.zeros(len(areas), bool)   # faces of the kept regions (for the support estimate)
    for c in _regions(mesh, flagged):
        a = float(areas[c].sum())
        if a < MIN_REGION_MM2:
            out["small"] += 1
        else:
            out["regions"].append((a, centre(c)))
            out["faces"][c] = True
    return out


def check_knife_edges(mesh):
    """Convex edges whose interior dihedral angle is under KNIFE_DEG: [(angle_deg, length, midpoint)].
    Interior angle = 180 - angle between the two face normals; only convex edges count (a concave
    groove is not a knife). Rewritten from the idea in text-to-cad, no code copied.
    shortcut: per mesh edge, not merged into chains, so a long knife prints once per edge piece
    (the caller caps the listing); upgrade to chains if the output is noisy."""
    import numpy as np
    adj = mesh.face_adjacency
    if not len(adj):
        return []
    interior = 180.0 - np.degrees(mesh.face_adjacency_angles)
    hit = mesh.face_adjacency_convex & (interior < KNIFE_DEG)
    ev = mesh.vertices[mesh.face_adjacency_edges[hit]]
    return [(float(a), float(np.linalg.norm(e[1] - e[0])), e.mean(axis=0))
            for a, e in zip(interior[hit], ev)]


def check_stair_steps(mesh, build_axis, layer, baseplate_eps):
    """Up-facing regions shallower than STAIR_DEG (and steeper than STAIR_FLAT_DEG) from horizontal:
    [(area, mean_angle, cusp_mm, step_width_mm, centre)]. cusp = layer*cos(angle), step = layer/tan(angle)."""
    import numpy as np
    up = np.array(build_axis, dtype=float)
    up /= np.linalg.norm(up)
    tilt = np.degrees(np.arccos(np.clip(mesh.face_normals.dot(up), -1.0, 1.0)))
    areas = mesh.area_faces
    mask = (tilt > STAIR_FLAT_DEG) & (tilt < STAIR_DEG)
    out = []
    for c in _regions(mesh, mask):
        a = float(areas[c].sum())
        ang = float(np.average(tilt[c], weights=areas[c]))
        ctr = (mesh.triangles_center[c] * areas[c][:, None]).sum(axis=0) / a
        out.append((a, ang, layer * np.cos(np.radians(ang)), layer / np.tan(np.radians(ang)), ctr))
    return sorted(out, key=lambda r: -r[0])


def check_support_volume(mesh, faces, build_axis, cap=3000):
    """Estimate (mm^3) of support under the overhang faces: for each face, projected area times the
    drop to the first surface below (else down to the plate = mesh minimum). One downward ray per
    face centroid, sampled to `cap` faces and scaled back by projected area.
    shortcut: centroid column per face, so a face over a slope is approximated by its centre height;
    upgrade to text-to-cad's raster columns (meshops_printing `support`) if estimates matter."""
    import numpy as np
    up = np.array(build_axis, dtype=float)
    up /= np.linalg.norm(up)
    idx = np.flatnonzero(faces)
    if not len(idx):
        return 0.0
    proj = mesh.area_faces[idx] * mesh.face_normals[idx].dot(-up)
    scale = 1.0
    if len(idx) > cap:
        sel = np.random.default_rng(0).choice(len(idx), cap, replace=False)
        scale = proj.sum() / proj[sel].sum()
        idx, proj = idx[sel], proj[sel]
    org = mesh.triangles_center[idx] - up * 1e-3
    loc, ray, _ = trimesh_ray_intersector(mesh).intersects_location(org, np.tile(-up, (len(idx), 1)),
                                                                     multiple_hits=False)
    floor = mesh.vertices.dot(up).min()
    drop = org.dot(up) - floor
    for p, r in zip(loc, ray):
        drop[r] = min(drop[r], org[r].dot(up) - p.dot(up))
    return float((proj * np.maximum(drop, 0)).sum() * scale)


def _build_extents(mesh, build_axis):
    """Part extents as (across1, across2, along build axis) so they compare with bed (X, Y, Z).
    Axis-aligned build axis: the other two STL axes in order; otherwise projections on the axis
    and two in-plane axes (x-ish first)."""
    import numpy as np
    up = np.array(build_axis, dtype=float)
    up /= np.linalg.norm(up)
    k = int(np.argmax(abs(up)))
    if abs(up[k]) > 0.999:
        e = mesh.extents
        return [float(e[i]) for i in range(3) if i != k] + [float(e[k])]
    u = np.cross(up, [1.0, 0, 0] if abs(up[0]) < 0.9 else [0, 1.0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(up, u)
    return [float(np.ptp(mesh.vertices.dot(a))) for a in (v, u, up)]


def check_build_volume(mesh, bed, build_axis=(0, 0, 1)):
    """(fits, turned) -- bbox extents (STL axes) vs bed; turned = an axis permutation (a 90 deg
    turn) that fits when the as-modelled orientation does not, else None.
    Z of the bed is compared with the extent along build_axis.
    shortcut: axis-aligned bbox only, no free rotation; upgrade to text-to-cad's hull rotation
    (meshops_printing `lie`) for angled parts."""
    import itertools
    ext = _build_extents(mesh, build_axis)
    fits = all(e <= b + 1e-6 for e, b in zip(ext, bed))
    if fits:
        return True, None
    for perm in itertools.permutations(ext):
        if all(e <= b + 1e-6 for e, b in zip(perm, bed)):
            return False, perm
    return False, None


def check_bed_contact(mesh, build_axis, baseplate_eps):
    """Vertices of the plate-contact faces whose summed corner angle is <= SHARP_CORNER_DEG
    (a convex corner of the first-layer footprint). Interior angle at a vertex = sum of the
    contact triangles' corner angles there; a straight edge is 180, a rectangle corner 90."""
    import numpy as np
    up = np.array(build_axis, dtype=float)
    up /= np.linalg.norm(up)
    h = mesh.triangles_center.dot(up)
    contact = (h <= h.min() + baseplate_eps) & (mesh.face_normals.dot(-up) > 0.99)
    if not contact.any():
        return []
    ang = np.zeros(len(mesh.vertices))
    np.add.at(ang, mesh.faces[contact].ravel(), np.degrees(mesh.face_angles[contact]).ravel())
    cv = mesh.vertices[np.unique(mesh.faces[contact])]
    side = max(float(np.ptp(cv.dot(a))) for a in (np.cross(up, [1.0, 0, 0] if abs(up[0]) < 0.9 else [0, 1.0, 0]),
                                                  np.cross(up, np.cross(up, [1.0, 0, 0] if abs(up[0]) < 0.9 else [0, 1.0, 0]))))
    if side < WARP_MIN_SIDE_MM:
        return []
    return [mesh.vertices[i] for i in np.flatnonzero((ang > 0) & (ang <= SHARP_CORNER_DEG))]


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
    ap.add_argument("--bed", type=float, nargs=3, metavar=("X", "Y", "Z"), default=None,
                     help="printer build volume in mm (default 256 256 256, unverified "
                          "Bambu-class size); the part bbox in the STL's own axes must fit")
    ap.add_argument("--layer", type=float, default=DEFAULT_LAYER_MM,
                     help="layer height in mm for the stair-stepping INFO (default 0.2, unverified)")
    args = ap.parse_args()

    try:
        import trimesh
    except ImportError:
        __import__("mesh_python").reexec()
        print("ERROR: trimesh not installed. Run: bash scripts/setup_env.sh", file=sys.stderr)
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

    bed = tuple(args.bed) if args.bed else DEFAULT_BED
    fits, turned = check_build_volume(mesh, bed, build_axis)
    ext = _build_extents(mesh, build_axis)
    print(f"Build volume: part {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm (build axis last) vs bed "
          f"{bed[0]:g} x {bed[1]:g} x {bed[2]:g} mm"
          f"{'' if args.bed else ' (default bed, unverified: set --bed)'}"
          f" -- {'fits' if fits else 'DOES NOT FIT'}.")
    if not fits:
        hint = (f" It would fit after a 90 deg turn (extents {turned[0]:.1f} x {turned[1]:.1f} "
                f"x {turned[2]:.1f}); that changes the build direction, re-check overhang."
                if turned else " No 90 deg turn fits either.")
        msg = (f"part {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm exceeds bed "
               f"{bed[0]:g} x {bed[1]:g} x {bed[2]:g} mm.{hint}")
        if args.bed:
            failures.append("BUILD VOLUME: " + msg + " Hint: shrink the part, split it, or pass the real --bed X Y Z.")
        else:  # AC-C2: the default bed is unverified, so it can only warn
            print("WARN: BUILD VOLUME: " + msg + " (default bed 256^3 unverified; pass --bed X Y Z)")

    ov = check_overhang(mesh, build_axis, args.overhang_deg, args.baseplate_eps)
    if ov["total_down_area"] == 0.0:
        print("Overhang: no downward-facing area at all -- nothing to flag.")
    else:
        bad_area = sum(a for a, _ in ov["regions"])
        total_down_area = ov["total_down_area"]
        pct = 100.0 * bad_area / total_down_area
        print(f"Overhang: {bad_area:.1f} mm^2 of {total_down_area:.1f} mm^2 downward-"
              f"facing area ({pct:.1f}%) exceeds {args.overhang_deg:.0f} deg from "
              f"vertical (worst face {90.0 - ov['worst_angle']:.1f} deg from vertical).")
        for i, (a, c) in enumerate(ov["regions"], 1):
            print(f"  overhang region {i}: {a:.1f} mm^2, centre ({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f})")
        if ov["small"]:
            print(f"  {ov['small']} region(s) under {MIN_REGION_MM2:g} mm^2 ignored "
                  f"(floor unverified: text-to-cad's own value).")
        for a, span, c in ov["bridges"]:
            ok = span <= BRIDGE_MAX_MM
            print(f"  bridge: {a:.1f} mm^2 flat ceiling carried both sides, span {span:.1f} mm "
                  f"at ({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f}) -- "
                  f"{'ok (<= %g mm)' % BRIDGE_MAX_MM if ok else 'TOO LONG'}")
            if not ok:
                failures.append(
                    f"BRIDGE SPAN: flat ceiling {a:.1f} mm^2 at ({c[0]:.1f}, {c[1]:.1f}, "
                    f"{c[2]:.1f}) spans {span:.1f} mm > {BRIDGE_MAX_MM:g} mm between its supports "
                    f"-- will sag. Hint: add a support under the span, split it, or change the print orientation.")
        if bad_area > 0.0:
            failures.append(
                f"UNSUPPORTED OVERHANG: {bad_area:.1f} mm^2 in {len(ov['regions'])} region(s) "
                f"steeper than {args.overhang_deg:.0f} deg from vertical "
                f"(build axis {build_axis}) "
                f"-- will need support material or a different print orientation. Hint: change the "
                f"print orientation, or add a chamfer/45 deg slope on the overhanging faces.")

    if ov["total_down_area"] and ov["faces"].any():
        vol = check_support_volume(mesh, ov["faces"], build_axis)
        print(f"INFO: SUPPORT VOLUME: about {vol:.0f} mm^3 of support under the flagged overhang "
              f"region(s), down to the plate or the part below (estimate: centroid columns; "
              f"informational only).")

    knives = check_knife_edges(mesh)
    if knives:
        knives.sort(key=lambda k: k[0])
        where = "; ".join(f"{a:.0f} deg at ({m[0]:.1f}, {m[1]:.1f}, {m[2]:.1f}) len {ln:.1f}"
                          for a, ln, m in knives[:4])
        print(f"WARN: KNIFE EDGE: {len(knives)} convex edge piece(s) sharper than {KNIFE_DEG:g} deg, "
              f"e.g. {where} -- thin sharp edges print poorly and break; add a chamfer or radius "
              f"(threshold unverified: text-to-cad's own value).")

    stairs = check_stair_steps(mesh, build_axis, args.layer, args.baseplate_eps)
    if stairs:
        a, ang, cusp, step, c = stairs[0]
        print(f"INFO: STAIR STEPPING: {len(stairs)} up-facing slope region(s) under {STAIR_DEG:g} deg "
              f"from horizontal at layer {args.layer:g} mm; largest {a:.1f} mm^2 at "
              f"({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f}), {ang:.1f} deg, step width {step:.1f} mm, "
              f"cusp {cusp:.2f} mm (threshold unverified; informational only).")

    corners = check_bed_contact(mesh, build_axis, args.baseplate_eps)
    if corners:
        where = ", ".join(f"({c[0]:.1f}, {c[1]:.1f})" for c in corners[:4])
        print(f"WARN: BED CONTACT: {len(corners)} sharp corner(s) (<= {SHARP_CORNER_DEG:g} deg) on "
              f"the plate-contact face, e.g. {where} -- sharp first-layer corners lift/warp; "
              f"add a 45 deg chamfer or radius (threshold unverified: our own value; advice: Hubs).")

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
                    f"below threshold) -- likely to fail or warp during printing. Hint: thicken the wall in the part's "
                    f".scad to at least {min_wall:.2f} mm, or lower the wall limit only if the printer can hold it.")
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
