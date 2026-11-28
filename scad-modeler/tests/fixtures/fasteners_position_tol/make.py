# P40 fixture builder (Bethune sec 8-48: O20 holes, T = 0.03 -> floating F <= 19.97, fixed F <= 19.94).
# argv: out_dir floating|fixed d
#   floating: two 10 mm plates (z 0..20), O20 holes, through-bolt (no `into`), position_tol 0.03
#   fixed   : top plate z 10..20 with O20 hole, base z -20..10 with an M20 tap drill O17.5, screw into base
import json, sys, trimesh
out, mode, d = sys.argv[1], sys.argv[2], float(sys.argv[3])
def box(lo, hi):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)]); b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)]); return b
def zcyl(dd, z0, z1):
    c = trimesh.creation.cylinder(radius=dd / 2, height=z1 - z0, sections=360); c.apply_translation([0, 0, (z0 + z1) / 2]); return c
diff = lambda a, cuts: trimesh.boolean.difference([a] + cuts, engine="manifold")
f = {"name": f"{mode} d{d}", "start": [0, 0, 20], "axis": [0, 0, -1], "d": d, "head_d": 32, "head_h": 12,
     "position_tol": 0.03}
if mode == "floating":
    diff(box([-30, -30, 10], [30, 30, 20]), [zcyl(20, 9, 21)]).export(f"{out}/top.stl")
    diff(box([-30, -30, 0], [30, 30, 10]), [zcyl(20, -1, 11)]).export(f"{out}/bottom.stl")
    f.update({"length": 20})
else:
    diff(box([-30, -30, 10], [30, 30, 20]), [zcyl(20, 9, 21)]).export(f"{out}/top.stl")
    diff(box([-30, -30, -20], [30, 30, 10]), [zcyl(17.5, -15, 11)]).export(f"{out}/base.stl")
    f.update({"length": 30, "pitch": 2.5, "thread_from": 10, "into": "base"})
json.dump([f], open(f"{out}/f.json", "w"))
