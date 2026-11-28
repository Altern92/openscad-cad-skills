# P32 bearing seat fixture. argv: out_dir bore_depth
#   housing 40x40x12 (z 0..12): O22 bore `bore_depth` deep from the top, O15 through below (the shoulder);
#   bearing O21.98 x 7 sits on the shoulder (608-size: 22 x 7, peg = outer ring).
import sys, trimesh
out, depth = sys.argv[1], float(sys.argv[2])
def zcyl(d, z0, z1):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=128); c.apply_translation([0, 0, (z0 + z1) / 2]); return c
box = trimesh.creation.box(extents=[40, 40, 12]); box.apply_translation([0, 0, 6])
trimesh.boolean.difference([box, zcyl(22, 12 - depth, 13), zcyl(15, -1, 13)], engine="manifold").export(f"{out}/housing.stl")
zcyl(21.98, 12 - depth, 12 - depth + 7).export(f"{out}/bearing.stl")
