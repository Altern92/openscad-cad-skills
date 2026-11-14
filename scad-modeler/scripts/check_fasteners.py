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
   "access_mm": 0}                  # optional: free straight tool path behind the head
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
shortcut: the contact face is the largest flat patch of the part touching the host; a part touching
its host on several planes is checked on that one plane only.

Checks per fastener (rings of 12 points, every 0.5 mm):
  head    : cylinder head_d/2 x head_h behind `start` empty in all parts       -> "head blocked"
  access  : cylinder head_d/2 x access_mm behind the head empty                 -> "tool access blocked"
  shank   : 0..thread_from, ring r = d/2 empty in all parts (clearance holes)   -> "shank blocked"
  pilot   : thread_from..length, ring r = 0.35 d empty in all parts (pilot)     -> "no pilot"
  bite    : bite_from..length, ring r = d/2 solid in `into`                   -> "no thread material"
Pairwise: head and shank cylinders of two fasteners closer than r1 + r2 + 0.5 mm -> "fasteners cross".
Exit 0 all OK, 3 any failure, 2 bad input.
shortcut: rings sample 12 points; a feature narrower than ~30 deg of arc can slip between them.
"""
import argparse, glob, itertools, json, os, subprocess, sys
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

    def empty(t, r, what):
        pts = ring(s + t * ax, ax, r)
        hit = [n for n, m in meshes.items() if m.contains(pts).any()]
        if hit:
            errs.append(f"{what} at {t:+.1f} mm (r {r:.2f}) by {', '.join(sorted(hit))}")

    for t in samples(-hh, -0.05):
        empty(t, hd / 2, "head blocked")
    for t in samples(-hh - acc, -hh - 0.05):
        empty(t, hd / 2, "tool access blocked")
    for t in samples(0.05, tf - 0.05):
        empty(t, d / 2, "shank blocked")
    for t in samples(tf + 0.05, L):
        empty(t, 0.35 * d, "no pilot")
    if into:
        tgt = [m for n, m in meshes.items() if into.lower() in n.lower()]
        if not tgt:
            errs.append(f"'into' part {into!r} matches no positioned STL")
        else:
            for t in samples(bf + 0.3, L - 0.3):
                if not any(m.contains(ring(s + t * ax, ax, d / 2)).all() for m in tgt):
                    errs.append(f"no thread material at {t:+.1f} mm (r {d / 2:.2f}) in {into}")
    # one message per kind keeps the report readable
    seen, out = set(), []
    for e in errs:
        k = e.split(" at ")[0]
        if k not in seen:
            seen.add(k); out.append(e)
    return out


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
            bad.append(f"fasteners cross: {a['name']} / {b['name']} (gap {gap:.2f} mm < {CROSS_MARGIN})")
    return bad


def mount_count(m, fs, meshes):
    """Declared fasteners that pass through part m['part'] and bite into m['on']."""
    part = [mesh for n, mesh in meshes.items() if str(m["part"]).lower() in n.lower()]
    if not part:
        return None
    n = 0
    for f in fs:
        if str(m["on"]).lower() not in str(f.get("into") or "").lower():
            continue
        s, ax = np.array(f["start"], float), np.array(f["axis"], float)
        ax /= np.linalg.norm(ax)
        r = float(f["d"]) / 2 + 0.75
        if any(pm.contains(ring(s + t * ax, ax, r)).any() for t in samples(0.05, float(f["length"])) for pm in part):
            n += 1
    return n


def covered_host_holes(m, meshes, n=20000, seed=0):
    """Centres of host holes under the part's contact face that the part covers (P20b)."""
    part = [mesh for k, mesh in meshes.items() if str(m["part"]).lower() in k.lower()]
    host = [mesh for k, mesh in meshes.items() if str(m["on"]).lower() in k.lower()]
    if len(part) != 1 or not host:
        return []
    P = part[0]
    pts, fi = trimesh.sample.sample_surface_even(P, n, seed=seed) if hasattr(trimesh.sample, "sample_surface_even") else trimesh.sample.sample_surface(P, n)
    nrm = P.face_normals[fi]
    inside_host = lambda q: np.any([h.contains(q) for h in host], axis=0)
    touch = inside_host(pts + 0.3 * nrm)
    if not touch.any():
        return []
    # contact plane = most common (rounded normal, offset) among touching samples
    key = lambda i: (tuple(np.round(nrm[i], 3)), round(float(nrm[i] @ pts[i]), 1))
    keys = [key(i) for i in np.flatnonzero(touch)]
    (nv, off), _ = max(((k, keys.count(k)) for k in set(keys)), key=lambda kv: kv[1])
    nv = np.array(nv)
    on_plane = (np.abs(nrm @ nv - 1) < 1e-3) & (np.abs(pts @ nv - off) < 0.1)
    cand = np.flatnonzero(on_plane & ~touch)
    if not len(cand):
        return []
    q = pts[cand] + 0.3 * nv
    deep = ~inside_host(q + 1.0 * nv)            # void continues into the host: a hole, not a dent
    cand, q = cand[deep], q[deep]
    holes = []
    for i, c in zip(cand, q):                    # surrounded by host material at some radius
        if any(inside_host(ring(c, nv, r)).mean() > 0.9 for r in (3.0, 6.0, 10.0)):
            holes.append(pts[i])
    if not holes:
        return []
    from scipy.spatial import cKDTree
    H = np.array(holes); tree = cKDTree(H); seen = np.zeros(len(H), bool); out = []
    for i in range(len(H)):
        if seen[i]:
            continue
        grp, todo = set(), [i]
        while todo:
            j = todo.pop()
            if j in grp:
                continue
            grp.add(j); todo += tree.query_ball_point(H[j], 1.5)
        seen[list(grp)] = True
        if len(grp) >= 3:
            out.append(H[list(grp)].mean(axis=0))
    ok = [np.array(c, float) for c in m.get("covered_ok", [])]
    return [c for c in out if not any(np.linalg.norm(c - o) < 3.0 for o in ok)]


def render_instances(names, outdir="build/positioned"):
    """Render instance names missing from (or older than every .scad in) outdir via assembly.scad."""
    os.makedirs(outdir, exist_ok=True)
    newest = max((os.path.getmtime(p) for p in glob.glob("**/*.scad", recursive=True)), default=0)
    todo = [n for n in names if not os.path.isfile(f"{outdir}/{n}.stl") or os.path.getmtime(f"{outdir}/{n}.stl") < newest]
    exe = os.environ.get("OPENSCAD", "openscad")

    def one(n):
        r = subprocess.run([exe, "--backend=Manifold", "-o", f"{outdir}/{n}.stl", "--export-format=binstl",
                            "-D", 'MODE="part"', "-D", f'PART="{n}"', "assembly.scad"], capture_output=True)
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
        for m in mounts:
            m["part"], m["on"]
        fs = [f for f in (data["fasteners"] if isinstance(data, dict) else data) if "start" in f]
        for f in fs:
            for k in ("name", "axis", "d", "length"):
                f[k]
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"bad {a.fasteners}: {e}", file=sys.stderr); return 2
    stls = a.stls or sorted(glob.glob("build/positioned/*.stl"))
    if inst and not a.stls:
        if not os.path.isfile("assembly.scad"):
            print("instances declared but no assembly.scad here", file=sys.stderr); return 2
        stls, failed = render_instances(inst)
        if failed:
            print(f"instances failed to render: {', '.join(failed)}", file=sys.stderr); return 2
    if not stls or not fs:
        print("no positioned STLs or no fasteners -- nothing checked", file=sys.stderr); return 2
    meshes = {os.path.basename(p)[:-4]: trimesh.load(p, force="mesh") for p in stls}
    nbad = 0
    for f in fs:
        errs = check_one(f, meshes)
        nbad += bool(errs)
        print(("OK   " if not errs else "FAIL ") + f["name"] + "".join(f"\n       {e}" for e in errs))
    cross = crossings(fs)
    for c in cross:
        print("FAIL " + c)
    mbad = 0
    for m in mounts:
        k, need = mount_count(m, fs, meshes), int(m.get("min", 1))
        if k is None:
            print(f"FAIL mount {m['part']} -> {m['on']}: part matches no positioned STL"); mbad += 1
        elif k < need:
            print(f"FAIL mount {m['part']} -> {m['on']}: no declared fastener goes through it into {m['on']}"
                  if k == 0 else f"FAIL mount {m['part']} -> {m['on']}: {k} fastener(s), need {need}"); mbad += 1
        else:
            print(f"OK   mount {m['part']} -> {m['on']}: {k} fastener(s)")
        for c in (covered_host_holes(m, meshes) if k is not None else []):
            print(f"FAIL mount {m['part']} -> {m['on']}: covers host hole at ({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f})"
                  " -- no declared fastener uses it; add a hole/relief, declare its screw, or list it in covered_ok"); mbad += 1
    print(f"fasteners: {len(fs) - nbad}/{len(fs)} OK, {len(cross)} crossing pair(s)"
          + (f", mounts {len(mounts) - mbad}/{len(mounts)} OK" if mounts else ""))
    return 3 if nbad or cross or mbad else 0


if __name__ == "__main__":
    sys.exit(main())
