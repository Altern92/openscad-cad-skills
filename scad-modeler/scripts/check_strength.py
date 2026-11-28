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
         Transverse shear (wave 2 / AC-E3): at every station tau = 1.5 V / A, V = the force component
         normal to the beam axis (Zhuravskii tau = V Q / (I b), https://en.wikipedia.org/wiki/Shear_stress
         "Beam shear"; Q = b h^2 / 8, I = b h^3 / 12 for a rectangle gives 1.5 V / A, derived; other
         sections: approximate). Allowed = "shear_mpa" / safety when the case gives a datasheet shear
         value (FAIL); else 0.6 x min(X-Y, Z) / safety, a rule of thumb (WARN only, not a datasheet value).
ANALYTIC CASES in loads.json["cases"] with "type" (no mesh needed; "force_N" is a number, N):
  "screw_pullout": {"thread_d_mm", "pitch_mm", "engagement_mm", "force_N", "material", "safety",
         "shear_mpa" (optional)} strip-out of the INTERNAL thread (the printed boss strips): tau = F / A against
         the same shear allowance as above, A = pi n Le Ds [1/(2n) + 0.57735 (Ds - En)] (Machinery's Handbook
         internal-thread shear area) with basic dimensions Ds = D, En = D - 0.649519 p, n = 1/p, i.e. ~0.875 pi D Le.
         Verified 2026-11-27 on Engineers Edge "Shear Area Internal & External Thread Formula per. Fed-STD-H28",
         https://www.engineersedge.com/thread_strength/thread_bolt_stress.htm (equation image asn.gif reads
         An = pi n Le Ds min (1/(2n) + 0.57735 (Ds min - En max)), Ds min = min major dia of external thread).
         Basic dimensions overestimate the area against tolerance limits (undersized hole, worn thread): the
         real margin is smaller.
  "press_fit": {"shaft_d_mm" (solid), "hub_od_mm", "interference_mm" (diametral), "hub_E_mpa", "hub_nu",
         "shaft_E_mpa", "shaft_nu", "axis" (default [0,0,1]), "print_up", "material", "safety"}.
         Lame (https://en.wikipedia.org/wiki/Cylinder_stress, "Thick-walled vessels"): hub bore hoop
         stress = p (D^2 + d^2) / (D^2 - d^2). Contact pressure p from Lame + Hooke (plane stress; ours,
         derived): delta = d p [ ((D^2 + d^2) / (D^2 - d^2) + nu_h) / E_h + (1 - nu_s) / E_s ].
         Hoop runs round the axis, so against X-Y strength when the axis is within 30 deg of print_up,
         else Z (it then crosses layers). No creep / stress relaxation: PETG presses relax over time.
Not FEA: no torsion, stress concentration, fatigue or creep.

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
    hit = [n for n in meshes if n == sub]  # P26 / AC-3b: exact -- "upright" must not also match upright_l
    if len(hit) != 1:
        usage(f"{what} {sub!r} matches {len(hit)} positioned STL(s) {hit} -- want exactly one")
    return meshes[hit[0]]


def hole_radius(m, c, ax, rmax):
    """Hole radius: per direction (12 round the axis) the first radius that is material, median of them.
    A full-ring test fails next to a thin side wall, where the ring leaves the part (fixture blk_wall)."""
    rs = np.arange(0.3, rmax, 0.025)
    pts = np.vstack([ring(c, ax, r) for r in rs])          # len(rs) rings x 12 directions
    inside = m.contains(pts).reshape(len(rs), -1)
    first = []
    dirs = ring(np.zeros(3), ax, 1.0)                        # the same 12 unit directions
    for j, col in enumerate(inside.T):
        if not col.any():
            first.append(rmax)
            continue
        k = int(np.argmax(col))
        lo, hi = (rs[k - 1] if k else 0.0), rs[k]
        for _ in range(4):   # P25 metamorphic test: 0.025 steps flipped 4.60/4.65 under rotation -> bisect to 0.002
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if m.contains([c + mid * dirs[j]])[0] else (mid, hi)
        first.append(hi)
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
                   + (" -- a hole at the knurl OD leaves the knurls nothing to grip" if d >= D1 - 0.15 else "")
                   + f" -- Hint: set the hole diameter to the datasheet {D3} mm in the part's .scad")
    # bottom = where the hole narrows below the insert's hole (solid, or a screw clearance hole
    # continuing past it -- the axis alone saw that as "through", rear_axle_v4 2026-11-18)
    bottom = None
    solid = lambda t: m.contains(ring(s + t * ax, ax, D3 / 2 - 0.15)).all()
    for t in np.arange(t0 + 0.25, t0 + L + 3.0, 0.25):
        if solid(t):
            lo, bottom = t - 0.25, t      # P27 / AC-2: bisect, a 0.25 mm grid rounded a 6.55 hole up to 6.75
            while bottom - lo > 0.01:
                mid = (lo + bottom) / 2
                lo, bottom = (lo, mid) if solid(mid) else (mid, bottom)
            break
    if bottom is not None and bottom - t0 < L + 1.0 - 0.05:
        out.append(f"blind depth {bottom - t0:.2f} mm < L + 1 = {L + 1.0:.1f} (insert bottoms out, melt has nowhere to go) -- Hint: drill the blind hole deeper, to at least L + 1")
    mid = s + (t0 + L / 2) * ax
    if not m.contains(ring(mid, ax, D3 / 2 + W)).all():
        out.append(f"wall under {W} mm around the hole (ring at r {D3 / 2 + W:.2f} leaves the part) -- Hint: thicken the wall around the insert hole to at least {W} mm")
    elif not m.contains(ring(s + (t0 + L - 0.3) * ax, ax, D1 / 2 + 0.3)).all():
        out.append(f"material ends before the insert does (no wall at {L - 0.3:.1f} mm of its {L} mm length): it sticks out -- Hint: extend the material over the whole insert length or shorten the insert")
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
    worst, fails, gaps, tau_w = None, [], [], 0.0
    shear, shear_given = shear_allow(case, mat, sf)
    V = np.linalg.norm(F - (F @ n) * n)
    nst = max(10, int(np.ceil(np.linalg.norm(P - S) / STATION_MM - 1e-6)))   # 50.0000001 mm is 50 stations
    # P26 / AC-8 (Fable audit e9): stations ran 5-95 %, so the root -- where the moment peaks -- was never cut
    # and a bar stopping 4.5 mm short of both ends passed. Now 0.2 mm inside each end.
    span = float(np.linalg.norm(P - S)); inset = min(0.2 / span, 0.05)
    from shapely.geometry import Point
    for k, u in enumerate(np.linspace(inset, 1 - inset, nst)):
        p = S + u * (P - S)
        sec = m.section(plane_origin=p, plane_normal=n)
        polys = []
        if sec is not None:
            planar, to3 = sec.to_2D(normal=n)
            p2 = (np.linalg.inv(to3) @ np.r_[p, 1])[:2]
            # one piece only (P26 / AC-8): the one the support-load line runs through, else the nearest within
            # reach. Unioning every piece in reach made an unloaded sibling prong carry the load (356 -> 5 MPa).
            cand = []
            for poly in planar.polygons_full:
                c3 = (to3 @ np.r_[poly.centroid.x, poly.centroid.y, 0, 1])[:3]
                if np.linalg.norm(np.cross(c3 - S, n)) <= reach:
                    cand.append((poly.distance(Point(p2)), poly))
            if cand:
                polys = [min(cand, key=lambda t: t[0])[1]]
        if not polys:
            gaps.append(p)
            continue
        A, c2, Sxx, Syy, Sxy = section_props(polys[0])
        c3 = (to3 @ np.r_[c2[0], c2[1], 0, 1])[:3]
        Mv = np.cross(P - c3, F)
        Mb = Mv - (Mv @ n) * n                          # bending part; torsion (Mv . n) is not checked
        R = to3[:3, :3]
        mb2 = (R.T @ Mb)[:2]
        sig = abs(float(F @ n)) / A
        if np.linalg.norm(mb2) > 1e-9:
            # P27 / AC-1 (Fable calculation audit): |M| c / I about the moment axis holds only on a principal
            # axis; an oblique load on a 20x2 bar read 5.9 MPa for ~30. Unsymmetric bending: sigma = a x + b y
            # (centroid origin) with Mx = int y sigma, My = -int x sigma; Sxx = int x^2, Syy = int y^2.
            a, b = np.linalg.solve(np.array([[Sxy, Syy], [Sxx, Sxy]]), np.array([mb2[0], -mb2[1]]))
            pts = np.vstack([np.asarray(q.exterior.coords) for q in polys]) - c2
            sig += float(np.max(np.abs(pts @ np.array([a, b]))))
        tau_w = max(tau_w, 1.5 * V / A)   # AC-E3: rectangle, tau = 1.5 V / A (Zhuravskii, Q = b h^2 / 8)
        if worst is None or sig > worst[0]:
            worst = (sig, k + 1, A)
    if gaps:
        g = np.asarray(gaps[0][:3], float)
        fails.append(f"no material at {len(gaps)}/{nst} station(s), first {np.linalg.norm(g - S):.1f} mm from the "
                     f"support [{g[0]:.1f}, {g[1]:.1f}, {g[2]:.1f}] -- the part does not connect the support to the load -- Hint: join the part so material runs from the support to the load point, or correct their coordinates in loads.json")
    if worst and worst[0] > allow:
        fails.append(f"stress {worst[0]:.1f} MPa at station {worst[1]} (section {worst[2]:.1f} mm2) > "
                     f"{allow:.1f} MPa = {'Z (layers pulled apart)' if z_dir else 'X-Y'} "
                     f"{mat['z_mpa'] if z_dir else mat['xy_mpa']} / safety {sf} -- Hint: enlarge the section "
                     f"at that station, or lower the load or change the material in loads.json")
    warns = []
    if tau_w > shear:
        (fails if shear_given else warns).append(f"shear {tau_w:.1f} MPa > {shear:.1f} MPa = "
            + (f"shear_mpa {case['shear_mpa']} / safety {sf}" if shear_given else f"{SHEAR_RULE} / safety {sf}, not a datasheet value (WARN only)")
            + " -- Hint: enlarge the web/section, or lower the shear load in loads.json")
    return worst, allow, z_dir, fails, warns, tau_w, shear


SHEAR_RULE = "0.6 x min(X-Y, Z) strength"  # rule of thumb for printed plastic, not a datasheet value


def shear_allow(case, mat, sf):
    """(allowed shear MPa, True when from a datasheet value in the case, else the 0.6 rule: WARN only)."""
    if case.get("shear_mpa") is not None:
        return float(case["shear_mpa"]) / sf, True
    return 0.6 * min(mat["xy_mpa"], mat["z_mpa"]) / sf, False


def check_pullout(c, mats):
    D, p, Le, F = (float(c[k]) for k in ("thread_d_mm", "pitch_mm", "engagement_mm", "force_N"))
    mat = material(c, mats); sf = float(c.get("safety", 2.0))
    n = 1.0 / p
    A = np.pi * n * Le * D * (1 / (2 * n) + 0.57735 * (D - (D - 0.649519 * p)))   # Fed-STD-H28, see module docstring
    tau = F / A
    allow, given = shear_allow(c, mat, sf)
    out = [f"tau {tau:.2f} MPa > {allow:.1f} (shear area {A:.1f} mm2) -- Hint: lengthen the engagement or use a larger thread, or lower the load in loads.json"] if tau > allow else []
    return tau, allow, given, out


def check_press_fit(c, mats):
    d, D, dl = (float(c[k]) for k in ("shaft_d_mm", "hub_od_mm", "interference_mm"))
    Eh, nh, Es, ns = (float(c[k]) for k in ("hub_E_mpa", "hub_nu", "shaft_E_mpa", "shaft_nu"))
    mat = material(c, mats); sf = float(c.get("safety", 2.0))
    k = (D * D + d * d) / (D * D - d * d)
    p = dl / (d * ((k + nh) / Eh + (1 - ns) / Es))
    hoop = p * k
    ax = np.array(c.get("axis", [0, 0, 1]), float); ax /= np.linalg.norm(ax)
    up = np.array(c.get("print_up", [0, 0, 1]), float); up /= np.linalg.norm(up)
    along = abs(float(ax @ up)) >= np.cos(np.radians(LAYER_DEG))   # hoop lies in the layers
    allow = (mat["xy_mpa"] if along else mat["z_mpa"]) / sf
    out = [f"hoop {hoop:.1f} MPa > {allow:.1f} MPa = {'X-Y' if along else 'Z (hoop crosses layers)'} strength / safety {sf} -- Hint: loosen the interference or thicken the wall around the press fit"] if hoop > allow else []
    return p, hoop, allow, along, out


def material(c, mats):
    m = mats.get(c.get("material", "PETG Basic"))
    if m is None:
        usage(f"load {c.get('name')}: unknown material {c.get('material')!r} (references/materials.json: {sorted(mats)})")
    return m


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
            doc = json.load(open(a.fasteners))   # bare list or {"fasteners": [...]} (P26 / AC-9)
            fs = [f for f in (doc if isinstance(doc, list) else doc.get("fasteners", [])) if f.get("insert")]
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
    if not stls and (fs or any(not c.get("type") for c in cases)):
        print("FAIL strength: no positioned STLs (build/positioned) -- nothing could be measured -- Hint: run validate_scad.sh --all to build the positioned STLs first")
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
        typ, nm, warns = c.get("type"), c.get("name", "?"), []
        try:
            if typ == "screw_pullout":
                tau, allow, given, out = check_pullout(c, mats)
                warns = [] if given or not out else out
                out = out if given else []
                head = f"screw_pullout {nm}: tau {tau:.2f} MPa (allow {allow:.1f}{'' if given else f', {SHEAR_RULE}, not a datasheet value'})"
            elif typ == "press_fit":
                p, hoop, allow, along, out = check_press_fit(c, mats)
                head = f"press_fit {nm}: contact {p:.2f} MPa, hoop {hoop:.1f} MPa (allow {allow:.1f}, {'X-Y' if along else 'Z'})"
            elif typ is None:
                m = find_mesh(meshes, c["part"], f"load {nm}: part")
                worst, allow, z_dir, out, warns, tau, sallow = check_load(c, m, mats)
                w = f"{worst[0]:.1f} MPa (allow {allow:.1f}, {'Z' if z_dir else 'X-Y'})" if worst else "no section"
                head = f"load {nm} on {c['part']}: {w}, shear {tau:.1f} MPa (allow {sallow:.1f})"
            else:
                usage(f"case {nm}: unknown type {typ!r} (screw_pullout, press_fit, or none = beam)")
        except KeyError as e:
            usage(f"case {nm}: missing field {e}")
        print(f"{'FAIL' if out else 'WARN' if warns else 'OK  '} {head}")
        for o in out + warns:
            print(f"       {o}")
        total += len(out)
    print(f"STRENGTH: {len(fs)} insert(s), {len(cases)} load case(s), {total} failure(s)")
    return EXIT_FAIL if total else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
