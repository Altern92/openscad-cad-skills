#!/usr/bin/env python3
"""P25 / AC-9, AC-10 helpers.
  meta.py transform <src_dir> <dst_dir> <seed> [--geometry-only]
      rigid motion (rotation + translation from the seed) of build/positioned/*.stl, *.stl and the
      coordinates in fasteners.json (start, axis) and loads.json (support, at, force_N, print_up);
      --geometry-only moves the meshes but not the declarations (the negative case)
  meta.py compare <a.txt> <b.txt>      same lines, numbers within 0.05 abs or 1 % rel -> exit 0
  meta.py sections <scripts_dir>       section_props against closed forms -> exit 0"""
import glob, json, os, re, shutil, sys
import numpy as np


def rot(seed):
    r = np.random.default_rng(seed)
    q, _ = np.linalg.qr(r.normal(size=(3, 3)))
    if np.linalg.det(q) < 0:
        q[:, 0] *= -1
    return q, r.uniform(-200, 200, 3)


def transform(src, dst, seed, geom_only):
    import trimesh
    R, t = rot(int(seed))
    shutil.copytree(src, dst)
    T = np.eye(4); T[:3, :3] = R; T[:3, 3] = t
    for f in glob.glob(os.path.join(dst, "**", "*.stl"), recursive=True):
        m = trimesh.load(f, force="mesh"); m.apply_transform(T); m.export(f)
    if geom_only:
        return
    P = lambda v: (R @ np.asarray(v, float) + t).tolist()
    V = lambda v: (R @ np.asarray(v, float)).tolist()
    fp = os.path.join(dst, "fasteners.json")
    if os.path.isfile(fp):
        d = json.load(open(fp))
        for f in (d if isinstance(d, list) else d.get("fasteners", [])):
            f["start"], f["axis"] = P(f["start"]), V(f["axis"])
        json.dump(d, open(fp, "w"))
    lp = os.path.join(dst, "loads.json")
    if os.path.isfile(lp):
        d = json.load(open(lp))
        for c in d.get("cases", []):
            c["support"], c["at"], c["force_N"] = P(c["support"]), P(c["at"]), V(c["force_N"])
            c["print_up"] = V(c.get("print_up", [0, 0, 1]))
        json.dump(d, open(lp, "w"))


NUM = re.compile(r"[-+]?\d+\.?\d*(?:e[-+]?\d+)?")
COORD = re.compile(r"\[[-0-9., ]+\]")   # assembly coordinates move with the assembly: not compared


def compare(a, b):
    la, lb = [COORD.sub("[xyz]", open(x).read()).splitlines() for x in (a, b)]
    bad = []
    if len(la) != len(lb):
        bad.append(f"{len(la)} lines vs {len(lb)}")
    for x, y in zip(la, lb):
        if NUM.sub("#", x) != NUM.sub("#", y):
            bad.append(f"text differs:\n  {x}\n  {y}")
            continue
        for u, v in zip(map(float, NUM.findall(x)), map(float, NUM.findall(y))):
            if abs(u - v) > max(0.05, 0.01 * abs(u)):
                bad.append(f"number {u} vs {v}:\n  {x}\n  {y}")
    print("\n".join(bad) or "same")
    return 1 if bad else 0


def sections(scripts):
    sys.path.insert(0, scripts)
    from check_strength import section_props
    from shapely.geometry import Polygon, Point
    from shapely import affinity
    r, bad = np.random.default_rng(7), []
    for i in range(20):
        b, h = r.uniform(1, 30, 2)
        ang, dx, dy = r.uniform(0, 180), *r.uniform(-50, 50, 2)
        D = r.uniform(4, 40); d = r.uniform(0.2, 0.8) * D
        rect = affinity.translate(affinity.rotate(Polygon([(0, 0), (b, 0), (b, h), (0, h)]), ang), dx, dy)
        tube = Point(dx, dy).buffer(D / 2, 256).difference(Point(dx, dy).buffer(d / 2, 256))
        for name, poly, want_a, want_i in (
                ("rect", rect, b * h, sorted([b * h ** 3 / 12, h * b ** 3 / 12])),
                ("tube", tube, np.pi * (D ** 2 - d ** 2) / 4, [np.pi * (D ** 4 - d ** 4) / 64] * 2)):
            A, _, Sxx, Syy, Sxy = section_props(poly)
            got = sorted(np.linalg.eigvalsh([[Sxx, Sxy], [Sxy, Syy]]))
            if abs(A - want_a) > 0.02 * want_a or any(abs(g - w) > 0.02 * w for g, w in zip(got, want_i)):
                bad.append(f"{name} #{i}: A {A:.3f} vs {want_a:.3f}, I {got} vs {want_i}")
    print("\n".join(bad) or "sections match closed forms (40 cases)")
    return 1 if bad else 0


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    if cmd == "transform":
        transform(a[0], a[1], a[2], "--geometry-only" in a)
    elif cmd == "compare":
        sys.exit(compare(*a))
    else:
        sys.exit(sections(*a))
