#!/usr/bin/env python3
"""Projected outline vs a reference silhouette (P6, 2026-11-01).

    // SILHOUETTE: front refs/front.png >= 0.85

projects the mesh (front = X across, Z up; side = Y across, Z up; top = X, Y),
scales both outlines to their own bounding box, and requires their
intersection-over-union on a 128 x 128 grid to reach the threshold. Size and
aspect are PROPORTION's job; this asks whether the SHAPE is the reference's.

The reference is a silhouette image: dark shape on a light background, or a
transparent background (alpha). Cut it out of the photo first; a raw photo
with clutter measures the clutter. Path is relative to the .scad file.

Usage:
    python3 check_silhouette.py --scad figure.scad --stl figure.stl

Exit codes:
    0  pass, or SKIP when nothing is declared
    3  fail -- IoU below the threshold
    4  usage error (missing file, Pillow missing -- install: uv pip install pillow)
"""
import argparse
import os
import re
import sys

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4
DECL_RE = re.compile(r"^[ \t]*//[ \t]*SILHOUETTE[ \t]*:[ \t]*(front|side|top)[ \t]+(\S+)[ \t]*>=[ \t]*([0-9.]+)", re.M)
GRID = 128
VIEWS = {"front": ([0, -1, 0], 0, 2), "side": ([1, 0, 0], 1, 2), "top": ([0, 0, 1], 0, 1)}


def grid_from_mask(mask):
    """mask: 2-D numpy bool, row 0 = top. Crop to its bbox, resample to GRID x GRID."""
    import numpy as np
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    m = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ri = (np.arange(GRID) + 0.5) * m.shape[0] / GRID
    ci = (np.arange(GRID) + 0.5) * m.shape[1] / GRID
    return m[ri.astype(int)[:, None], ci.astype(int)[None, :]]


def mesh_grid(stl, view):
    import numpy as np
    import shapely
    import trimesh
    mesh = trimesh.load(stl, force="mesh")
    _, ax_u, ax_v = VIEWS[view]
    tri = mesh.vertices[mesh.faces][:, :, [ax_u, ax_v]]
    polys = [shapely.Polygon(t) for t in tri if abs(shapely.Polygon(t).area) > 1e-12]
    outline = shapely.unary_union(polys)
    minx, miny, maxx, maxy = outline.bounds
    u = minx + (np.arange(GRID) + 0.5) * (maxx - minx) / GRID
    v = maxy - (np.arange(GRID) + 0.5) * (maxy - miny) / GRID  # row 0 = top, like an image
    uu, vv = np.meshgrid(u, v)
    return shapely.contains_xy(outline, uu, vv)


def ref_grid(path):
    import numpy as np
    from PIL import Image
    im = Image.open(path)
    if im.mode in ("RGBA", "LA") or "transparency" in im.info:
        a = np.asarray(im.convert("RGBA"))[:, :, 3]
        if a.min() < 128 <= a.max():
            return grid_from_mask(a >= 128)
    return grid_from_mask(np.asarray(im.convert("L")) < 128)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scad", required=True)
    ap.add_argument("--stl", required=True)
    a = ap.parse_args()
    for p in (a.scad, a.stl):
        if not os.path.isfile(p):
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            return EXIT_USAGE
    decls = DECL_RE.findall(open(a.scad, encoding="utf-8", errors="replace").read())
    if not decls:
        print(f"SKIP: silhouette, {a.scad} declares no // SILHOUETTE:")
        return EXIT_OK
    try:
        import PIL  # noqa: F401
        import numpy as np
    except ImportError:
        print("ERROR: Pillow not installed -- uv pip install --python \"$(bash scripts/resolve_python.sh --print)\" pillow",
              file=sys.stderr)
        return EXIT_USAGE
    fails, oks = [], []
    for view, ref, thr in decls:
        rp = os.path.join(os.path.dirname(os.path.abspath(a.scad)), ref)
        if not os.path.isfile(rp):
            print(f"ERROR: reference not found: {rp}", file=sys.stderr)
            return EXIT_USAGE
        r, m = ref_grid(rp), mesh_grid(a.stl, view)
        if r is None:
            fails.append(f"{view} {ref}: reference has no dark/opaque shape")
            continue
        iou = float(np.logical_and(r, m).sum()) / max(1, int(np.logical_or(r, m).sum()))
        (oks if iou >= float(thr) else fails).append(f"{view} vs {ref}: IoU {iou:.3f} (need >= {thr})")
    for f in fails:
        print(f"FAIL: silhouette, {a.scad}: {f}")
    if fails:
        return EXIT_FAIL
    print(f"PASS: silhouette, {a.scad}: " + "; ".join(oks))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
