# AC-H1 / AC-H2 (wave 2) fixture builder.  argv: out_dir mode [length] [extra json fields]
#   block: 40x40x30 block (z 0..30) with a blind round hole from the top; screw starts at the top face.
#   modes: engage  -> M4 pilot d3.3, hole 20 deep, screw length argv[3]; argv[4] = extra fastener fields (json)
#          insert  -> M3 insert hole d4.0, 10 deep, screw M3 length argv[3], "insert": "M3", insert_from 0
#          bottom  -> M4 pilot d3.3, hole only 10 deep, screw length 16 (tip hits the hole bottom)
#          twoplane-> part on plate (z=10 top) AND on a step (z=15 top) that carries an unused hole
import json, sys, trimesh
out, mode = sys.argv[1], sys.argv[2]
def box(lo, hi):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)]); b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)]); return b
def zcyl(d, x, y, z0, z1):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=48); c.apply_translation([x, y, (z0 + z1) / 2]); return c
diff = lambda a, cuts: trimesh.boolean.difference([a] + cuts, engine="manifold")
if mode == "twoplane":
    plate = trimesh.boolean.union([box([0, 0, 0], [60, 40, 10]), box([60, 0, 0], [80, 40, 15])], engine="manifold")
    diff(plate, [zcyl(3.3, 30, 20, -1, 11), zcyl(5, 70, 20, -1, 16)]).export(f"{out}/plate.stl")
    diff(trimesh.boolean.union([box([0, 0, 10], [60, 40, 20]), box([60, 0, 15], [80, 40, 20])], engine="manifold"),
         [zcyl(5.5, 30, 20, 9, 21)]).export(f"{out}/leg.stl")
    json.dump({"mounts": [{"part": "leg", "on": "plate"}], "fasteners": [{
        "name": "leg M4", "start": [30, 20, 20], "axis": [0, 0, -1], "d": 4, "length": 18, "head_d": 8.5, "head_h": 5,
        "into": "plate", "thread_from": 10}]}, open(f"{out}/f.json", "w"))
    sys.exit(0)
d, depth, L = {"engage": (3.3, 20, 16), "insert": (4.0, 10, 8), "bottom": (3.3, 10, 16)}[mode]
if len(sys.argv) > 3: L = float(sys.argv[3])
diff(box([-20, -20, 0], [20, 20, 30]), [zcyl(d, 0, 0, 30 - depth, 31)]).export(f"{out}/block.stl")
f = {"name": "screw", "start": [0, 0, 30], "axis": [0, 0, -1], "d": 3 if mode == "insert" else 4, "length": L,
     "head_d": 8, "head_h": 3}
if mode == "insert": f.update({"insert": "M3", "insert_in": "block", "insert_from": 0})
else: f["into"] = "block"
if len(sys.argv) > 4: f.update(json.loads(sys.argv[4]))
json.dump([f], open(f"{out}/f.json", "w"))
