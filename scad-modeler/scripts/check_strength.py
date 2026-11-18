#!/usr/bin/env python3
"""Static strength of printed parts: heat-set insert holes and beam bending (P24, 2026-11-18).

INC-2026-11-18-07: 16 insert holes in the RC axles were cut at Ø4.6, the insert's own knurl OD
(CNC Kitchen: 4.0 drilled / 4.2 printed), 5.7-6.5 mm deep (blind needs L + 1). Every gate passed:
nothing measured an insert hole. This check does, on the positioned meshes (build/positioned).

INSERTS  fasteners.json entry with "insert": "M3" (size from references/inserts.json),
         "insert_in": "<part>" (substring of the positioned STL name), "insert_from": t (distance
         along the screw axis where the insert's top face sits; default thread_from). Measured:
         hole Ø in [D3 - 0.05, D3 + 0.35]; blind depth >= L + 1 (or the hole runs through);
         material all round at D3/2 + W.
LOADS    loads.json {"cases": [{"name", "part", "support": [x,y,z], "at": [x,y,z],
         "force_N": [fx,fy,fz], "print_up": [0,0,1], "material": "PETG Basic", "safety": 2.0,
         "reach": 30}]} in assembly coords. The positioned mesh is cut every 1 mm (>= 10 stations) between
         support and load (plane normal = support -> load); the section pieces within `reach` mm
         of the line form the beam section. sigma = |M_bending| c / I + |F_axial| / A, against the
         material's X-Y strength, or Z when the stress direction is within 30 deg of print_up
         (layers pulled apart). No section at a station = the part does not carry the load there.
Not FEA: no torsion, shear, stress concentration, fatigue or creep.

Usage: python3 check_strength.py --project-dir . [--fasteners fasteners.json] [--loads loads.json]
Exit: 0 pass, 3 fail, 4 usage (unknown insert size / material, bad JSON), 2 nothing to check.
"""
import argparse
import glob
import json
import os
import sys

EXIT_OK, EXIT_NONE, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    import numpy as np
    import trimesh
    from shapely.geometry import Polygon
    from check_fasteners import ring
except ImportError as e:
    __import__("mesh_python").reexec()
    print(f"ERROR: missing dependency ({e}). Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)

LAYER_DEG = 30.0
STATION_MM = 1.0   # cut at least every mm: a 4 mm gap between 5 mm stations passed (fixture bar_gap)


def usage(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def table(name):
    with open(os.path.join(HERE, "..", "references", name), encoding="utf-8") as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def find_mesh(meshes, sub, what):
    hit = [n for n in meshes if sub in n]
    if len(hit) != 1:
        usage(f"{what} {sub!r} matches {len(hit)} positioned STL(s) {hit} -- want exactly one")
    return meshes[hit[0]]


def hole_radius(m, c, ax, rmax):
    """Hole radius: per direction (12 round the axis) the first radius that is material, median of them.
    A full-ring test fails next to a thin side wall, where the ring leaves the part (fixture blk_wall)."""
    rs = np.arange(0.3, rmax, 0.025)
    pts = np.vstack([ring(c, ax, r) for r in rs])          # len(rs) rings x 12 directions
    inside = m.contains(pts).reshape(len(rs), -1)
    first = [rs[np.argmax(col)] if col.any() else rmax for col in inside.T]
    return float(np.median(first))


def check_insert(f, spec, m):
    s, ax = np.array(f["start"], float), np.array(f["axis"], float)
    ax /= np.linalg.norm(ax)
    t0 = float(f.get("insert_from", f.get("thread_from", 0.0)))
    L, D1, D3, W = spec["L"], spec["D1"], spec["D3"], spec["W"]
    out = []
    depths = np.linspace(t0 + 0.6, t0 + L - 0.6, 5)
    d = 2 * float(np.median([hole_radius(m, s + t * ax, ax, D1 / 2 + W + 1.0) for t in depths]))
    if not (D3 - 0.05 <= d <= D3 + 0.35):
        out.append(f"hole Ø{d:.2f} outside [{D3 - 0.05:.2f}, {D3 + 0.35:.2f}] (datasheet {D3}, knurl OD {D1})"
                   + (" -- a hole at the knurl OD leaves the knurls nothing to grip" if d >= D1 - 0.15 else ""))
    # bottom = where the hole narrows below the insert's hole (solid, or a screw clearance hole
    # continuing past it -- the axis alone saw that as "through", rear_axle_v4 2026-11-18)
    bottom = None
    for t in np.arange(t0 + 0.25, t0 + L + 3.0, 0.25):
        if m.contains(ring(s + t * ax, ax, D3 / 2 - 0.15)).all():
            bottom = t; break
    if bottom is not None and bottom - t0 < L + 1.0 - 0.05:
        out.append(f"blind depth {bottom - t0:.2f} mm < L + 1 = {L + 1.0:.1f} (insert bottoms out, melt has nowhere to go)")
    mid = s + (t0 + L / 2) * ax
    if not m.contains(ring(mid, ax, D3 / 2 + W)).all():
        out.append(f"wall under {W} mm around the hole (ring at r {D3 / 2 + W:.2f} leaves the part)")
    elif not m.contains(ring(s + (t0 + L - 0.3) * ax, ax, D1 / 2 + 0.3)).all():
        out.append(f"material ends before the insert does (no wall at {L - 0.3:.1f} mm of its {L} mm length): it sticks out")
    return d, bottom, out


def section_props(poly):
    """Area, centroid and second moments (about the centroid) of a shapely polygon with holes."""
    def ring_terms(xy):
        x, y = xy[:-1, 0], xy[:-1, 1]
        x1, y1 = xy[1:, 0], xy[1:, 1]
        cr = x * y1 - x1 * y
        a = cr.sum() / 2
        cx = ((x + x1) * cr).sum() / 6
        cy = ((y + y1) * cr).sum() / 6
        ixx = ((y * y + y * y1 + y1 * y1) * cr).sum() / 12      # int y^2
        iyy = ((x * x + x * x1 + x1 * x1) * cr).sum() / 12      # int x^2
        ixy = ((x * y1 + 2 * x * y + 2 * x1 * y1 + x1 * y) * cr).sum() / 24
        return np.array([a, cx, cy, ixx, iyy, ixy])
    tot = np.zeros(6)
    for p in getattr(poly, "geoms", [poly]):
        e = np.asarray(p.exterior.coords)
        tot += np.sign(ring_terms(e)[0]) * ring_terms(e)
        for h in p.interiors:
            hc = np.asarray(h.coords)
            tot -= np.sign(ring_terms(hc)[0]) * ring_terms(hc)
    A = tot[0]
    cx, cy = tot[1] / A, tot[2] / A
    Sxx = tot[4] - A * cx * cx          # int (x - cx)^2
    Syy = tot[3] - A * cy * cy
    Sxy = tot[5] - A * cx * cy
    return A, np.array([cx, cy]), Sxx, Syy, Sxy


def check_load(case, m, mats):
    S, P = np.array(case["support"], float), np.array(case["at"], float)
    F = np.array(case["force_N"], float)
    up = np.array(case.get("print_up", [0, 0, 1]), float); up /= np.linalg.norm(up)
    mat = mats.get(case.get("material", "PETG Basic"))
    if mat is None:
        usage(f"load {case.get('name')}: unknown material {case.get('material')!r} (references/materials.json: {sorted(mats)})")
    sf, reach = float(case.get("safety", 2.0)), float(case.get("reach", 30.0))
    n = (P - S) / np.linalg.norm(P - S)
    z_dir = abs(float(n @ up)) >= np.cos(np.radians(LAYER_DEG))
    allow = (mat["z_mpa"] if z_dir else mat["xy_mpa"]) / sf
    worst, fails, gaps = None, [], []
    nst = max(10, int(np.ceil(np.linalg.norm(P - S) / STATION_MM)))
    for k, u in enumerate(np.linspace(0.05, 0.95, nst)):
        p = S + u * (P - S)
        sec = m.section(plane_origin=p, plane_normal=n)
        polys = []
        if sec is not None:
            planar, to3 = sec.to_2D(normal=n)
            for poly in planar.polygons_full:
                c3 = (to3 @ np.r_[poly.centroid.x, poly.centroid.y, 0, 1])[:3]
                if np.linalg.norm(np.cross(c3 - S, n)) <= reach:
                    polys.append(poly)
        if not polys:
            gaps.append(p)
            continue
        from shapely.ops import unary_union
        A, c2, Sxx, Syy, Sxy = section_props(unary_union(polys))
        c3 = (to3 @ np.r_[c2[0], c2[1], 0, 1])[:3]
        Mv = np.cross(P - c3, F)
        Mb = Mv - (Mv @ n) * n                          # bending part; torsion (Mv . n) is not checked
        R = to3[:3, :3]
        mb2 = (R.T @ Mb)[:2]
        sig = abs(float(F @ n)) / A
        if np.linalg.norm(mb2) > 1e-9:
            e = mb2 / np.linalg.norm(mb2)
            mperp = np.array([-e[1], e[0]])             # distance from the neutral axis runs along mperp
            I = mperp[0] ** 2 * Sxx + 2 * mperp[0] * mperp[1] * Sxy + mperp[1] ** 2 * Syy
            pts = np.vstack([np.asarray(q.exterior.coords) for q in polys])
            cfar = float(np.max(np.abs((pts - c2) @ mperp)))
            sig += float(np.linalg.norm(Mb)) * cfar / I
        if worst is None or sig > worst[0]:
            worst = (sig, k + 1, A)
    if gaps:
        fails.append(f"no material at {len(gaps)}/{nst} station(s), first ({gaps[0][0]:.1f}, {gaps[0][1]:.1f}, "
                     f"{gaps[0][2]:.1f}) -- the part does not connect the support to the load")
    if worst and worst[0] > allow:
        fails.append(f"stress {worst[0]:.1f} MPa at station {worst[1]} (section {worst[2]:.1f} mm2) > "
                     f"{allow:.1f} MPa = {'Z (layers pulled apart)' if z_dir else 'X-Y'} "
                     f"{mat['z_mpa'] if z_dir else mat['xy_mpa']} / safety {sf}")
    return worst, allow, z_dir, fails


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--fasteners", default="fasteners.json")
    ap.add_argument("--loads", default="loads.json")
    ap.add_argument("stls", nargs="*", help="positioned STLs (default build/positioned/*.stl)")
    a = ap.parse_args()
    os.chdir(a.project_dir)
    fs = []
    if os.path.isfile(a.fasteners):
        try:
            fs = [f for f in json.load(open(a.fasteners)).get("fasteners", []) if f.get("insert")]
        except ValueError as e:
            usage(f"{a.fasteners}: {e}")
    cases = []
    if os.path.isfile(a.loads):
        try:
            cases = json.load(open(a.loads)).get("cases", [])
        except ValueError as e:
            usage(f"{a.loads}: {e}")
    if not fs and not cases:
        print("STRENGTH: nothing declared (no fasteners with \"insert\", no loads.json)")
        return EXIT_NONE
    stls = a.stls or sorted(glob.glob("build/positioned/*.stl"))
    if not stls:
        print("FAIL strength: no positioned STLs (build/positioned) -- nothing could be measured")
        return EXIT_FAIL
    meshes = {os.path.basename(p)[:-4]: trimesh.load(p, force="mesh") for p in stls}
    inserts, mats = table("inserts.json"), table("materials.json")
    total = 0
    for f in fs:
        spec = inserts.get(f["insert"])
        if spec is None:
            usage(f"{f.get('name')}: unknown insert {f['insert']!r} (references/inserts.json: {sorted(inserts)})")
        if not f.get("insert_in"):
            usage(f"{f.get('name')}: \"insert\" needs \"insert_in\" (the part the insert is melted into)")
        m = find_mesh(meshes, f["insert_in"], "insert_in")
        d, bottom, out = check_insert(f, spec, m)
        depth = "through" if bottom is None else f"{bottom - float(f.get('insert_from', f.get('thread_from', 0.0))):.2f}"
        print(f"{'FAIL' if out else 'OK  '} insert {f['insert']} {f.get('name', '?')}: Ø{d:.2f}, depth {depth}")
        for o in out:
            print(f"       {o}")
        total += len(out)
    for c in cases:
        m = find_mesh(meshes, c["part"], f"load {c.get('name')}: part")
        worst, allow, z_dir, out = check_load(c, m, mats)
        w = f"{worst[0]:.1f} MPa (allow {allow:.1f}, {'Z' if z_dir else 'X-Y'})" if worst else "no section"
        print(f"{'FAIL' if out else 'OK  '} load {c.get('name', '?')} on {c['part']}: {w}")
        for o in out:
            print(f"       {o}")
        total += len(out)
    print(f"STRENGTH: {len(fs)} insert(s), {len(cases)} load case(s), {total} failure(s)")
    return EXIT_FAIL if total else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
