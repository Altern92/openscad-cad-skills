#!/usr/bin/env python3
"""Regenerate jam_vs_gear_dist.gif: gear pair at 38.5 mm (jams) vs gear_dist() 38.845 mm.

Needs: openscad (BOSL2), python3 with trimesh, shapely, numpy, pillow, matplotlib.
Usage: python3 make_demo.py [out.gif]   (run from anywhere)
One loop = one tooth period of the pinion (360/11 deg); the spur turns 1/6 of that, opposite way.
Frames are the z-mid cross-section of the real part STLs; overlap = exact polygon intersection.
Caption numbers come from real validate_scad.sh --all runs; the OK line is verbatim, the FAIL line is the motion_sweep.py centre-distance line shortened (measured-axes note, module/teeth list and advice dropped). Re-copy them if the checker wording changes.
"""
import subprocess, sys, tempfile, io
from pathlib import Path
import numpy as np, trimesh
from shapely.geometry import MultiPolygon, Polygon
from shapely import affinity
from shapely.ops import unary_union
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "jam_vs_gear_dist.gif"
N, D_BAD, D_OK, Z1, Z2 = 30, 38.5, 38.845, 11, 66
PERIOD = 360 / Z1  # pinion rotation after which the mesh repeats
CAP_FAIL = "FAIL: centre distance pinion<->spur: axes are 38.500 mm apart, BOSL2 gear_dist() = 38.845 mm (-0.345 mm)"
CAP_OK = "OK: centre distance pinion<->spur 38.845 mm (measured axes) = gear_dist() 38.845 mm"

def load(part, tmp):
    stl = Path(tmp) / f"{part}.stl"
    subprocess.run(["openscad", "--backend=Manifold", "-o", str(stl), str(HERE / "parts" / f"{part}.scad")],
                   check=True, capture_output=True)
    s = trimesh.load(stl).section(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1])
    segs = [np.asarray(e)[:, :2] for e in s.discrete]
    rings = sorted((Polygon(r) for r in segs), key=lambda p: -p.area)
    outer, holes = rings[0], unary_union(rings[1:])
    return outer.difference(holes)

def patch(geom, **kw):
    geoms = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    verts, codes = [], []
    for g in geoms:
        for ring in [g.exterior, *g.interiors]:
            c = np.asarray(ring.coords)
            verts += list(c); codes += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(verts, codes), **kw)

def pose(pin, spur, a, d):
    p = affinity.rotate(pin, a, origin=(0, 0))
    s = affinity.rotate(spur, -a / (Z2 / Z1), origin=(0, 0))
    return p, affinity.translate(s, d, 0)

def draw(ax, pin, spur, a, d, jam_label):
    p, s = pose(pin, spur, a, d)
    ov = p.intersection(s)
    ax.add_patch(patch(p, fc="#5b8def", ec="#1c3d7a", lw=0.5))
    ax.add_patch(patch(s, fc="#9ad39a", ec="#2b6b2b", lw=0.5, alpha=0.9))
    if ov.area > 1e-6:
        ax.add_patch(patch(ov, fc="#e00000", ec="#e00000", lw=2.5))
    ax.set_xlim(-9, 19); ax.set_ylim(-8, 8)  # zoom on the mesh point
    ax.set_aspect("equal"); ax.axis("off")
    return ov.area

def main():
    with tempfile.TemporaryDirectory() as tmp:
        pin, spur = load("pinion", tmp), load("spur", tmp)
    frames, areas = [], []
    for i in range(N):
        a = i * PERIOD / N
        fig, (l, r) = plt.subplots(1, 2, figsize=(8.8, 3.6), dpi=100)
        fig.subplots_adjust(left=0, right=1, top=0.78, bottom=0.2, wspace=0)
        a1 = draw(l, pin, spur, a, D_BAD, "")
        a2 = draw(r, pin, spur, a, D_OK, "")
        areas.append((a, a1, a2))
        l.set_title(f"centre distance 38.5 mm (m(z1+z2)/2)\noverlap {a1:.2f} mm2 at pinion angle {a:4.1f} deg", fontsize=9, color="#b00000" if a1 > 1e-6 else "black")
        r.set_title(f"centre distance 38.845 mm (gear_dist)\noverlap {a2:.2f} mm2", fontsize=9)
        fig.text(0.02, 0.10, CAP_FAIL, fontsize=6.4, family="monospace", color="#b00000")
        fig.text(0.02, 0.03, CAP_OK, fontsize=6.4, family="monospace", color="#1a6b1a")
        buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig); buf.seek(0)
        frames.append(Image.open(buf).convert("RGB"))
    assert max(a[2] for a in areas) < 1e-3, "gear_dist pair must never overlap"
    assert max(a[1] for a in areas) > 0.05, "38.5 mm pair must visibly overlap"
    pal = [f.quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=90, loop=0, optimize=True)
    worst = max(areas, key=lambda t: t[1])
    print(f"{OUT} {OUT.stat().st_size} bytes {frames[0].size} frames={N} worst pinion angle {worst[0]:.2f} deg overlap {worst[1]:.3f} mm2")

if __name__ == "__main__":
    main()
