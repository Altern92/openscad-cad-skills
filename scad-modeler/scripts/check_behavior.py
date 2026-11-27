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

KINEMATICS (P24, only when a joint has "type"):
  joint "type": fixed | ball | revolute | slider; ball/revolute/slider need "at": [x,y,z] (assembly
  coords at the dof pose), revolute/slider need "axis". Untyped joints count as fixed.
  "dof": {"count": 2, "why": [...], "idle": [{"body": "tie_rod", "why": "spins on its balls"}],
          "at": {"BUMP": 0}}            # pose for the Jacobian (default: all-zero grid point, else first)
  DOF = 6 x moving bodies - rank(constraint Jacobian), SVD; static bodies are the world. More DOF
  than count + idle = a body moves with nothing stopping it (named); fewer = the mechanism locks.
  An "at" not within max_gap of one body and 5 mm of the other = an invented anchor -> FAIL. A body in a typed joint
  must be ONE piece (several separate studs that move with different parts are several bodies).
  joint "angle": {"echo": "UB_TILT", "max_deg": 15, "source": ".."} -- OpenSCAD is run per pose with
  the body defines and must print `ECHO: UB_TILT = <deg>`; |value| > max_deg at any pose -> FAIL.

Not a physics simulation: no forces, friction or strength (check_strength.py does static strength).

Usage: python3 check_behavior.py --project-dir . [--behavior behavior.json] [-D NAME=VALUE ...]
Exit: 0 pass, 3 fail (incl. a body that does not render), 4 usage (bad JSON, unknown body).
"""
import argparse
import glob
import hashlib
import itertools
import json
import weakref
import os
import re
import subprocess
import sys
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor

from markers import LIBRARY_RE, PREVIEW_RE

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
        t = j.get("type", "fixed")
        if t not in JOINT_ROWS:
            usage(f"{path}: joint {j['a']}-{j['b']}: type {t!r} not in {sorted(JOINT_ROWS)}")
        if t != "fixed" and len(j.get("at") or []) != 3:
            usage(f"{path}: {t} joint {j['a']}-{j['b']} needs \"at\": [x, y, z]")
        if t in ("revolute", "slider") and len(j.get("axis") or []) != 3:
            usage(f"{path}: {t} joint {j['a']}-{j['b']} needs \"axis\"")
        an = j.get("angle")
        if an is not None and not (an.get("echo") and "max_deg" in an and str(an.get("source", "")).strip()):
            usage(f"{path}: joint {j['a']}-{j['b']}: angle needs echo, max_deg and a non-empty source")
    for p in (d.get("clearance") or {}).get("pairs", []):
        for k in ("a", "b"):
            if p.get(k) not in names:
                usage(f"{path}: clearance pair names unknown body {p.get(k)!r}")
    for i in (d.get("dof") or {}).get("idle", []):
        if i.get("body") not in names:
            usage(f"{path}: dof.idle names unknown body {i.get('body')!r}")
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
# P27 / AC-13: import()/surface() data files are part of the render -- a moved import("servo.stl") kept
# its stale cached mesh. shortcut: literal file names only; a computed path (str(...)) is not followed.
DATA_RE = re.compile(r"\b(?:import|surface)\s*\([^)\"]*?\"([^\"]+)\"")   # P27b: also import(convexity=4, file="x")


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
        txt = data.decode("utf-8", "replace")
        for inc in INC_RE.findall(txt):
            todo.append(os.path.normpath(os.path.join(os.path.dirname(f), inc)))
        for dat in DATA_RE.findall(txt):
            dp = os.path.normpath(os.path.join(os.path.dirname(f), dat))
            h.update(dp.encode())
            if os.path.isfile(dp):
                with open(dp, "rb") as dh:
                    h.update(hashlib.sha256(dh.read()).digest())
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
    refs = [meshes[x]] + [meshes[y] for y, _ in partners]
    hit = _LOOSE.get(key)
    # P27 / AC-15: id() of a freed per-pose mesh can be reused; the entry holds weak references and only
    # counts when they still point at these very objects
    if hit is not None and all(w() is m for w, m in zip(hit[0], refs)):
        return hit[1]
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
    _LOOSE[key] = ([weakref.ref(m) for m in refs], out)
    return out


JOINT_ROWS = {"fixed": 6, "ball": 3, "revolute": 5, "slider": 5}
ANCHOR_REACH = 5.0   # mm: a ball centre to its cup wall (5.8 mm RC ball in its cup: ~2.9)


def _skew(p):
    return np.array([[0, -p[2], p[1]], [p[2], 0, -p[0]], [-p[1], p[0], 0]])


def _perp2(u):
    u = np.asarray(u, float) / np.linalg.norm(u)
    a = np.cross(u, [0, 0, 1] if abs(u[2]) < .9 else [1, 0, 0]); a /= np.linalg.norm(a)
    return np.vstack([a, np.cross(u, a)])


def dof_rank(joints, moving, L):
    """Instantaneous mobility: 6 x moving - rank J, and the null-space basis (rows = motions).
    Twist per moving body [v, w L] about the origin; static bodies have none."""
    col = {n: 6 * i for i, n in enumerate(moving)}
    rows = []
    for j in joints:
        t = j.get("type", "fixed")
        if t == "fixed":
            pt = np.zeros(3)
        else:
            pt = np.asarray(j["at"], float)
        Bv = np.hstack([np.eye(3), -_skew(pt) / L])          # point velocity rows
        Bw = np.hstack([np.zeros((3, 3)), np.eye(3) / L])     # angular velocity rows
        if t == "fixed":
            blk = np.vstack([Bv, Bw])
        elif t == "ball":
            blk = Bv
        elif t == "revolute":
            blk = np.vstack([Bv, _perp2(j["axis"]) @ Bw])
        else:   # slider
            blk = np.vstack([_perp2(j["axis"]) @ Bv, Bw])
        r = np.zeros((blk.shape[0], 6 * len(moving)))
        for name, sgn in ((j["a"], 1.0), (j["b"], -1.0)):
            if name in col:
                r[:, col[name]:col[name] + 6] += sgn * blk
        rows.append(r)
    if not moving:
        return 0, np.zeros((0, 0))
    J = np.vstack(rows) if rows else np.zeros((1, 6 * len(moving)))
    sv = np.linalg.svd(J, compute_uv=True)
    U, sig, Vt = sv
    tol = max(J.shape) * np.finfo(float).eps * (sig.max() if sig.size else 1.0) * 1e3
    rank = int((sig > tol).sum())
    return 6 * len(moving) - rank, J


def echo_values(rnd, scad, defines, names):
    """Run OpenSCAD for its echo output only; {name: float} for `ECHO: NAME = v` lines."""
    scad = os.path.normpath(os.path.join(rnd.project, scad or rnd.scad))
    args = sum((["-D", f"{k}={fmt(v)}"] for k, v in defines.items()), [])
    args += sum((["-D", f"{k}={v}"] for k, v in rnd.extra), [])   # same command-line defines as the meshes
    out = os.path.join(rnd.cache, hashlib.sha256((rnd.salt(scad) + scad + " ".join(args)).encode()).hexdigest()[:20] + ".echo")
    if not os.path.exists(out):
        r = subprocess.run([rnd.openscad, "-o", out] + args + [scad], cwd=os.path.dirname(scad), capture_output=True, text=True)
        if r.returncode or not os.path.exists(out):
            raise RuntimeError(f"echo run failed for {scad}: {r.stderr[-400:]}")
    txt = open(out, encoding="utf-8", errors="replace").read()
    vals = {}
    for n in names:   # echo(A=.., B=..) prints one line
        hits = [float(v) for v in re.findall(rf"(?:ECHO: |, ){re.escape(n)} = (-?[0-9.]+(?:e[-+]?[0-9]+)?)", txt)]
        if hits:      # P27 / AC-14: every match, worst |value| (a mirrored copy echoes the same name)
            vals[n] = max(hits, key=abs)
    return vals


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

    fails = {"holds": [], "moves": [], "stands": [], "kinematics": []}
    per_pose = {}   # (gate, key) -> [worst severity, message, poses failed]

    def add(gate, key, sev, msg):
        """A per-pose failure: report the worst pose once, with how many poses failed."""
        e = per_pose.setdefault((gate, key), [None, "", 0])
        e[2] += 1
        if e[0] is None or sev > e[0]:
            e[0], e[1] = sev, msg
    joint_pairs = {frozenset((j["a"], j["b"])) for j in joints}

    # -- HOLDS, coverage (P26 / AC-2): a body list that leaves a printed part out proves nothing about it
    covered, whole = set(), False
    for spec in bodies.values():
        for r in spec["render"]:
            mode, part = str(r.get("MODE", "")).strip('"'), str(r.get("PART", "")).strip('"')
            whole |= mode == "assembly"
            covered.add(part.lower())
    built = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(proj, "build", "*.stl"))}
    for scad in sorted(glob.glob(os.path.join(proj, "parts", "*.scad"))):
        name = os.path.splitext(os.path.basename(scad))[0]
        src = open(scad, encoding="utf-8", errors="replace").read()
        if whole or PREVIEW_RE.search(src) or LIBRARY_RE.search(src) or (built and name not in built):
            continue
        if name.lower() not in covered:
            fails["holds"].append(f"part {name} is in no body -- add it to behavior.json \"bodies\" (render "
                                  f"{{\"MODE\": \"part\", \"PART\": \"{name}\"}}) so the gate sees it")

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
    typed = any("type" in j for j in joints)
    dofd = d.get("dof")
    dof_at = (dofd or {}).get("at")
    # P26 / AC-16: "at" names a subset of the grid keys (like ground.at); pick the first grid pose it matches
    dof_pose = next((pz for pz in grid if all(pz.get(k) == v for k, v in dof_at.items())), None) if dof_at else \
        next((pz for pz in grid if all(v == 0 for v in pz.values())), grid[0])
    if dof_pose is None:
        usage(f"dof.at {dof_at} matches no pose of the grid {poses_decl}")
    dof_meshes = None
    angle_names = sorted({j["angle"]["echo"] for j in joints if j.get("angle")})
    worst_angle = {}
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
        if pose == dof_pose or (dof_meshes is None and pose == grid[-1]):
            dof_meshes = dict(meshes)
        if angle_names:
            try:
                # P28 / AC-A3: the echo may live in the top-level scad or in a joint body's own "scad"
                # (pulled in by use<>); run each distinct file once (echo_values caches), keep the worst |value|
                vals = {}
                for s in dict.fromkeys([d.get("scad")] + [bodies[n].get("scad") for j in joints if j.get("angle")
                                                          for n in (j["a"], j["b"])]):
                    for n, v in echo_values(rnd, s, pose, angle_names).items():
                        if n not in vals or abs(v) > abs(vals[n]):
                            vals[n] = v
            except RuntimeError as e:
                print(f"FAIL render: {e}"); print("BEHAVIOR: render failure"); return EXIT_FAIL
            for j in joints:
                an = j.get("angle")
                if not an:
                    continue
                k = (j["a"], j["b"])
                if an["echo"] not in vals:
                    fails["kinematics"].append(f"{j['a']} <-> {j['b']}: OpenSCAD printed no `ECHO: {an['echo']} = ..` "
                                               f"at {ptxt} -- the angle is not checked; add echo({an['echo']}=...)")
                    continue
                v = vals[an["echo"]]
                if k not in worst_angle or abs(v) > abs(worst_angle[k][0]):
                    worst_angle[k] = (v, ptxt, float(an["max_deg"]))
                if abs(v) > float(an["max_deg"]):
                    add("kinematics", (k, "angle"), abs(v), f"{j['a']} <-> {j['b']}: {an['echo']} = {v:.1f} deg > "
                        f"{an['max_deg']} at {ptxt} ({an['source']}) -- the purchased joint cannot swing that far")
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

    if typed and not dofd:
        fails["kinematics"].append("joints have a \"type\" but behavior.json has no \"dof\" -- declare the motions "
                                   "the mechanism must have (count, why, idle)")
    if typed and dofd:
        ptxt = " ".join(f"{k}={v}" for k, v in dof_pose.items()) or "nominal"
        for j in joints:
            t = j.get("type", "fixed")
            for nb in (j["a"], j["b"]):
                pieces = dof_meshes[nb].split(only_watertight=False)
                if t != "fixed" and len([q for q in pieces if min(q.extents) > PIECE_MIN_MM]) > 1:
                    fails["kinematics"].append(f"{nb}: {len(pieces)} separate pieces in a {t} joint -- one rigid body "
                                               "per piece (studs that move with different parts are different bodies)")
            if t != "fixed":
                pt = np.asarray(j["at"], float)
                dd = {}
                for nb in (j["a"], j["b"]):
                    m = dof_meshes[nb]
                    dd[nb] = 0.0 if m.is_volume and m.contains([pt])[0] else float(trimesh.proximity.closest_point(m, [pt])[1][0])
                near, far = sorted(dd.values())
                # a ball's centre sits inside the ball, a few mm from the cup: on one body, near the other
                if near > float(j["max_gap"]) or far > ANCHOR_REACH:
                    fails["kinematics"].append(
                        f"{j['a']} <-> {j['b']}: anchor ({pt[0]:g}, {pt[1]:g}, {pt[2]:g}) is "
                        + ", ".join(f"{dd[n]:.2f} mm from {n}" for n in dd)
                        + f" at {ptxt} (want <= max_gap {j['max_gap']} on one body, <= {ANCHOR_REACH} on the other) "
                        "-- the joint point is not on the parts")
        moving = [n for n in bodies if not bodies[n].get("static")]
        note = ""
        if not any(bodies[n].get("static") for n in bodies):
            moving, note = moving[1:], f" ({names[0]} taken as the fixed world: no static body)"
        L = max(1.0, max((np.linalg.norm(j["at"]) for j in joints if j.get("at")), default=1.0))
        ndof, J = dof_rank(joints, moving, L)
        want = int(dofd.get("count", 0)) + len(dofd.get("idle", []))
        print(f"DOF: computed {ndof}, declared {dofd.get('count', 0)} + {len(dofd.get('idle', []))} idle "
              f"({', '.join(map(str, dofd.get('why', [])))}) at {ptxt}{note}")
        if ndof > want:
            alone = []
            for i, n in enumerate(moving):
                Jb = J[:, 6 * i:6 * i + 6]
                k = 6 - int((np.linalg.svd(Jb, compute_uv=False) > 1e-9 * max(1.0, np.abs(J).max())).sum())
                if k:
                    alone.append((k, n))
            idle = {i["body"] for i in dofd.get("idle", [])}
            txt = ", ".join(f"{n} ({k} DOF{' idle' if n in idle else ''})" for k, n in sorted(alone, reverse=True))
            fails["kinematics"].append(f"{ndof} DOF > declared {want}: with every other body held, these still move: "
                                       f"{txt or 'none alone (a chain is loose)'} -- a joint is missing or too free")
        elif ndof < want:
            fails["kinematics"].append(f"{ndof} DOF < declared {want}: the mechanism locks -- the declared motion "
                                       "({}) is impossible with these joints".format(", ".join(map(str, dofd.get("why", [])))))
    for (x, y), (v, ptxt, lim) in sorted(worst_angle.items(), key=lambda kv: -abs(kv[1][0])):
        print(f"angle {x:12s} <-> {y:12s} worst {v:6.1f} deg (limit {lim}) at {ptxt}")
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
    for gate in ("holds", "moves", "stands", "kinematics"):
        for f in dict.fromkeys(fails[gate]):
            print(f"FAIL {gate}: {f}")
        total += len(fails[gate])
        state = ("SKIP (no ground declared)" if gate == "stands" and not ground else
                 "SKIP (no joint \"type\", no \"angle\")" if gate == "kinematics" and not typed and not angle_names else
                 ("FAIL" if fails[gate] else "PASS"))
        print(f"{gate.upper()}: {state}")
    print(f"BEHAVIOR: {len(grid)} pose(s), {len(bodies)} bodies, {len(joints)} joints, "
          f"{len(pair_min)} declared clearance pair(s), {total} failure(s)")
    return EXIT_FAIL if total else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
