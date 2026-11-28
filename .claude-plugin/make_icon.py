"""Regenerate icon.png (1024 px): a weathered teal gear with copper circuit traces on a dark grid.

Run: uv run --with pillow --with numpy python .claude-plugin/make_icon.py
Procedural, no external assets, fixed seed (same file every run).
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1024
rng = np.random.default_rng(7)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")


def gear_polygon(cx, cy, r_root, r_tip, teeth, tip_frac=0.42, root_frac=0.55, steps=12):
    pts = []
    pitch = 2 * math.pi / teeth
    for i in range(teeth):
        a0 = i * pitch
        # root arc, flank up, tip arc, flank down
        ra, rb = a0, a0 + pitch * root_frac
        ta = a0 + pitch * (root_frac + (1 - root_frac - tip_frac) / 2)
        tb = ta + pitch * tip_frac
        for k in range(steps):
            a = ra + (rb - ra) * k / steps
            pts.append((cx + r_root * math.cos(a), cy + r_root * math.sin(a)))
        for k in range(steps + 1):
            a = ta + (tb - ta) * k / steps
            pts.append((cx + r_tip * math.cos(a), cy + r_tip * math.sin(a)))
    return pts


def noise(scale, octaves=4):
    """Smooth value noise in [0, 1] built from upscaled random grids."""
    acc = np.zeros((S, S))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        n = max(2, int(S / scale * 2 ** o))
        g = Image.fromarray((rng.random((n, n)) * 255).astype(np.uint8)).resize((S, S), Image.BICUBIC)
        acc += amp * np.asarray(g, float) / 255
        tot += amp
        amp *= 0.5
    return acc / tot


# background: near-black blue with a faint grid
bg = np.zeros((S, S, 3))
bg[:] = (11, 20, 26)
img = Image.fromarray(bg.astype(np.uint8))
d = ImageDraw.Draw(img)
for x in range(0, S, 32):
    d.line([(x, 0), (x, S)], fill=(17, 34, 40), width=1)
    d.line([(0, x), (S, x)], fill=(17, 34, 40), width=1)

# gear mask: toothed ring with a big bore
cx, cy = S * 0.5, S * 0.5
mask = Image.new("L", (S, S), 0)
md = ImageDraw.Draw(mask)
md.polygon(gear_polygon(cx, cy, 390, 470, 12), fill=255)
md.ellipse([cx - 270, cy - 270, cx + 270, cy + 270], fill=0)
m = np.asarray(mask, float) / 255

# patina texture: teal base, darker blotches, rust patches
n1, n2, n3 = noise(140), noise(60), noise(18, 2)
teal = np.array([47, 128, 122]); dark = np.array([20, 62, 62]); rust = np.array([112, 58, 32])
tex = teal * (0.55 + 0.45 * n1[..., None]) * (0.75 + 0.35 * n3[..., None])
tex = tex * (1 - 0.6 * (n2[..., None] > 0.58)) + dark * 0.6 * (n2[..., None] > 0.58)
rust_m = ((n1 < 0.38) & (n3 > 0.5))[..., None]
tex = np.where(rust_m, rust * (0.7 + 0.4 * n3[..., None]), tex)
# bevel shading: lighter toward upper-left
yy, xx = np.mgrid[0:S, 0:S]
shade = 0.85 + 0.3 * (1 - (xx + yy) / (2 * S))
tex = np.clip(tex * shade[..., None], 0, 255)

base = np.asarray(img, float)
comp = base * (1 - m[..., None]) + tex * m[..., None]
img = Image.fromarray(comp.astype(np.uint8))

# soft dark rim on the gear edge (depth)
edge = mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(3))
e = np.asarray(edge, float)[..., None] / 255
img = Image.fromarray(np.clip(np.asarray(img, float) * (1 - 0.7 * e), 0, 255).astype(np.uint8))

# warm glow at the bottom of the bore
glow = Image.new("L", (S, S), 0)
ImageDraw.Draw(glow).ellipse([cx - 150, cy + 190, cx + 150, cy + 290], fill=150)
glow = np.asarray(glow.filter(ImageFilter.GaussianBlur(40)), float)[..., None] / 255
inner = Image.new("L", (S, S), 0)
ImageDraw.Draw(inner).ellipse([cx - 270, cy - 270, cx + 270, cy + 270], fill=255)
glow *= np.asarray(inner, float)[..., None] / 255
img = Image.fromarray(np.clip(np.asarray(img, float) + glow * np.array([200, 110, 40]), 0, 255).astype(np.uint8))

# copper circuit traces running over the right half of the gear, 45-degree bends, pad at each end
d = ImageDraw.Draw(img)
copper, copper_dark = (205, 140, 70), (120, 72, 30)
for i in range(6):
    y0 = 300 + i * 70
    x0 = 1024 + 10
    x1 = 760 - i * 22
    y1 = y0 + (x0 - x1) * 0.0
    x2 = x1 - 90
    y2 = y1 + 90
    path = [(x0, y0), (x1, y1), (x2, y2), (x2 - 60 - i * 8, y2)]
    for w, c in ((14, copper_dark), (8, copper)):
        d.line(path, fill=c, width=w, joint="curve")
    px, py = path[-1]
    d.ellipse([px - 14, py - 14, px + 14, py + 14], outline=copper, width=6, fill=(11, 20, 26))

img.save(OUT, optimize=True)
print(OUT, os.path.getsize(OUT))
