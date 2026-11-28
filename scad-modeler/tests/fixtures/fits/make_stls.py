# argv: out_dir peg_d hole_d  -- a peg (z 0..20) through a 30x30x10 block (z 5..15) bored to hole_d, both centred on the z axis
# argv: out_dir near gap      -- two 10x10x5 blocks `gap` mm apart (face to face)
import os, sys, trimesh
out = sys.argv[1]
def put(name, m): m.export(os.path.join(out, name + ".stl"))
def box(ex, at):
    b = trimesh.creation.box(extents=ex); b.apply_translation(at); return b
if sys.argv[2] == "near":
    g = float(sys.argv[3])
    put("blk_a", box([10, 10, 5], [0, 0, 2.5])); put("blk_b", box([10, 10, 5], [0, 0, 5 + g + 2.5]))
else:
    pd, hd = float(sys.argv[2]), float(sys.argv[3])
    peg = trimesh.creation.cylinder(radius=pd / 2, height=20, sections=192); peg.apply_translation([0, 0, 10])
    bore = trimesh.creation.cylinder(radius=hd / 2, height=12, sections=192); bore.apply_translation([0, 0, 10])
    put("peg", peg); put("plate", trimesh.boolean.difference([box([30, 30, 10], [0, 0, 10]), bore], engine="manifold"))
