# P41 fixture builder (Bethune sec 6-13 worked example). argv: out_dir hole_depth
#   cover 10 thick (z 15..25) with an O12 clearance hole; base z -10..15 with an M10x1.25 tap drill O8.75
#   `hole_depth` deep from z 15; screw M10x1.25x25 from z 25, so 15 mm in the base and its tip at z 0.
#   Book: 15 + 2P (2.5) = 17.5 -> tapped hole 18 deep (OK); 17 deep leaves 2.0 < 2P past the tip (WARN).
import json, sys, trimesh
out, depth = sys.argv[1], float(sys.argv[2])
def box(lo, hi):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)]); b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)]); return b
def zcyl(d, z0, z1):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=96); c.apply_translation([0, 0, (z0 + z1) / 2]); return c
diff = lambda a, cuts: trimesh.boolean.difference([a] + cuts, engine="manifold")
diff(box([-20, -20, 15], [20, 20, 25]), [zcyl(12, 14, 26)]).export(f"{out}/cover.stl")
diff(box([-20, -20, -10], [20, 20, 15]), [zcyl(8.75, 15 - depth, 16)]).export(f"{out}/base.stl")
json.dump([{"name": "M10x1.25x25", "start": [0, 0, 25], "axis": [0, 0, -1], "d": 10, "pitch": 1.25, "length": 25,
            "head_d": 16, "head_h": 6, "thread_from": 10, "into": "base"}], open(f"{out}/f.json", "w"))
