#!/usr/bin/env python3
"""P32 / P36: do declared fits hold, and is every near-contact declared?

joints.json "contacts" entries may carry a "fit" (parts = names of build/positioned/<name>.stl):
  {"pair": ["peg", "plate"], "fit": {"peg": "peg", "hole": "plate", "clearance_mm": 0.2}}
  {"pair": ["shaft", "hub"], "fit": {"peg": "shaft", "hole": "hub", "iso286": "H7/g6", "nominal_mm": 10}}
optional "axis": [x,y,z] and "at": [x,y,z] (default: the peg's longest bbox axis, at the point where the
peg surface is closest to the hole part). Peg and hole Ø are measured on the plane through "at"
normal to the axis: 24 rays from the section centre, median first-hit distance (so a stepped peg is
measured at the contact, not at its head).
  clearance_mm: FAIL when hole - peg is outside clearance +- --tol (default 0.05 mm, provisional).
  seat_depth_mm (optional): FAIL when the bore of Ø hole (+-0.1) runs shorter than this along the axis around "at"
  (a bearing or bushing not seated its full width; a shoulder or smaller hole ends the seat).
  iso286: FAIL when the hole is outside its class limits or the peg outside its own (+- --meas-tol,
  0.01 mm of mesh/tessellation noise). Subset: H7 H8 | g6 h6 k6 p6, nominal over 3 up to 50 mm.

P36: two parts whose surfaces are within --near mm (0.3) over >= --min-area mm2 (1.0) and that are in
no joints.json contact -> WARN (FAIL with --strict). Both numbers are unverified defaults.

shortcut: round pegs/holes only (ray-median Ø); area = fraction of 0.1 mm2-weighted surface samples
within --near of the other mesh, min of both directions. Upgrade to section polygons for non-round fits.
Exit: 0 ok / SKIP (also WARN), 3 fail, 4 usage.
"""
import argparse
import glob
import itertools
import json
import os
import sys

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4

try:
    import numpy as np
    import trimesh
except ImportError:
    __import__("mesh_python").reexec()
    print("ERROR: trimesh not installed. Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)

# ISO 286-2:2010 limit deviations in micrometres (lower, upper), nominal size ranges over 3 up to 6,
# 10, 18, 30, 50 mm. Source (checked 2026-11-27): RoyMech "ISO 286-2 Hole/Shaft Tolerance Limits - 3 to
# 400 mm", https://www.roymech.co.uk/Useful_Tables/ISO_Tolerances/ISO_286_2H.html and .../ISO_286_2s.html;
# cross-checked there on the worked example 40 H7 = +0/+25, 40 g6 = -25/-9 (39.975-39.991 mm), and on
# Wikipedia "Engineering fit" (50 mm: H7 0/+25, k6 +2/+18).
RANGES = [(3, 6), (6, 10), (10, 18), (18, 30), (30, 50)]
ISO = {
    "H7": [(0, 12), (0, 15), (0, 18), (0, 21), (0, 25)],
    "H8": [(0, 18), (0, 22), (0, 27), (0, 33), (0, 39)],
    "g6": [(-12, -4), (-14, -5), (-17, -6), (-20, -7), (-25, -9)],
    "h6": [(-8, 0), (-9, 0), (-11, 0), (-13, 0), (-16, 0)],
    "k6": [(1, 9), (1, 10), (1, 12), (2, 15), (2, 18)],
    "p6": [(12, 20), (15, 24), (18, 29), (22, 35), (26, 42)],
    # The rows above also match, all 60 cells for 4-30 mm, Bethune "Engineering Design and Graphics with
    # SolidWorks 2016" (Pearson), appendix "Preferred Clearance / Transition and Interference Fits (Hole
    # Basis; ANSI B4.2)", PDF pp. 773-774. The classes below come only from those pages, so up to 30 mm
    # (None = not verified; u6 changes at 24 mm, so it stops at 18).
    "H9": [(0, 30), (0, 36), (0, 43), (0, 52), None],
    "H11": [(0, 75), (0, 90), (0, 110), (0, 130), None],
    "c11": [(-145, -70), (-170, -80), (-205, -95), (-240, -110), None],
    "d9": [(-60, -30), (-76, -40), (-93, -50), (-117, -65), None],
    "f7": [(-22, -10), (-28, -13), (-34, -16), (-41, -20), None],
    "n6": [(8, 16), (10, 19), (12, 23), (15, 28), None],
    "s6": [(19, 27), (23, 32), (28, 39), (35, 48), None],
    "u6": [(23, 31), (28, 37), (33, 44), None, None],
}


def iso_limits(cls, nominal):
    """(min, max) mm of class `cls` at `nominal` mm."""
    for i, (lo, hi) in enumerate(RANGES):
        if lo < nominal <= hi:
            e = ISO[cls][i]
            if e is None:
                raise ValueError(f"{cls} at {nominal:g} mm is not in the verified table")
            return nominal + e[0] / 1000.0, nominal + e[1] / 1000.0
    raise ValueError(f"nominal {nominal} mm outside the supported range over 3 up to 50 mm")


def section_dia(mesh, c, ax, n=24):
    """Median first-hit radius*2 from point c in the plane normal to ax; None when under 3/4 of rays hit."""
    u = np.cross(ax, [1, 0, 0] if abs(ax[0]) < 0.9 else [0, 1, 0])
    u /= np.linalg.norm(u)
    v = np.cross(ax, u)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False) + 0.1
    d = np.outer(np.cos(ang), u) + np.outer(np.sin(ang), v)
    loc, ray, _ = trimesh.ray.ray_triangle.RayMeshIntersector(mesh).intersects_location(
        np.tile(c, (n, 1)), d, multiple_hits=False)
    if len(ray) < 0.75 * n:
        return None
    return 2 * float(np.median(np.linalg.norm(loc - c, axis=1)))


def seat_length(hole, cen, ax, hd, step=0.1, limit=200.0):
    """P32 (2026-11-28): length of the bore around cen whose Ø stays within 0.1 mm of hd (a shoulder, a step to a
    smaller hole or an open end stops it). shortcut: 0.1 mm steps, so the result is good to ~0.1 mm."""
    n = 0
    for sgn in (1, -1):
        t = step
        while t < limit:
            d = section_dia(hole, cen + sgn * t * ax, ax)
            if d is None or abs(d - hd) > 0.1:
                break
            t += step
        n += t - step
    return n


def section_centre(mesh, at, ax):
    s = mesh.section(plane_origin=at, plane_normal=ax)
    if s is None:
        return None
    v = s.vertices
    return (v.min(0) + v.max(0)) / 2


def closest_point(peg, hole):
    pts = trimesh.sample.sample_surface(peg, 3000, seed=0)[0]
    _, dist, _ = trimesh.proximity.closest_point(hole, pts)
    return pts[int(np.argmin(dist))]


def near_area(a, b, d):
    """Surface of `a` within d mm of `b`, mm2 (sampled, 0.1 mm2 per sample, 500..30000 samples)."""
    n = int(min(30000, max(500, a.area / 0.1)))
    pts = trimesh.sample.sample_surface(a, n, seed=0)[0]
    lo, hi = b.bounds[0] - d, b.bounds[1] + d
    pts = pts[((pts >= lo) & (pts <= hi)).all(axis=1)]
    if not len(pts):
        return 0.0
    _, dist, _ = trimesh.proximity.closest_point(b, pts)
    return a.area * float((dist < d).sum()) / n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--positioned", default=None, help="dir of positioned STLs (default <project>/build/positioned)")
    ap.add_argument("--joints", default=None, help="joints.json (default <project>/joints.json)")
    ap.add_argument("--tol", type=float, default=0.05, help="mm around a declared clearance (provisional)")
    ap.add_argument("--meas-tol", type=float, default=0.01, help="mm of measurement noise on ISO limits")
    ap.add_argument("--near", type=float, default=0.3, help="mm: surfaces closer than this are near-contact (unverified)")
    ap.add_argument("--min-area", type=float, default=1.0, help="mm2 of near-contact worth a warning (unverified)")
    ap.add_argument("--strict", action="store_true", help="undeclared near-contact FAILs instead of WARN")
    a = ap.parse_args()
    pos = a.positioned or os.path.join(a.project_dir, "build", "positioned")
    stls = sorted(glob.glob(os.path.join(pos, "*.stl")))
    if not stls:
        print(f"SKIP: fits, no positioned STLs in {pos} (run validate_scad.sh --all) -- not checked")
        return EXIT_OK
    jp = a.joints or os.path.join(a.project_dir, "joints.json")
    contacts = []
    if os.path.isfile(jp):
        try:
            data = json.load(open(jp))
            contacts = data.get("contacts", []) if isinstance(data, dict) else data
            contacts = [c for c in contacts if isinstance(c, dict) and "pair" in c]
        except (ValueError, AttributeError) as e:
            print(f"ERROR: {jp}: {e}", file=sys.stderr)
            return EXIT_USAGE
    paths = {os.path.splitext(os.path.basename(p))[0].lower(): p for p in stls}
    declared, fits = set(), []
    for c in contacts:
        declared.add(frozenset(str(x).lower() for x in c["pair"]))
        f = c.get("fit")
        if f is not None:
            try:
                fits.append((str(f["peg"]).lower(), str(f["hole"]).lower(), f))
                if "iso286" not in f and "clearance_mm" not in f:
                    raise KeyError("clearance_mm or iso286")
            except (KeyError, TypeError) as e:
                print(f"ERROR: {jp}: contact {c['pair']} has a malformed fit ({e})", file=sys.stderr)
                return EXIT_USAGE
            declared.add(frozenset((fits[-1][0], fits[-1][1])))
    unknown = {n for p, h, _ in fits for n in (p, h)} - set(paths)
    if unknown:
        print(f"ERROR: {jp} fit names no such positioned part: {', '.join(sorted(unknown))}", file=sys.stderr)
        return EXIT_USAGE
    meshes = {}

    def mesh(n):
        if n not in meshes:
            meshes[n] = trimesh.load(paths[n], force="mesh")
        return meshes[n]

    fails, warns, oks = [], [], []
    try:
        for pn, hn, f in fits:
            peg, hole = mesh(pn), mesh(hn)
            at = np.array(f["at"], float) if "at" in f else closest_point(peg, hole)
            if "axis" in f:
                ax = np.array(f["axis"], float)
                ax /= np.linalg.norm(ax)
            else:
                ax = np.eye(3)[int(np.argmax(peg.extents))]
            cen = section_centre(peg, at, ax)
            pd = section_dia(peg, cen, ax) if cen is not None else None
            hd = section_dia(hole, cen, ax) if cen is not None else None
            tag = f"fit {pn} in {hn} at ({at[0]:.1f}, {at[1]:.1f}, {at[2]:.1f})"
            if pd is None or hd is None:
                fails.append(f"{tag}: cannot measure Ø ({'peg' if pd is None else 'hole'} section has no closed wall "
                             f"along axis {np.round(ax, 2).tolist()}); give \"axis\" and \"at\" -- Hint: add \"axis\" and \"at\" to the fit in joints.json")
                continue
            if "seat_depth_mm" in f:   # P32: a bearing / bushing must sit its full width in the bore
                try:
                    want_seat = float(f["seat_depth_mm"])
                except (TypeError, ValueError):
                    print(f"ERROR: {jp}: fit {pn}/{hn}: seat_depth_mm must be a number", file=sys.stderr)
                    return EXIT_USAGE
                seat = seat_length(hole, cen, ax, hd)
                if seat < want_seat - 0.15:
                    fails.append(f"{tag}: seat {seat:.1f} mm < seat_depth_mm {want_seat:g} (bore Ø{hd:.3f} along "
                                 f"{np.round(ax, 2).tolist()}) -- Hint: deepen the bore to the part's width, or move the shoulder")
                else:
                    oks.append(f"{tag}: seat {seat:.1f} mm >= seat_depth_mm {want_seat:g}")
            if "iso286" in f:
                try:
                    hc, pc = f["iso286"].split("/")
                    nom = float(f["nominal_mm"])
                    hl, pl = iso_limits(hc, nom), iso_limits(pc, nom)
                except (KeyError, ValueError) as e:
                    print(f"ERROR: {jp}: fit {pn}/{hn}: {e} (supported: {', '.join(ISO)}; nominal_mm required)",
                          file=sys.stderr)
                    return EXIT_USAGE
                m = a.meas_tol
                bad = []
                if not hl[0] - m <= hd <= hl[1] + m:
                    bad.append(f"hole {hn} Ø{hd:.3f} outside {hc} [{hl[0]:.3f}, {hl[1]:.3f}] -- Hint: resize the hole to the class limits")
                if not pl[0] - m <= pd <= pl[1] + m:
                    bad.append(f"peg {pn} Ø{pd:.3f} outside {pc} [{pl[0]:.3f}, {pl[1]:.3f}] -- Hint: resize the peg to the class limits")
                # a clearance class (min clearance >= 0) must not measure as interference: each part may pass
                # its class only thanks to meas-tol, which is mesh noise, not tolerance budget
                if hl[0] - pl[1] >= 0 and hd - pd < 0:
                    bad.append(f"interference: hole Ø{hd:.3f} < peg Ø{pd:.3f} ({hd - pd:+.3f} mm) in clearance fit "
                               f"{f['iso286']}; --meas-tol {m:g} mm is a mesh-noise allowance on each class limit only -- Hint: enlarge the hole or shrink the peg to clear")
                (fails if bad else oks).append(f"{tag}: " + "; ".join(bad) if bad else
                                              f"{tag}: {f['iso286']} @ {nom:g} mm, hole Ø{hd:.3f}, peg Ø{pd:.3f} "
                                              f"(limits widened by --meas-tol {m:g} mm, a mesh-noise allowance)")
            else:
                c = hd - pd
                want = float(f["clearance_mm"])
                if abs(c - want) > a.tol:
                    fails.append(f"hole {hn} vs peg {pn} at ({at[0]:.1f}, {at[1]:.1f}, {at[2]:.1f}): clearance {c:.2f} "
                                 f"(hole Ø{hd:.3f}, peg Ø{pd:.3f}) is outside {want:.2f} +- {a.tol:.2f} -- Hint: resize the hole or the peg, or correct clearance_mm in the fit in joints.json")
                else:
                    oks.append(f"{tag}: clearance {c:.2f} (hole Ø{hd:.3f}, peg Ø{pd:.3f}), declared {want:.2f}")
        for x, y in itertools.combinations(sorted(paths), 2):
            if frozenset((x, y)) in declared:
                continue
            A, B = mesh(x), mesh(y)
            lo, hi = np.maximum(A.bounds[0], B.bounds[0]), np.minimum(A.bounds[1], B.bounds[1])
            if (hi + a.near < lo).any() or (lo - hi > a.near).any():
                continue
            area = min(near_area(A, B, a.near), near_area(B, A, a.near))
            if area >= a.min_area:
                ctr = (np.maximum(lo, hi) + np.minimum(lo, hi)) / 2
                warns.append(f"{x} <-> {y}: surfaces within {a.near:g} mm over ~{area:.0f} mm2 near "
                             f"({ctr[0]:.1f}, {ctr[1]:.1f}, {ctr[2]:.1f}) and the pair is untoleranced: declare it in "
                             f"joints.json \"contacts\" (touch / fit / expected_interference_mm) or open the gap")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: fits, cannot measure: {e}", file=sys.stderr)
        return EXIT_USAGE
    for m in oks:
        print(f"OK: {m}")
    for m in warns:
        print(f"{'FAIL' if a.strict else 'WARN'}: untoleranced contact {m}" + (" -- Hint: declare the pair in joints.json or open the gap" if a.strict else ""))
    for m in fails:
        print(f"FAIL: {m}")
    if fails or (warns and a.strict):
        return EXIT_FAIL
    if not fits and not warns:
        print("SKIP: fits, no fit declared in joints.json and no undeclared near-contact -- nothing to check")
        return EXIT_OK
    print(f"PASS: fits, {len(fits)} fit(s) checked, {len(warns)} warning(s)")
    return EXIT_OK


if __name__ == "__main__":
    _exit = main()
    try:
        from validation_log import log_run, label_for_exit
        log_run("fits", _exit, "check_fits.py " + " ".join(sys.argv[1:]), label_for_exit(_exit))
    except Exception:
        pass
    sys.exit(_exit)
