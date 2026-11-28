#!/usr/bin/env python3
"""blk_shear: 4 x 20 x 20 mm stub, x from 0 to 4 (a short, deep beam: shear governs over bending)."""
import os, sys, trimesh
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
b = trimesh.creation.box([4, 20, 20]); b.apply_translation([2, 0, 0]); b.export(f"{out}/blk_shear.stl")
