#!/usr/bin/env python3
"""Positioned STLs for strength_gates: insert blocks (good / at knurl OD / shallow / thin wall) and bars."""
import os, sys, trimesh
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
def hole(d, depth, x=0.0, y=0.0, top=15.0):
    c = trimesh.creation.cylinder(radius=d / 2, height=depth + 0.02, sections=96)
    c.apply_translation([x, y, top - depth / 2 + 0.01]); return c
def block(name, d, depth, x=0.0):
    b = trimesh.creation.box([20, 20, 15]); b.apply_translation([0, 0, 7.5])
    trimesh.boolean.difference([b, hole(d, depth, x)], engine="manifold").export(f"{out}/{name}.stl")
block("blk_good", 4.2, 6.7)
block("blk_knurl", 4.6, 6.7)
block("blk_shallow", 4.2, 5.9)
block("blk_wall", 4.2, 6.7, x=10 - 2.1 - 1.0)          # 1.0 mm wall to the side face (< W 1.6)
# audit A7 (2026-11-28): the median of 5 depths hid a Ø6.0 top 2.4 mm of the insert zone; 12 sampled directions
# missed a 0.8 mm saw cut through the wall 15 deg off them
import numpy as np
def cyl(d, z0, z1):
    c = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=96); c.apply_translation([0, 0, (z0 + z1) / 2]); return c
def blk():
    b = trimesh.creation.box([20, 20, 15]); b.apply_translation([0, 0, 7.5]); return b
D = lambda a, b: trimesh.boolean.difference([a, b], engine="manifold")
U = lambda l: trimesh.boolean.union(l, engine="manifold")
D(blk(), U([cyl(6.0, 12.6, 15.01), cyl(4.2, 8.29, 15.01)])).export(f"{out}/blk_step.stl")
s = trimesh.creation.box([0.8, 12, 15]); s.apply_translation([0, -6, 8.3])
s.apply_transform(trimesh.transformations.rotation_matrix(np.radians(15), [0, 0, 1]))
D(blk(), U([cyl(4.2, 8.29, 15.01), s])).export(f"{out}/blk_slit.stl")
def bar(name, size, length, axis="x", gap=False):
    ext = {"x": [length, size, size], "z": [size, size, length]}[axis]
    b = trimesh.creation.box(ext); b.apply_translation([e / 2 if a == axis else 0 for a, e in zip("xyz", ext)])
    if gap:
        g = trimesh.creation.box([4, size + 2, size + 2]); g.apply_translation([length / 2, 0, 0])
        b = trimesh.boolean.difference([b, g], engine="manifold")
    b.export(f"{out}/{name}.stl")
bar("bar_x6", 6, 50)
bar("bar_x3", 3, 50)
bar("bar_z6", 6, 50, axis="z")
bar("bar_gap", 6, 50, gap=True)
