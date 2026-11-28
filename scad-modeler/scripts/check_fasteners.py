#!/usr/bin/env python3
"""Check every declared screw against the positioned assembly: head room, free shank, thread bite, no crossings.

Why (INC-2026-08-21-07, INC-2026-08-22-06, INC-2026-11-08-01): attachments.json only asks
"is there material at this point". Three real failures passed it:
  - a screw head sat under a panel mounted later -- the panel had no head hole, so it could not
    sit flat (cnc-valdymo-punktas 2026-11-08, found by the user);
  - a hidden vertical screw channel crossed horizontal EIA holes (server_rack part1);
  - holes on the wrong axis, screwdriver blocked by a side panel (server_rack part2).
All three are visible only when the screw is a line through the ASSEMBLED parts.

fasteners.json (project root, assembly coordinates, checked against build/positioned/*.stl):
[
  {"name": "base M4 FL",            # label in the report
   "start": [-113.5, -87, 12],      # centre of the head's bearing face (where the head seats)
   "axis": [0, 1, 0],               # direction the shank goes in (into the material)
   "d": 4,                          # nominal thread diameter
   "length": 16,                    # shank length under the head
   "head_d": 7, "head_h": 3.1,      # head envelope; this space must be free in every part
   "into": "frame_base",            # part the thread bites into (substring of the STL name);
                                    # null/absent = through-bolt with a nut, no bite check
   "thread_from": 3.6,              # shank distance where the pilot (tapped) part starts (default 0)
   "bite_from": 6.5,                # optional: where `into` material starts (default thread_from),
                                    # e.g. a screw through a post-wall pilot into a plug behind it
   "access_mm": 0,                  # optional: free straight tool path behind the head
   "into_material": "plastic",     # optional (default plastic): "aluminium" = FAIL below 2 d engagement (Tameson
                                   # chart), plastic = WARN below 1.5 d (◇ unverified); any other value = no check
   "insert": "M3", "insert_in": "part", "insert_from": 0,   # heat-set insert (inserts.json, as check_strength):
                                   # FAIL when the screw reaches less than the insert's length L into it
   "position_tol": 0.1}            # optional (mm): hole position error T (printer ~0.1, tolerances.md); FAIL when a
                                   # clearance hole is under F + T (through-bolt) or F + 2T (into/insert), Bethune 8-43/8-46;
                                   # into/insert needs thread_from; a through-bolt checks 0..thread_from
                                   # (set it to the stack thickness when a nut/washer is a part), else 0..length
]
Instanced parts (one part file placed several times, e.g. 4 identical corner posts): validate_scad.sh
renders one positioned STL per part FILE, so wrap the list as
  {"instances": ["frame_post_lower_fl", ...], "fasteners": [...]}
and every instance name is rendered with assembly.scad MODE="part" PART="<name>" into build/positioned/.

Parts made outside parts/*.scad (P20, INC-2026-11-13-02): a Python/trimesh script exports each part
to build/positioned/<name>.stl and the same checks apply; validate_scad.sh runs them without an
assembly.scad. Declare what each such part is bolted to, so a part with no screws at all FAILs:
  {"mounts": [{"part": "z_motor_mount", "on": "z_plate", "min": 2}], "fasteners": [...]}
  mount   : >= min (default 1) declared fasteners whose shank passes through `part` (a ring just
            outside the shank meets its material) and whose `into` names `on`   -> "no declared fastener"
  covered : the part's face resting on the host must not cover a host hole that no declared
            fastener uses (P20b): sample that face, keep points with no host material just past
            it but host material all around (a hole, not the host's edge) -> "covers host hole
            at (x, y, z)". Intended ones go in the mount's "covered_ok": [[x, y, z], ...].
Host screw heads under the mounted part are the "head blocked" check: declare the host's screws too.

Purchased bodies a screw clamps (P26c, e.g. a servo tab): name them with the assembly.scad -D values
that render each one positioned, and they count as material in every test below (`into` may name one):
  {"purchased": {"servo": {"MODE": "vit", "VIT": "servo"}}, "fasteners": [...]}
They are rendered to build/purchased/<name>.stl, outside build/positioned, so collision gates never see them.
Contact faces (P20b, AC-H2): every flat patch of the part (>= 1 mm2) within 0.3 mm of host material is checked.
H1 also FAILs "screw bottoms out" when the axis is open then solid before the tip (blind pilot too shallow).
P41 WARNs when a blind hole of an `into` screw ends less than 2 pitches past the tip (Bethune sec 6-13).

Checks per fastener (rings of 12 points, every 0.5 mm):
  head    : cylinder head_d/2 x head_h behind `start` empty in all parts       -> "head blocked"
  access  : cylinder head_d/2 x access_mm behind the head empty                 -> "tool access blocked"
  shank   : 0..thread_from, ring r = d/2 empty in all parts (clearance holes)   -> "shank blocked"
  pilot   : thread_from..length, ring r = 0.35 d empty in all parts (pilot)     -> "no pilot"
  bite    : bite_from..length, ring r = d/2 solid in `into`                   -> "no thread material"
Pairwise: head and shank cylinders of two fasteners closer than r1 + r2 + 0.5 mm -> "fasteners cross".
Exit 0 all OK, 3 any failure, 2 bad input, 4 unknown "insert" / "into_material" value.
shortcut: rings sample 12 points; a feature narrower than ~30 deg of arc can slip between them.
"""
import argparse, glob, itertools, json, math, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

try:
    import numpy as np
    import trimesh
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mesh_python
    mesh_python.reexec()
    print("check_fasteners.py needs numpy + trimesh (scad-modeler venv)", file=sys.stderr)
    sys.exit(2)

STEP, N, CROSS_MARGIN = 0.5, 12, 0.5
# ISO 261 coarse pitch by nominal d (mm); a fine thread sets "pitch" on the fastener
COARSE_PITCH = {1.6: 0.35, 2: 0.4, 2.5: 0.45, 3: 0.5, 3.5: 0.6, 4: 0.7, 5: 0.8, 6: 1.0, 8: 1.25, 10: 1.5, 12: 1.75,
                14: 2.0, 16: 2.0, 18: 2.5, 20: 2.5, 22: 2.5, 24: 3.0, 27: 3.0, 30: 3.5, 33: 3.5, 36: 4.0}
DATA_EXT = (".stl", ".dxf", ".svg", ".off", ".3mf", ".obj", ".amf", ".dat", ".png")


def pitch_of(f):
    d = float(f["d"])
    return float(f.get("pitch") or COARSE_PITCH.get(d) or COARSE_PITCH[min(COARSE_PITCH, key=lambda k: abs(k - d))])


def bite_radius(f):
    """Radius from which thread material must be solid: the tap drill d - P (ISO) plus 0.04 d for printed
    pilots running over (P27b: a fixed 0.44 d failed M10x1 into its own 9.0 mm tap drill)."""
    d = float(f["d"])
    return min((d - pitch_of(f)) / 2 + 0.04 * d, d / 2 - 0.01)


def leaky(m):
    """True for a mesh with a boundary: an edge used by an ODD number of faces. trimesh's is_watertight also
    rejects 4-face edges, which OpenSCAD writes for touching cubes or a hole tangent to a wall (P27b)."""
    _, counts = np.unique(m.edges_sorted, axis=0, return_counts=True)
    return bool((counts % 2).any())


def ring(c, ax, r):
    u = np.cross(ax, [0, 0, 1] if abs(ax[2]) < .9 else [1, 0, 0]); u /= np.linalg.norm(u); v = np.cross(ax, u)
    if r == 0:
        return np.array([c])
    t = np.linspace(0, 2 * np.pi, N, endpoint=False)
    return c + r * (np.outer(np.cos(t), u) + np.outer(np.sin(t), v))


def samples(t0, t1):
    if t1 <= t0:
        return []
    n = max(2, int(np.ceil((t1 - t0) / STEP)) + 1)
    return np.linspace(t0, t1, n)


def seg_dist(p1, q1, p2, q2):
    """Closest distance between segments p1q1 and p2q2 (Ericson, Real-Time Collision Detection 5.1.9)."""
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, f = d1 @ d1, d2 @ d2, d2 @ r
    # P27 / AC-7: a zero-length segment (head_h 0) made 0/0 = NaN, and NaN < margin is False: no crossing
    if a <= 1e-12 and e <= 1e-12:
        return float(np.linalg.norm(r))
    if a <= 1e-12:
        return float(np.linalg.norm(p1 - (p2 + np.clip(f / e, 0, 1) * d2)))
    if e <= 1e-12:
        return float(np.linalg.norm(p2 - (p1 + np.clip(-(d1 @ r) / a, 0, 1) * d1)))
    c, b = d1 @ r, d1 @ d2
    den = a * e - b * b
    s = np.clip((b * f - c * e) / den, 0, 1) if den > 1e-12 else 0.0
    t = (b * s + f) / e
    if t < 0:
        t, s = 0.0, np.clip(-c / a, 0, 1)
    elif t > 1:
        t, s = 1.0, np.clip((b - c) / a, 0, 1)
    return float(np.linalg.norm((p1 + s * d1) - (p2 + t * d2)))


def check_one(f, meshes):
    errs = []
    s, ax = np.array(f["start"], float), np.array(f["axis"], float)
    ax /= np.linalg.norm(ax)
    d, L = float(f["d"]), float(f["length"])
    hd, hh = float(f.get("head_d", 1.8 * d)), float(f.get("head_h", 0.7 * d))
    tf, acc, into = float(f.get("thread_from", 0)), float(f.get("access_mm", 0)), f.get("into")
    bf = float(f.get("bite_from", tf))

    def empty(t, r, what, hint):
        pts = ring(s + t * ax, ax, r)
        hit = [n for n, m in meshes.items() if m.contains(pts).any()]
        if hit:
            errs.append(f"{what} at {t:+.1f} mm (r {r:.2f}) by {', '.join(sorted(hit))} -- Hint: {hint}")

    for t in samples(-hh, -0.05):
        empty(t, hd / 2, "head blocked", "move or cut away the part over the head (counterbore), or lower head_d/head_h")
    for t in samples(-hh - acc, -hh - 0.05):
        empty(t, hd / 2, "tool access blocked", "clear the space over the head for the tool, or lower access_mm")
    for t in samples(0.05, tf - 0.05):
        empty(t, d / 2, "shank blocked", "enlarge the clearance hole for the shank in that part")
    # P40 (Bethune sec 8-43/8-46): a clearance hole must take the fastener plus its position error T.
    # Floating (through-bolt, clearance in every part): H - T = F; fixed (thread in one part): H - 2T = F.
    T = float(f.get("position_tol") or 0)
    if T:
        fixed = bool(into or f.get("insert"))
        # clearance zone: up to thread_from (fixed: where the thread starts, main() demands it; floating: the stack
        # thickness, so a nut or washer modelled as a part is not read as a too-small hole), else the whole shank
        end = tf if fixed else (tf or L)
        for t in samples(0.05, end - 0.05):
            empty(t, d / 2 + (T if fixed else T / 2),
                  f"clearance hole under F + {'2T' if fixed else 'T'} = {d + (2 * T if fixed else T):.3f} mm "
                  f"(position_tol {T:g}, {'H - 2T = F' if fixed else 'H - T = F'}, Bethune sec 8-4{'6' if fixed else '3'})",
                  "enlarge the clearance hole in the part named to the stated diameter, or lower position_tol")
    # AC-H1: a blind pilot shallower than the screw: the axis is open, then solid before the head seats
    bottom = None
    for i, t in enumerate(samples(tf + 0.05, L)):
        if any(m.contains(np.array([s + t * ax])).any() for m in meshes.values()):
            bottom = t if i else None
            break
    if bottom is not None and bottom < L - 0.3:
        errs.append(f"screw bottoms out: tip meets material at +{bottom:.1f} mm, {L - bottom:.1f} mm short of seating the head -- Hint: drill the pilot deeper, or shorten the screw (length)")
    else:
        for t in samples(tf + 0.05, L):
            empty(t, 0.35 * d, "no pilot", "add a hole/relief along the screw path in that part")
    # P41 (Bethune sec 6-13): a blind tapped hole runs >= 2 pitches past the screw tip (tap lead, chips).
    p2, deep = 2 * pitch_of(f), None
    tgt_in = [m for n, m in meshes.items() if into and n.lower() == str(into).lower()]
    if tgt_in and (bottom is None or bottom >= L - 0.3):   # only the hole bottom in `into`, not a part behind it
        deep = next((t for t in samples(max(L - 0.3, tf + 0.05), L + p2)
                     if any(m.contains(np.array([s + t * ax])).any() for m in tgt_in)), None)
    # P26 / AC-7 (Fable audit e8): a screw at [200, 200, 200] in empty space was "OK" -- every test above
    # asks that something is ABSENT. A screw must also seat its head on material and pass through some.
    seat_r = (d / 2 + hd / 2) / 2 + 0.15
    # an interface screw clamping a part from another module waives only this seat test, with a reason
    if not str(f.get("seat_external") or "").strip() and \
            not any(m.contains(ring(s + 0.3 * ax, ax, seat_r)).any() for m in meshes.values()):
        errs.append(f"head seats on nothing at +0.3 mm (r {seat_r:.2f}) -- no part under the head -- Hint: move the fastener's start onto the seating face, or declare seat_external with a reason for an interface screw")
    if not any(m.contains(ring(s + t * ax, ax, d / 2 + 0.6)).any()
               for t in samples(0.3, L) for m in meshes.values()):
        errs.append(f"shank passes through no part (r {d / 2 + 0.6:.2f}) -- the screw is in empty space -- Hint: correct start/axis in fasteners.json so the screw passes through the parts")
    if into:
        tgt = [m for n, m in meshes.items() if n.lower() == into.lower()]  # P26 / AC-3b: exact names
        if not tgt:
            errs.append(f"'into' part {into!r} matches no positioned STL -- Hint: set \"into\" to the name of a positioned STL (file name without .stl)")
        else:
            # P27 / AC-10: material from r = 0.44 d, i.e. a pilot of at most 0.88 d (ISO tap drills 0.82-0.84 d;
            # printed pilots run a little over). At r = d/2 an M4 bit "into" a 3.9 mm hole.
            rb = bite_radius(f)
            for t in samples(bf + 0.3, L - 0.3):
                if not any(m.contains(ring(s + t * ax, ax, rb)).all() for m in tgt):
                    errs.append(f"no thread material at {t:+.1f} mm (r {rb:.2f}, pilot over {2 * rb:.2f}) in {into} -- Hint: shrink the pilot hole or add wall material where the thread must bite")
    # AC-H1 thread engagement. Heat-set insert: the screw must reach through the whole insert (inserts.json L).
    # Otherwise = threaded length L - bite_from, once the bite test found material over all of it.
    warns = []
    if f.get("insert"):
        spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "inserts.json"))
                         ).get(f["insert"])
        if spec:
            eng = max(0.0, min(L - float(f.get("insert_from", tf)), spec["L"]))
            if eng < spec["L"] - 0.05:
                errs.append(f"thread engagement {eng:.1f} mm < insert length {spec['L']} mm ({f['insert']}, inserts.json) -- Hint: lengthen the screw to reach through the whole insert, or pick a shorter insert")
    elif into and not any(e.startswith(("no thread material", "'into'")) for e in errs):
        eng, mat = L - bf, str(f.get("into_material", "plastic")).lower()
        # Tameson thread engagement chart (tameson.com/pages/thread-engagement-chart, read 2026-11-27): aluminium
        # 2.0-2.5 x d (verified, FAIL at 2.0 d); plastic "higher than metals, trials needed", no number, so the
        # 1.5 d plastic floor is ◇ unverified and only WARNs.
        if mat == "aluminium" and eng < 2.0 * d - 0.05:
            errs.append(f"thread engagement {eng:.1f} mm < 2 d = {2 * d:.1f} mm (aluminium, Tameson chart 2.0-2.5 d) -- Hint: lengthen the screw or deepen the tapped hole to at least 2 d")
        elif mat == "plastic" and eng < 1.5 * d - 0.05:
            warns.append(f"WARN thread engagement {eng:.1f} mm < 1.5 d = {1.5 * d:.1f} mm (plastic, ◇ unverified floor)")
    if deep is not None:
        warns.append(f"WARN tapped hole ends {max(0.0, deep - L):.1f} mm past the tip < 2P = {p2:.1f} mm (Bethune sec 6-13)")
    # one message per kind keeps the report readable
    seen, out = set(), []
    for e in errs:
        k = e.split(" at ")[0]
        if k not in seen:
            seen.add(k); out.append(e)
    return out, warns


def cylinders(f):
    s, ax = np.array(f["start"], float), np.array(f["axis"], float)
    ax /= np.linalg.norm(ax)
    d = float(f["d"]); hd, hh = float(f.get("head_d", 1.8 * d)), float(f.get("head_h", 0.7 * d))
    return [(s - hh * ax, s, hd / 2), (s, s + float(f["length"]) * ax, d / 2)]


def crossings(fs):
    bad = []
    for a, b in itertools.combinations(fs, 2):
        gap = min(seg_dist(p1, q1, p2, q2) - r1 - r2
                  for p1, q1, r1 in cylinders(a) for p2, q2, r2 in cylinders(b))
        if gap < CROSS_MARGIN:
            bad.append(f"fasteners cross: {a['name']} / {b['name']} (gap {gap:.2f} mm < {CROSS_MARGIN}) -- Hint: move one fastener or shorten it so the two do not meet")
    return bad


def mount_count(m, fs, meshes):
    """Declared fasteners that pass through part m['part'] and bite into m['on']."""
    part = [mesh for n, mesh in meshes.items() if n.lower() == str(m["part"]).lower()]
    if not part:
        return None
    n = 0
    for f in fs:
        if str(m["on"]).lower() != str(f.get("into") or "").lower():
            continue
        s, ax = np.array(f["start"], float), np.array(f["axis"], float)
        ax /= np.linalg.norm(ax)
        r = float(f["d"]) / 2 + 0.75
        if any(pm.contains(ring(s + t * ax, ax, r)).any() for t in samples(0.05, float(f["length"])) for pm in part):
            n += 1
    return n


def covered_host_holes(m, meshes, n=20000, seed=0):
    """Centres of host holes under the part's contact face that the part covers (P20b)."""
    part = [mesh for k, mesh in meshes.items() if k.lower() == str(m["part"]).lower()]
    host = [mesh for k, mesh in meshes.items() if k.lower() == str(m["on"]).lower()]
    if len(part) != 1 or not host:
        return []
    P = part[0]
    pts, fi = trimesh.sample.sample_surface_even(P, n, seed=seed) if hasattr(trimesh.sample, "sample_surface_even") else trimesh.sample.sample_surface(P, n)
    nrm = P.face_normals[fi]
    inside_host = lambda q: np.any([h.contains(q) for h in host], axis=0)
    touch = inside_host(pts + 0.3 * nrm)
    if not touch.any():
        return []
    # AC-H2: every contact plane = (rounded normal, offset) with >= 3 touching samples and >= 1 mm2 of face
    keys = {}
    for i in np.flatnonzero(touch):
        keys.setdefault((tuple(np.round(nrm[i], 3)), round(float(nrm[i] @ pts[i]), 1)), []).append(i)
    pts0, nrm0, touch0 = pts, nrm, touch
    out = []
    for (nv, off), idx in keys.items():
        if len(idx) < 3:
            continue
        nv = np.array(nv)
        fn = P.face_normals
        on = (np.abs(fn @ nv - 1) < 1e-3) & (np.abs(P.triangles_center @ nv - off) < 0.1)
        if not on.any() or P.area_faces[on].sum() < 1.0:
            continue
        out += plane_holes(P, nv, off, pts0, nrm0, touch0, inside_host, n, seed)
    ok = [np.array(c, float) for c in m.get("covered_ok", [])]
    res = []
    for c in out:   # the same hole seen from two planes is reported once
        if not any(np.linalg.norm(c - o) < 3.0 for o in ok) and not any(np.linalg.norm(c - r) < 1.0 for r in res):
            res.append(c)
    return res


def plane_holes(P, nv, off, pts, nrm, touch, inside_host, n, seed):
    """Host holes under one contact plane of part P that the part covers."""
    # P27 / AC-11: resample only the contact face, ~4 points per mm2 (a fixed 20000 over a 300 mm lid
    # left a 4 mm hole with under 3 samples). shortcut: capped at 400000 points, ~100000 mm2 of face.
    fn = P.face_normals
    face_on = (np.abs(fn @ nv - 1) < 1e-3) & (np.abs(P.triangles_center @ nv - off) < 0.1)
    if face_on.any():
        sub = P.submesh([np.flatnonzero(face_on)], append=True)
        k = int(min(400000, max(n, 4 * sub.area)))
        sp, sfi = trimesh.sample.sample_surface(sub, k, seed=seed) if "seed" in trimesh.sample.sample_surface.__code__.co_varnames \
            else trimesh.sample.sample_surface(sub, k)
        pts = np.vstack([pts, sp]); nrm = np.vstack([nrm, sub.face_normals[sfi]])
        touch = np.concatenate([touch, inside_host(sp + 0.3 * sub.face_normals[sfi])])
    on_plane = (np.abs(nrm @ nv - 1) < 1e-3) & (np.abs(pts @ nv - off) < 0.1)
    cand = np.flatnonzero(on_plane & ~touch)
    if not len(cand):
        return []
    # P27b: cluster the uncovered face points FIRST (link 1.5 mm), then test one centroid per cluster: a
    # per-point loop over ~160k candidates under a 200 mm window took 344 s. A cluster wider than 20 mm is an
    # opening, not a screw hole (its centroid could never be surrounded by host material at r <= 10).
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree
    _, keep = np.unique(np.round(pts[cand] / 0.5).astype(np.int64), axis=0, return_index=True)
    H = pts[cand[np.sort(keep)]]
    if not len(H):
        return []
    ncl, lab = connected_components(cKDTree(H).sparse_distance_matrix(cKDTree(H), 1.5), directed=False)
    cents = []
    for k in range(ncl):
        g = H[lab == k]
        if len(g) >= 3 and np.ptp(g, axis=0).max() <= 20.0:
            cents.append(g.mean(axis=0))
    if not cents:
        return []
    C = np.array(cents)
    q = C + 0.3 * nv
    C, q = C[~inside_host(q + 1.0 * nv)], q[~inside_host(q + 1.0 * nv)]   # void continues into the host
    ring0 = ring(np.zeros(3), nv, 1.0)
    surrounded = np.zeros(len(q), bool)
    for r in (3.0, 6.0, 10.0):
        todo = np.flatnonzero(~surrounded)
        if not len(todo):
            break
        pr = (q[todo, None, :] + r * ring0[None, :, :]).reshape(-1, 3)
        surrounded[todo] = inside_host(pr).reshape(len(todo), -1).mean(axis=1) > 0.9
    return list(C[surrounded])


def render_instances(names, outdir="build/positioned", defs=None):
    """Render instance names missing from (or older than every .scad in) outdir via assembly.scad.
    defs: name -> {-D name: value}; default MODE="part" PART="<name>"."""
    os.makedirs(outdir, exist_ok=True)
    # P27 / AC-16: import()ed data files count too, not only .scad (build/ output excluded)
    newest = max((os.path.getmtime(p) for p in glob.glob("**/*", recursive=True)
                  if p.endswith(".scad") or (p.lower().endswith(DATA_EXT) and not p.startswith("build" + os.sep)
                                             and os.path.basename(p) not in ("fasteners.json",))), default=0)
    def same_defs(n):   # a body rendered with other -D values is stale too (sidecar <name>.D.json)
        try:
            return json.load(open(f"{outdir}/{n}.D.json")) == defs[n]
        except (OSError, ValueError):
            return not explicit
    explicit = defs is not None and outdir != "build/positioned"
    defs = defs or {n: {"MODE": "part", "PART": n} for n in names}
    todo = [n for n in names if not os.path.isfile(f"{outdir}/{n}.stl") or os.path.getmtime(f"{outdir}/{n}.stl") < newest
            or not same_defs(n)]
    exe = os.environ.get("OPENSCAD", "openscad")

    def one(n):
        dv = [x for k, v in defs[n].items() for x in ("-D", f"{k}={json.dumps(v)}")]
        r = subprocess.run([exe, "--backend=Manifold", *(["--hardwarnings"] if explicit else []), "-o",
                            f"{outdir}/{n}.stl", "--export-format=binstl", *dv, "assembly.scad"], capture_output=True)
        if not r.returncode and explicit:
            json.dump(defs[n], open(f"{outdir}/{n}.D.json", "w"))
        if r.returncode:
            for x in (f"{outdir}/{n}.stl", f"{outdir}/{n}.D.json"):
                try:
                    os.remove(x)
                except OSError:
                    pass
        return n, r.returncode
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        failed = [n for n, rc in ex.map(one, todo) if rc]
    return [f"{outdir}/{n}.stl" for n in names], failed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--fasteners", default="fasteners.json")
    ap.add_argument("stls", nargs="*", help="positioned STLs (default build/positioned/*.stl)")
    a = ap.parse_args()
    try:
        data = json.load(open(a.fasteners))
        inst = data.get("instances", []) if isinstance(data, dict) else []
        mounts = data.get("mounts", []) if isinstance(data, dict) else []
        purch = data.get("purchased", {}) if isinstance(data, dict) else {}
        for n, dv in purch.items():
            if not re.fullmatch(r"[A-Za-z0-9_]+", n) or not isinstance(dv, dict) or not dv or any(
                    not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k) or isinstance(v, bool)
                    or not isinstance(v, (str, int, float)) for k, v in dv.items()):
                raise ValueError(f"purchased {n!r}: needs {{-D name: string or number}}")
        for m in mounts:
            m["part"], m["on"]
        allf = data["fasteners"] if isinstance(data, dict) else data
        nostart = [f.get("name", f"#{i + 1}") for i, f in enumerate(allf)
                   if isinstance(f, dict) and "start" not in f and any(k in f for k in ("name", "axis", "d", "length"))]
        if nostart:   # P27 / AC-8: a typo ("strat") silently dropped the screw from every check
            raise ValueError(f"fastener(s) without \"start\": {', '.join(map(str, nostart))}")
        fs = [f for f in allf if "start" in f]
        for f in fs:
            for k in ("name", "axis", "d", "length"):
                f[k]
            T = float(f.get("position_tol") or 0)
            if not math.isfinite(T) or T < 0:
                raise ValueError(f"fastener {f['name']!r}: position_tol must be a number >= 0 mm")
            if T and (f.get("into") or f.get("insert")) and float(f.get("thread_from", 0)) <= 0:
                raise ValueError(f"fastener {f['name']!r}: position_tol on a screw into a part needs thread_from "
                                 "(where the clearance hole ends and the thread starts)")
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"bad {a.fasteners}: {e}", file=sys.stderr); return 2
    ins = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "inserts.json")))
    ok_ins = sorted(k for k in ins if not k.startswith("_"))
    for f in fs:   # wave2 review: an unknown key used to be skipped silently, i.e. the check never ran
        if f.get("insert") and f["insert"] not in ok_ins:
            print(f"bad {a.fasteners}: fastener {f['name']!r}: unknown insert {f['insert']!r} (accepted: {', '.join(ok_ins)})",
                  file=sys.stderr); return 4
        mat = str(f.get("into_material", "plastic")).lower()
        mat = "aluminium" if mat == "aluminum" else mat
        if mat not in ("plastic", "aluminium"):
            print(f"bad {a.fasteners}: fastener {f['name']!r}: unknown into_material {f['into_material']!r} "
                  f"(accepted: plastic, aluminium, aluminum)", file=sys.stderr); return 4
        f["into_material"] = mat
    stls = a.stls or sorted(glob.glob("build/positioned/*.stl"))
    if inst and not a.stls:
        if not os.path.isfile("assembly.scad"):
            print("instances declared but no assembly.scad here", file=sys.stderr); return 2
        ist, failed = render_instances(inst)
        if failed:
            print(f"instances failed to render: {', '.join(failed)}", file=sys.stderr); return 2
        # P27 / AC-6: the instance renders join build/positioned, they do not replace it (a cover there was ignored)
        stls = sorted(set(stls) | set(ist))
    if not stls or not fs:
        print("no positioned STLs or no fasteners -- nothing checked", file=sys.stderr); return 2
    if purch:
        if not os.path.isfile("assembly.scad"):
            print("purchased bodies declared but no assembly.scad here", file=sys.stderr); return 2
        pst, failed = render_instances(list(purch), "build/purchased", purch)
        if failed:
            print(f"purchased bodies failed to render: {', '.join(failed)}", file=sys.stderr); return 2
        stls = list(stls) + pst
    meshes = {os.path.basename(p)[:-4]: trimesh.load(p, force="mesh") for p in stls}
    open_ = sorted(n for n, m in meshes.items() if leaky(m))
    if open_:   # P27 / AC-9: containment on an open mesh is meaningless (a cover missing one face blocked nothing)
        print(f"not watertight, screw paths cannot be tested: {', '.join(open_)} -- re-export closed meshes",
              file=sys.stderr); return 2
    nbad = 0
    for f in fs:
        errs, warns = check_one(f, meshes)
        nbad += bool(errs)
        print(("OK   " if not errs else "FAIL ") + f["name"] + "".join(f"\n       {e}" for e in errs + warns))
    cross = crossings(fs)
    for c in cross:
        print("FAIL " + c)
    mbad = 0
    for m in mounts:
        k, need = mount_count(m, fs, meshes), int(m.get("min", 1))
        if k is None:
            print(f"FAIL mount {m['part']} -> {m['on']}: part matches no positioned STL -- Hint: name a positioned STL (file name without .stl) in the mount's \"part\""); mbad += 1
        elif k < need:
            print(f"FAIL mount {m['part']} -> {m['on']}: no declared fastener goes through it into {m['on']} -- Hint: declare the screw in fasteners.json with this part in its path and \"into\": \"{m['on']}\""
                  if k == 0 else f"FAIL mount {m['part']} -> {m['on']}: {k} fastener(s), need {need} -- Hint: declare more fasteners "
                  f"through it into {m['on']}, or lower the mount's \"min\""); mbad += 1
        else:
            print(f"OK   mount {m['part']} -> {m['on']}: {k} fastener(s)")
        for c in (covered_host_holes(m, meshes) if k is not None else []):
            print(f"FAIL mount {m['part']} -> {m['on']}: covers host hole at ({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f})"
                  " -- no declared fastener uses it; Hint: add a hole/relief, declare its screw, or list it in covered_ok"); mbad += 1
    print(f"fasteners: {len(fs) - nbad}/{len(fs)} OK, {len(cross)} crossing pair(s)"
          + (f", mounts {len(mounts) - mbad}/{len(mounts)} OK" if mounts else ""))
    return 3 if nbad or cross or mbad else 0


if __name__ == "__main__":
    sys.exit(main())
