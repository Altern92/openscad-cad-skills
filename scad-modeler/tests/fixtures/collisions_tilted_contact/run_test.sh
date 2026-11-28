#!/usr/bin/env bash
# 2026-11-12 (esp32-macropad, INC-2026-11-12-01): 30 MX switches in a 15 deg plate -- body exactly
# in its cutout, top housing resting on the plate -- read as "penetration depth 5.000 mm" with
# 0.0003 mm^3 overlap. Contact sheets on a TILTED face have an axis-aligned bbox as thick as the
# tilt makes it, and a ring of sheets around a body in its hole has an oriented box 1.5 mm thick.
# src/ is a copy of that project's shell + switch files (simple tilted test cubes do not
# reproduce it: their intersection comes out empty).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
openscad -q --backend=Manifold -o "$tmp/plate.stl" "$here/src/parts/top_shell.scad" || exit 1
openscad -q --backend=Manifold -o "$tmp/switch.stl" "$here/src/parts/vit_switches.scad" || exit 1
python3 - "$SCAD_MODELER_SCRIPTS" "$tmp" <<'PY' || exit 1
import sys, math, trimesh; sys.path.insert(0, sys.argv[1]); import check_collisions as c
t = sys.argv[2]; p = trimesh.load(f"{t}/plate.stl"); s = trimesh.load(f"{t}/switch.stl")
a = math.radians(15)
def sunk(h):
    k = s.copy(); k.apply_translation([0, h * math.sin(a), -h * math.cos(a)]); return c.bounded_depth(5.0, p, k)
d0, d1, d5 = c.bounded_depth(5.0, p, s), sunk(0.1), sunk(0.5)   # 5.0 = what FCL reported
print("contact", d0, "sunk 0.1 mm", d1, "sunk 0.5 mm", d5)
# P28 (2026-11-28): a 0.1 mm sink read 1.5 mm (oriented box of slab + zero-volume side sheets); now exact
sys.exit(0 if d0 <= 0.05 and abs(d1 - 0.1) <= 0.02 and abs(d5 - 0.5) <= 0.05 else 1)
PY
