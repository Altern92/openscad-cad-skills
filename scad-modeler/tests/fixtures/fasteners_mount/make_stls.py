# P20 (INC-2026-11-13-02, recurrence of INC-2026-11-08-01): a motor-mount leg built in a Python
# script (not parts/*.scad) sits on a plate that already carries two bearing-block bolt heads.
#   argv: out_dir reliefs(0/1) holes(0/1)
import sys, trimesh
out, reliefs, holes = sys.argv[1], sys.argv[2] == "1", sys.argv[3] == "1"
def box(lo, hi):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)]); b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)]); return b
def zcyl(d, x, y, z0, z1):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=48); c.apply_translation([x, y, (z0 + z1) / 2]); return c
diff = lambda a, cuts: trimesh.boolean.difference([a] + cuts, engine="manifold") if cuts else a
BK, LEG = [(15, 10), (15, 30)], [(45, 10), (45, 30)]
diff(box([0, 0, 0], [60, 40, 10]), [zcyl(3.3, x, y, -1, 11) for x, y in BK] + [zcyl(4.2, x, y, -1, 11) for x, y in LEG]).export(f"{out}/plate.stl")
cuts = ([zcyl(10, x, y, 9, 16) for x, y in BK] if reliefs else []) + ([zcyl(5.5, x, y, 9, 21) for x, y in LEG] if holes else [])
diff(box([0, 0, 10], [60, 40, 20]), cuts).export(f"{out}/leg.stl")
