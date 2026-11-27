# argv: out_dir case   (case: open | closed | slide) -- positioned meshes, trimesh only
import os, sys, trimesh
out, case = sys.argv[1], sys.argv[2]
def box(lo, hi):
    b = trimesh.creation.box(extents=[h - l for l, h in zip(lo, hi)]); b.apply_translation([(l + h) / 2 for l, h in zip(lo, hi)]); return b
def put(name, mesh): mesh.export(os.path.join(out, name + ".stl"))
diff = lambda a, c: trimesh.boolean.difference([a, c], engine="manifold")
hollow = lambda top: diff(box([0, 0, 0], [30, 30, 20]), box([5, 5, 5], [25, 25, 21 if top else 15]))
if case == "press":  # pin pressed 0.2 mm into the wall of an open-top block's hole
    put("block", diff(box([0, 0, 0], [30, 30, 15]), box([10, 10, 5], [20, 20, 16]))); put("pin", box([9.8, 9.8, 6], [20.2, 20.2, 14]))
elif case == "sealed_overlap":  # sealed pin overlapping the ceiling by 0.2 mm
    put("housing", hollow(False)); put("pin", box([12, 12, 6], [18, 18, 15.2]))
elif case == "thinwall":  # two 1 mm cubes (one STL) sealed behind a 0.4 mm ceiling
    put("housing", diff(box([0, 0, 0], [30, 30, 20]), box([5, 5, 5], [25, 25, 19.6])))
    put("pins", trimesh.util.concatenate([box([10, 10, 10], [11, 11, 11]), box([19, 19, 18], [20, 20, 19])]))
elif case == "slide":   # two plates sharing the face z=5, free to slide apart
    put("plate_a", box([0, 0, 0], [20, 20, 5])); put("plate_b", box([0, 0, 5], [20, 20, 10]))
else:
    if case == "open":  # open-top box, block inside, lid on top
        put("housing", hollow(True)); put("block", box([10, 10, 5], [20, 20, 12])); put("lid", box([0, 0, 20], [30, 30, 23]))
    else:               # closed housing: a pin sealed in a cavity (walls close at the top)
        put("housing", hollow(False)); put("pin", box([12, 12, 6], [18, 18, 14]))
