#!/usr/bin/env python3
"""P35: can the assembly be taken apart (so put together) by straight moves?

Greedy disassembly on the positioned meshes (build/positioned/*.stl): repeatedly find a
remaining part that can translate along one straight direction until its bounding box
clears every other remaining part, without colliding. Remove it, record (part, direction).
A part is tried along +-X, +-Y, +-Z first, then 20 cube diagonals and 30 Fibonacci sphere
directions. If no remaining part can leave: FAIL naming the trapped parts.

Contact is not a collision: the moving part is eroded along its vertex normals so each face
retreats by 0.6-1x --clearance (default 0.05 mm), so touching faces may slide.

assembly.json (optional, --exceptions): {"inserted_before": [{"part": "pin", "reason": "..."}],
"flex": [...]} -- those parts are left out of the search and named in the output.

Pairs that already overlap in the as-built pose are NOT ignored by default: the search runs
strict first. A part that can leave only if an overlap is ignored gives exit 2 "NOT VERIFIED"
unless assembly.json declares the pair under "press_fit": [{"pair": [a, b], "direction": [x, y, z],
"reason": ".."}] -- then a or b may move along +-direction through that overlap (PASS + INFO).

shortcut: straight translation only (no rotation, no multi-part moves) and a step test. The step
is 0.5 x the 2nd-percentile sampled wall thickness over all parts (floor 0.1 mm), so a feature
thinner than that percentile (a few thin ribs among thick walls) can still be tunnelled. Upgrade
to a swept-volume test when that bites. Out of time budget = exit 2, never PASS.

Exit: 0 ok / SKIP, 2 degraded (unloadable mesh, time budget), 3 fail, 4 usage.
"""
import argparse
import glob
import json
import math
import os
import sys
import time

EXIT_OK, EXIT_DEGRADED, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4

try:
    import numpy as np
    import trimesh
    from trimesh.collision import CollisionManager
except ImportError:
    __import__("mesh_python").reexec()
    print("ERROR: trimesh/python-fcl not installed. Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def directions():
    d = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    d += [v for v in ((x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1))
          if sum(map(abs, v)) >= 2]
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(30):
        z = 1 - 2 * (i + 0.5) / 30
        r = math.sqrt(1 - z * z)
        d.append((r * math.cos(ga * i), r * math.sin(ga * i), z))
    return [tuple(np.array(v) / np.linalg.norm(v)) for v in d]


def travel(box, others, d):
    """Distance along d after which `box` has left every other bbox (slab method); 0 if never inside."""
    tmax = 0.0
    for o in others:
        lo, hi = 0.0, math.inf
        for k in range(3):
            a, b = box[0][k] - o[1][k], box[1][k] - o[0][k]  # intersect while a + t*d < 0 < b + t*d
            if abs(d[k]) < 1e-12:
                if not (a < 0 < b):
                    lo, hi = 1, 0
                    break
            else:
                t1, t2 = sorted((-a / d[k], -b / d[k]))
                lo, hi = max(lo, t1), min(hi, t2)
        if lo < hi:
            tmax = max(tmax, hi)
    return tmax


def shrink(mesh, c):
    """Erode the mesh: every vertex moves c mm against its normal (each face retreats 0.6c..c),
    so touching faces do not collide. Scaling about the centre would thicken cavity walls."""
    m = mesh.copy()
    m.vertices = m.vertices - m.vertex_normals * c
    return m


# ignore_for(d) -> partner names whose collision is ignored while moving along d
def can_leave(name, meshes, shrunk, mgr, remaining, dirs, step, deadline, ignore_for):
    others = [meshes[n].bounds for n in remaining if n != name]
    if not others:
        return dirs[0]
    mgr.remove_object(name)
    try:
        for d in dirs:
            tmax = travel(meshes[name].bounds, others, d)
            ok = True
            for i in range(1, int(math.ceil(tmax / step)) + 2):
                if time.time() > deadline:
                    raise TimeoutError
                T = np.eye(4)
                T[:3, 3] = np.array(d) * min(i * step, tmax + step)
                hit, names = mgr.in_collision_single(shrunk[name], transform=T, return_names=True)
                if hit and set(names) - ignore_for(d):
                    ok = False
                    break
            if ok:
                return d
    finally:
        mgr.add_object(name, meshes[name])
    return None


def wall_step(meshes, cap=1500):
    """0.5 x the 2nd-percentile inward-ray wall thickness over all parts (check_printability's ray
    technique); floor 0.1 mm. A part with no ray hits falls back to its smallest extent."""
    best = None
    for m in meshes.values():
        idx = np.random.default_rng(0).choice(len(m.faces), size=min(cap, len(m.faces)), replace=False)
        o = m.triangles_center[idx] - m.face_normals[idx] * 1e-4
        loc, ray, _ = trimesh.ray.ray_triangle.RayMeshIntersector(m).intersects_location(
            o, -m.face_normals[idx], multiple_hits=False)
        t = [float(np.linalg.norm(l - o[r])) for l, r in zip(loc, ray)]
        v = float(np.percentile(t, 2)) if t else float(m.extents.min())
        best = v if best is None else min(best, v)
    return max(0.1, 0.5 * (best if best else 1.0))


def fmt(d):
    return "(" + ", ".join(f"{v:+.2f}" for v in d) + ")"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--positioned", default=None, help="dir of positioned STLs (default <project>/build/positioned)")
    ap.add_argument("--exceptions", default=None, help="assembly.json (default <project>/assembly.json if present)")
    ap.add_argument("--clearance", type=float, default=0.05, help="mm of contact that is not a collision")
    ap.add_argument("--time-budget", type=float, default=60.0, help="seconds before giving up as degraded")
    a = ap.parse_args()
    pos = a.positioned or os.path.join(a.project_dir, "build", "positioned")
    stls = sorted(glob.glob(os.path.join(pos, "*.stl")))
    if not stls:
        print(f"SKIP: assembly_sequence, no positioned STLs in {pos} (run validate_scad.sh --all) -- not checked")
        return EXIT_OK
    exc_path = a.exceptions or os.path.join(a.project_dir, "assembly.json")
    skipped, press_fit = {}, []
    if os.path.isfile(exc_path):
        try:
            data = json.load(open(exc_path))
            for key in ("inserted_before", "flex"):
                for e in data.get(key, []):
                    skipped[e["part"].lower()] = (key, e.get("reason", ""))
            for e in data.get("press_fit", []):
                x, y = (q.lower() for q in e["pair"])
                d = np.array(e["direction"], dtype=float)
                press_fit.append({"pair": (x, y), "dir": d / np.linalg.norm(d)})
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            print(f"ERROR: {exc_path}: {e}", file=sys.stderr)
            return EXIT_USAGE
    stems = {os.path.splitext(os.path.basename(p))[0].lower() for p in stls}
    named = set(skipped) | {q for e in press_fit for q in e["pair"]}
    if named - stems:
        print(f"ERROR: {exc_path} names no such positioned part: {', '.join(sorted(named - stems))}",
              file=sys.stderr)
        return EXIT_USAGE
    meshes = {}
    for p in stls:
        n = os.path.splitext(os.path.basename(p))[0]
        if n.lower() in skipped:
            continue
        try:
            m = trimesh.load(p, force="mesh")
            if len(m.faces) == 0:
                raise ValueError("empty")
            meshes[n] = m
        except Exception as e:  # noqa: BLE001
            print(f"DEGRADED: assembly_sequence, cannot read {p}: {e} -- not checked")
            return EXIT_DEGRADED
    if not meshes:
        print("SKIP: assembly_sequence, every part is excepted in assembly.json -- not checked")
        return EXIT_OK
    for n, (kind, why) in sorted(skipped.items()):
        print(f"INFO: assembly_sequence, {n} skipped ({kind}): {why or 'no reason given'}")
    step = wall_step(meshes)
    shrunk = {n: shrink(m, a.clearance) for n, m in meshes.items()}
    mgr = CollisionManager()
    for n, m in meshes.items():
        mgr.add_object(n, m)
    overlap = {n: set() for n in meshes}  # pairs already overlapping in the as-built pose
    for n in sorted(meshes):
        for o in mgr.in_collision_single(shrunk[n], return_names=True)[1] - {n}:
            overlap[n].add(o)
            overlap[o].add(n)
    orig = {n.lower(): n for n in meshes}
    press = {}
    for e in press_fit:
        x, y = (orig.get(q) for q in e["pair"])
        if x and y:
            press.setdefault(x, {})[y] = e["dir"]
            press.setdefault(y, {})[x] = e["dir"]
    dirs, remaining, order, unverified, used = directions(), sorted(meshes), [], [], []
    deadline = time.time() + a.time_budget
    try:
        while remaining:
            for n in remaining:
                none = lambda d: set()
                def declared(d, n=n):
                    return {o for o, pd in press.get(n, {}).items() if abs(np.dot(pd, d)) >= 0.999}
                every = lambda d, n=n: overlap[n]
                for how, fn in (("strict", none), ("press", declared), ("overlap", every)):
                    if how != "strict" and not any(overlap[n]):
                        break
                    d = can_leave(n, meshes, shrunk, mgr, remaining, dirs, step, deadline, fn)
                    if d is not None:
                        break
                if d is not None:
                    order.append((n, d))
                    if how == "press":
                        used.append((n, sorted(declared(d))))
                    elif how == "overlap":
                        unverified.append((n, sorted(overlap[n] & set(remaining))))
                    remaining.remove(n)
                    mgr.remove_object(n)
                    break
            else:
                print(f"FAIL: assembly_sequence, trapped: no straight removal direction for "
                      f"{', '.join(remaining)} -- Hint: open a path for the first part to leave (move or split the part "
                      f"that blocks it), or declare it in assembly.json")
                for n in remaining:
                    print(f"FAIL: part {n} is trapped: no straight removal direction -- Hint: open a path for it, "
                          f"or declare it in assembly.json (\"inserted_before\" / \"flex\" / \"press_fit\") with a reason")
                print("Fix: open a path, or declare the part in assembly.json "
                      "(\"inserted_before\" / \"flex\" / \"press_fit\") with a reason.")
                return EXIT_FAIL
    except TimeoutError:
        print(f"DEGRADED: assembly_sequence, time budget {a.time_budget:.0f} s exceeded with "
              f"{len(remaining)} part(s) left -- not checked")
        return EXIT_DEGRADED
    for n, ps in used:
        print(f"INFO: assembly_sequence, {n} leaves through declared press fit with {', '.join(ps)} "
              f"(interference is checked by the collisions gate)")
    if unverified:
        for n, ps in unverified:
            for o in ps:
                print(f"NOT VERIFIED: removal of {n} needs overlap {n} <-> {o} to separate (press fit / snap); "
                      f"declare it under \"press_fit\" in assembly.json or fix the overlap")
        return EXIT_DEGRADED
    print(f"PASS: assembly_sequence, {len(order)} part(s) can be removed one by one"
          + (f", {len(skipped)} excepted" if skipped else ""))
    for i, (n, d) in enumerate(order, 1):
        print(f"  {i}. {n} along {fmt(d)}")
    print("Assembly order = reverse of the above. Straight translations only; one static check.")
    return EXIT_OK


if __name__ == "__main__":
    _exit = main()
    try:
        from validation_log import log_run, label_for_exit
        log_run("assembly_sequence", _exit, "check_assembly_sequence.py " + " ".join(sys.argv[1:]),
                label_for_exit(_exit))
    except Exception:
        pass
    sys.exit(_exit)
