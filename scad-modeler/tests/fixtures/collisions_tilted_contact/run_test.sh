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
k = s.copy(); a = math.radians(15); k.apply_translation([0, 0.5 * math.sin(a), -0.5 * math.cos(a)])
d0, d1 = c.bounded_depth(5.0, p, s), c.bounded_depth(5.0, p, k)   # 5.0 = what FCL reported
print("contact", d0, "sunk 0.5 mm", d1)
sys.exit(0 if d0 <= 0.05 and d1 >= 0.4 else 1)
PY
