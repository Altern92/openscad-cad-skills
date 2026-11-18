#!/usr/bin/env python3
"""Assembly behaviour: does it HOLD, does it MOVE, does it STAND (P23, 2026-11-18).

INC-2026-11-18-01: a double-wishbone front axle passed every gate while its arms
floated in the air. joints.json / attachments.json declared the ball joints, but the
rod ends that make them (purchased parts) were never modelled, so nothing in the
geometry connected the arms to the upright. Declarations say what SHOULD touch; this
check measures what DOES, on the positioned parts AND vitamins, across the motion.

behavior.json (project root):
  "scad":   assembly file rendered per body (default assembly.scad)
  "poses":  {"PARAM": [v1, v2, ...], ...} -- full grid, each point passed as -D
  "bodies": {"name": {"render": [{"MODE": "part", "PART": "x"}, ...],   # -D sets, unioned
                      "scad": "../other/assembly.scad",   # optional: a sub-assembly's own file
                      "static": true,          # rendered once, without pose params
                      "mass_g": 120 | "density": 1.27}}                 # g, or g/cm3 (default 1.0)
  "joints": [{"a": .., "b": .., "max_gap": 0.3, "why": ".."}]   # max_gap <= 1.0 mm, always
  "clearance": {"default": 0.0, "pairs": [{"a": .., "b": .., "min": 1.5}]}
  "ground": {"z": 0, "bodies": [..], "tol": 0.5,               # optional -> STANDS
             "at": {"BUMP": 0}}     # only at these poses (a pose that lifts a wheel off a fixed chassis)

HOLDS  every body is in a joint; every joint's gap <= max_gap at every pose; max_gap <= 1 mm
       (a bigger gap is a missing part, not a joint); the joint graph is one group that
       reaches a ground body.
MOVES  at every pose: non-joint bodies do not interpenetrate (> 0.01 mm3) and keep the
       declared/default clearance. Joint pairs may overlap (a ball in its cup).
STANDS at every pose: each ground body's lowest point is within tol of ground z, and the
       mass centre lies inside the convex hull of the ground-contact points.

Not a physics simulation: no forces, friction or strength.

Usage: python3 check_behavior.py --project-dir . [--behavior behavior.json] [-D NAME=VALUE ...]
Exit: 0 pass, 3 fail (incl. a body that does not render), 4 usage (bad JSON, unknown body).
"""
import argparse
import hashlib
import itertools
import json
import os
import re
import subprocess
import sys
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4
warnings.filterwarnings("ignore", category=RuntimeWarning, module="trimesh")   # open shells: centroid used instead
MAX_GAP_CAP = 1.0      # mm; not configurable on purpose (AC-3)
VOL_EPS = 0.01         # mm3 of intersection counted as interference

try:
    import numpy as np
    import trimesh
    from trimesh.collision import CollisionManager
    from scipy.spatial import ConvexHull
except ImportError as e:
    __import__("mesh_python").reexec()
    print(f"ERROR: missing dependency ({e}). Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def usage(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        usage(f"cannot read {path}: {e}")
    bodies = d.get("bodies") or {}
    if not isinstance(bodies, dict) or not bodies:
        usage(f"{path}: \"bodies\" must be a non-empty object")
    for n, b in bodies.items():
        if not isinstance(b.get("render"), list) or not b["render"]:
            usage(f"{path}: body {n} needs a non-empty \"render\" list")
    names = set(bodies)
    for j in d.get("joints", []):
        for k in ("a", "b"):
            if j.get(k) not in names:
                usage(f"{path}: joint names unknown body {j.get(k)!r}")
        if "max_gap" not in j:
            usage(f"{path}: joint {j['a']}-{j['b']} has no max_gap")
    for p in (d.get("clearance") or {}).get("pairs", []):
        for k in ("a", "b"):
            if p.get(k) not in names:
                usage(f"{path}: clearance pair names unknown body {p.get(k)!r}")
    g = d.get("ground")
    if g is not None:
        for n in g.get("bodies", []):
            if n not in names:
                usage(f"{path}: ground names unknown body {n!r}")
        if not g.get("bodies"):
            usage(f"{path}: ground needs \"bodies\"")
    return d


def fmt(v):
    return f'"{v}"' if isinstance(v, str) else json.dumps(v)


INC_RE = re.compile(r"^\s*(?:use|include)\s*<([^>]+)>", re.M)


def deps_hash(scad):
    """sha256 over the file and every use/include it reaches by a relative path (other projects
    included); library files found only on the OpenSCAD library path are not followed."""
    h, todo, seen = hashlib.sha256(), [os.path.abspath(scad)], set()
    while todo:
        f = todo.pop()
        if f in seen or not os.path.isfile(f):
            continue
        seen.add(f)
        with open(f, "rb") as fh:
            data = fh.read()
        h.update(f.encode()); h.update(data)
        for inc in INC_RE.findall(data.decode("utf-8", "replace")):
            todo.append(os.path.normpath(os.path.join(os.path.dirname(f), inc)))
    return h.hexdigest()


class Renderer:
    def __init__(self, project, scad, extra, cache):
        self.project, self.scad, self.extra, self.cache = project, scad, extra, cache
        self.salts, self.lock = {}, threading.Lock()
        self.openscad = os.environ.get("OPENSCAD", "openscad")
        os.makedirs(cache, exist_ok=True)

    def salt(self, scad):
        with self.lock:
            if scad not in self.salts:
                self.salts[scad] = deps_hash(scad)
            return self.salts[scad]

    def path(self, job):
        scad, defines = job
        scad = os.path.normpath(os.path.join(self.project, scad or self.scad))
        cwd = os.path.dirname(scad)
        if not os.path.isfile(scad):
            raise RuntimeError(f"no such file: {scad}")
        args = []
        for k, v in defines.items():
            args += ["-D", f"{k}={fmt(v)}"]
        for k, v in self.extra:   # command-line defines: verbatim, like openscad -D
            args += ["-D", f"{k}={v}"]
        key = hashlib.sha256((self.salt(scad) + scad + " ".join(args)).encode()).hexdigest()[:20]
        out = os.path.join(self.cache, key + ".stl")
        if not os.path.exists(out):
            tmp = f"{out}.{os.getpid()}.{threading.get_ident()}.stl"
            cmd = [self.openscad, "--backend=Manifold", "-o", tmp] + args + [scad]
            r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
            if r.returncode or "ERROR" in r.stderr or not os.path.exists(tmp):
                raise RuntimeError(" ".join(cmd) + "\n" + r.stderr[-600:])
            os.replace(tmp, out)
        return out, args

    def prerender(self, jobs):
        """Render every (defines) job in parallel; openscad runs in subprocesses."""
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
            list(ex.map(self.path, jobs))   # re-raises the first RuntimeError

    def one(self, job):
        out, args = self.path(job)
        m = trimesh.load(out, force="mesh")
        if m.is_empty:
            raise RuntimeError(f"empty render: {' '.join(args)}")
        return m


_LOOSE = {}
PIECE_MIN_MM = 0.01   # a split "piece" thinner than this is a zero-thickness face, not material


def loose_pieces(x, meshes, joints):
    """[(index, piece, partner names)] for pieces of body x connected to no joint partner.

    Pieces = material shells (cavities and zero-thickness faces dropped). A piece is held when it
    is within the joint's max_gap of a partner, or touches (<= the body's largest max_gap) a held
    piece of the same body. Cached on the mesh objects, so static bodies are worked out once."""
    partners = [(j["b"] if j["a"] == x else j["a"], float(j["max_gap"])) for j in joints if x in (j["a"], j["b"])]
    if not partners:
        return []
    key = (x, id(meshes[x])) + tuple(id(meshes[y]) for y, _ in partners)
    if key in _LOOSE:
        return _LOOSE[key]
    pieces = [q for q in meshes[x].split(only_watertight=False)
              if min(q.extents) > PIECE_MIN_MM and not (q.is_watertight and q.volume < 0)]   # closed + negative = a cavity
    out = []
    if len(pieces) > 1:
        touch = max(g for _, g in partners)
        mgr = {y: CollisionManager() for y, _ in partners}
        for y, _ in partners:
            mgr[y].add_object(y, meshes[y])

        def near(c, m, g):
            return c.in_collision_single(m) or c.min_distance_single(m) <= g
        held = [any(near(mgr[y], q, g) for y, g in partners) for q in pieces]
        own = CollisionManager()
        for i, q in enumerate(pieces):
            own.add_object(str(i), q)
        _, hit = own.in_collision_internal(return_names=True)
        adj = {i: set() for i in range(len(pieces))}
        for u, v in hit:
            adj[int(u)].add(int(v)); adj[int(v)].add(int(u))
        if touch > 0:
            for i, j in itertools.combinations(range(len(pieces)), 2):
                if j not in adj[i] and np.all(pieces[i].bounds[0] - touch <= pieces[j].bounds[1]) \
                        and np.all(pieces[j].bounds[0] - touch <= pieces[i].bounds[1]):
                    c = CollisionManager(); c.add_object("i", pieces[i])
                    if c.min_distance_single(pieces[j]) <= touch:
                        adj[i].add(j); adj[j].add(i)
        stack = [i for i, h in enumerate(held) if h]
        while stack:
            i = stack.pop()
            for j in adj[i]:
                if not held[j]:
                    held[j] = True; stack.append(j)
        out = [(i, q, sorted(y for y, _ in partners)) for i, q in enumerate(pieces) if not held[i]]
    _LOOSE[key] = out
    return out


def body_mass(spec, mesh):
    if "mass_g" in spec:
        return float(spec["mass_g"]), False
    return abs(float(mesh.volume)) / 1000.0 * float(spec.get("density", 1.0)), "density" not in spec


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--behavior", default="behavior.json")
    ap.add_argument("-D", action="append", default=[], metavar="NAME=VALUE",
                    help="extra OpenSCAD define passed to every render (value used verbatim)")
    a = ap.parse_args()
    proj = os.path.abspath(a.project_dir)
    bpath = a.behavior if os.path.isabs(a.behavior) else os.path.join(proj, a.behavior)
    d = load(bpath)
    extra = []
    for x in a.D:
        k, sep, v = x.partition("=")
        if not sep:
            usage(f"-D {x}: want NAME=VALUE")
        extra.append((k, v))

    bodies = d["bodies"]
    joints = d.get("joints", [])
    clr = d.get("clearance") or {}
    default_min = float(clr.get("default", 0.0))
    pair_min = {frozenset((p["a"], p["b"])): float(p["min"]) for p in clr.get("pairs", [])}
    ground = d.get("ground")
    poses_decl = d.get("poses") or {}
    keys = list(poses_decl)
    grid = [dict(zip(keys, vals)) for vals in itertools.product(*[poses_decl[k] for k in keys])] or [{}]
    rnd = Renderer(proj, d.get("scad", "assembly.scad"), extra, os.path.join(proj, "build", "behavior"))

    fails = {"holds": [], "moves": [], "stands": []}
    per_pose = {}   # (gate, key) -> [worst severity, message, poses failed]

    def add(gate, key, sev, msg):
        """A per-pose failure: report the worst pose once, with how many poses failed."""
        e = per_pose.setdefault((gate, key), [None, "", 0])
        e[2] += 1
        if e[0] is None or sev > e[0]:
            e[0], e[1] = sev, msg
    joint_pairs = {frozenset((j["a"], j["b"])) for j in joints}

    # -- HOLDS, static part: membership, cap, graph
    joined = {n for j in joints for n in (j["a"], j["b"])}
    for n in bodies:
        if n not in joined and len(bodies) > 1:
            fails["holds"].append(f"{n} is not held by anything (in no joint) -- declare what holds it, "
                                  "and model that part if it is purchased")
    for j in joints:
        if float(j["max_gap"]) > MAX_GAP_CAP:
            fails["holds"].append(f"{j['a']} <-> {j['b']}: max_gap {j['max_gap']} mm > {MAX_GAP_CAP}: a gap is "
                                  "not a joint -- model the purchased part that bridges it (rod end, pin, spacer)")
    adj = {n: set() for n in bodies}
    for j in joints:
        adj[j["a"]].add(j["b"]); adj[j["b"]].add(j["a"])
    seen, groups = set(), []
    for n in bodies:
        if n in seen:
            continue
        stack, g = [n], set()
        while stack:
            x = stack.pop()
            if x not in g:
                g.add(x); stack.extend(adj[x] - g)
        seen |= g; groups.append(g)
    roots = set(ground["bodies"]) if ground else None
    for g in groups:
        if len(g) == 1 and next(iter(g)) not in joined:
            continue   # already reported as not held
        if roots is not None and not (g & roots):
            fails["holds"].append(f"detached group [{', '.join(sorted(g))}] does not reach a ground body "
                                  f"({', '.join(sorted(roots))}) -- no load path to the ground")
        elif roots is None and len(groups) > 1:
            fails["holds"].append(f"detached group [{', '.join(sorted(g))}] (joint graph has {len(groups)} groups)")

    # -- per pose
    jobs = []
    for n, spec in bodies.items():
        for r in spec["render"]:
            jobs += [(spec.get("scad"), dict(r))] if spec.get("static") else [(spec.get("scad"), {**r, **pose}) for pose in grid]
    try:
        rnd.prerender(jobs)
    except RuntimeError as e:
        print(f"FAIL render: a body did not render, nothing about it is known:\n{e}")
        print("BEHAVIOR: render failure")
        return EXIT_FAIL
    static_cache = {}
    worst_joint, worst_pair, worst_margin = {}, {}, None
    default_density = set()
    names = list(bodies)
    for pose in grid:
        ptxt = " ".join(f"{k}={v}" for k, v in pose.items()) or "nominal"
        meshes, masses = {}, {}
        try:
            for n in names:
                spec = bodies[n]
                if spec.get("static") and n in static_cache:
                    meshes[n] = static_cache[n]; continue
                defs_pose = {} if spec.get("static") else pose
                parts = [rnd.one((spec.get("scad"), {**r, **defs_pose})) for r in spec["render"]]
                meshes[n] = trimesh.util.concatenate(parts) if len(parts) > 1 else parts[0]
                if spec.get("static"):
                    static_cache[n] = meshes[n]
        except RuntimeError as e:
            print(f"FAIL render: a body did not render, nothing about it is known:\n{e}")
            print("BEHAVIOR: render failure")
            return EXIT_FAIL
        cm = CollisionManager()
        for n in names:
            cm.add_object(n, meshes[n])
        _, hits = cm.in_collision_internal(return_names=True)
        hits = {frozenset(h) for h in hits}

        def dist(x, y):
            if frozenset((x, y)) in hits:
                return 0.0
            c = CollisionManager(); c.add_object(x, meshes[x])
            return max(0.0, float(c.min_distance_single(meshes[y])))

        for j in joints:
            gap = dist(j["a"], j["b"])
            k = (j["a"], j["b"])
            if k not in worst_joint or gap > worst_joint[k][0]:
                worst_joint[k] = (gap, ptxt)
            if gap > float(j["max_gap"]):
                add("holds", k, gap, f"{j['a']} <-> {j['b']}: gap {gap:.2f} mm > max_gap {j['max_gap']} at {ptxt} "
                                     "-- they do not touch; the part that joins them is missing or misplaced")
        # a body of several separate pieces (four ball studs, a gear train) is held only if EVERY piece
        # reaches a joint partner, directly or through pieces of the same body that touch it; the
        # joint distance above sees only the nearest piece
        for x in names:
            for i, sh, partners in loose_pieces(x, meshes, joints):
                lo, hi = sh.bounds
                add("holds", (x, "piece", i), 1.0, f"{x}: separate piece {i + 1} at "
                    f"[{lo[0]:.0f}..{hi[0]:.0f}, {lo[1]:.0f}..{hi[1]:.0f}, {lo[2]:.0f}..{hi[2]:.0f}] reaches none of its "
                    f"joint partners ({', '.join(partners)}), not even through the body's other pieces, at {ptxt}")
        for x, y in itertools.combinations(names, 2):
            fk = frozenset((x, y))
            if fk in joint_pairs:
                continue
            lim = pair_min.get(fk, default_min)
            if fk in hits:
                try:
                    vol = float(trimesh.boolean.intersection([meshes[x], meshes[y]], engine="manifold").volume)
                except Exception:
                    vol = float("nan")
                if not vol <= VOL_EPS:   # NaN counts as interference: never a silent pass
                    add("moves", (x, y), vol if vol == vol else 1e9, f"{x} <-> {y}: interfere {vol:.2f} mm3 at {ptxt}")
                    worst_pair[fk] = (0.0, ptxt)
                    continue
                dd = 0.0
            elif lim > 0 or fk in pair_min:
                dd = dist(x, y)
            else:
                continue
            if fk in pair_min and (fk not in worst_pair or dd < worst_pair[fk][0]):
                worst_pair[fk] = (dd, ptxt)
            if dd < lim:
                add("moves", (x, y), lim - dd, f"{x} <-> {y}: {dd:.2f} mm < {lim} at {ptxt}")

        if ground and all(pose.get(k) == v for k, v in (ground.get("at") or {}).items()):
            gz, tol = float(ground["z"]), float(ground.get("tol", 0.5))
            pts = []
            for n in ground["bodies"]:
                v = meshes[n].vertices
                lo = float(v[:, 2].min())
                if abs(lo - gz) > tol:
                    add("stands", n, abs(lo - gz), f"{n}: lowest point z={lo:.2f}, ground z={gz} (tol {tol}) at {ptxt} "
                                                   "-- it does not rest on the ground")
                pts.extend(v[v[:, 2] <= gz + tol][:, :2].tolist())
            tot, mom = 0.0, np.zeros(3)
            for n in names:
                m, dflt = body_mass(bodies[n], meshes[n])
                if dflt:
                    default_density.add(n)
                c = meshes[n].center_mass if meshes[n].is_volume else meshes[n].centroid
                tot += m; mom += m * np.asarray(c)
            com = mom / tot if tot else mom
            try:
                hull = ConvexHull(np.unique(np.round(np.array(pts), 4), axis=0))
                margin = -float(np.max(hull.equations[:, :2] @ com[:2] + hull.equations[:, 2]))
            except Exception:
                add("stands", "hull", 0, f"no support polygon at {ptxt}: ground contact points are fewer than 3 "
                                          "or collinear")
                margin = None
            if margin is not None:
                if worst_margin is None or margin < worst_margin[0]:
                    worst_margin = (margin, ptxt, com)
                if margin < 0:
                    add("stands", "com", -margin, f"mass centre ({com[0]:.1f}, {com[1]:.1f}) lies outside the support "
                                                  f"polygon by {-margin:.1f} mm at {ptxt} -- it tips over")

    for (x, y), (gap, ptxt) in sorted(worst_joint.items(), key=lambda kv: -kv[1][0]):
        print(f"joint {x:12s} <-> {y:12s} widest gap {gap:6.2f} mm at {ptxt}")
    for fk, (dd, ptxt) in sorted(worst_pair.items(), key=lambda kv: kv[1][0]):
        x, y = sorted(fk)
        print(f"pair  {x:12s} <-> {y:12s} min {dd:6.2f} mm (limit {pair_min.get(fk, default_min)}) at {ptxt}")
    if worst_margin:
        m, ptxt, com = worst_margin
        print(f"mass centre ({com[0]:.1f}, {com[1]:.1f}, {com[2]:.1f}), smallest support margin {m:.1f} mm at {ptxt}")
    if default_density:
        print(f"NOTE: density 1.0 g/cm3 assumed for {', '.join(sorted(default_density))} -- set mass_g or density")
    if ground and not any(all(pz.get(k) == v for k, v in (ground.get("at") or {}).items()) for pz in grid):
        fails["stands"].append(f"ground.at {ground.get('at')} matches no pose of the grid -- nothing was checked")
    for (gate, _), (_, msg, cnt) in per_pose.items():
        fails[gate].append(msg + (f" (worst of {cnt}/{len(grid)} failing poses)" if len(grid) > 1 else ""))
    total = 0
    for gate in ("holds", "moves", "stands"):
        for f in dict.fromkeys(fails[gate]):
            print(f"FAIL {gate}: {f}")
        total += len(fails[gate])
        state = "SKIP (no ground declared)" if gate == "stands" and not ground else ("FAIL" if fails[gate] else "PASS")
        print(f"{gate.upper()}: {state}")
    print(f"BEHAVIOR: {len(grid)} pose(s), {len(bodies)} bodies, {len(joints)} joints, "
          f"{len(pair_min)} declared clearance pair(s), {total} failure(s)")
    return EXIT_FAIL if total else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
