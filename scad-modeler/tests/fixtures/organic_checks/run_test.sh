#!/usr/bin/env bash
# P6 (2026-11-01): openscad-organic had no numeric gate -- "render and look" only.
# PROPORTION lines (from the researched source, before modelling) check bbox ratios
# and slice widths; SILHOUETTE compares the projected outline with a reference image.
set -uo pipefail
PR="$SCAD_MODELER_SCRIPTS/check_proportions.py"; SI="$SCAD_MODELER_SCRIPTS/check_silhouette.py"
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
# a "figure": body 20 wide x 40 tall, head d=12 on top (total height 52)
fig='$fn=48; cylinder(d=20, h=40); translate([0,0,46]) sphere(d=12);'
w() { printf '%s\n%s\n' "$1" "$fig" > "$tmp/f.scad"; openscad -q -o "$tmp/f.stl" "$tmp/f.scad"; }

w '// PROPORTION: z/x = 2.6 +- 0.05
// PROPORTION: w_x@0.9 / x = 0.55 +- 0.1'
out=$(python3 "$PR" --scad "$tmp/f.scad" --stl "$tmp/f.stl" 2>&1) || die "true proportions failed"
w '// PROPORTION: z/x = 3.0 +- 0.1'
out=$(python3 "$PR" --scad "$tmp/f.scad" --stl "$tmp/f.stl" 2>&1); [ $? -eq 3 ] || die "wrong ratio not FAIL"
echo "$out" | grep -Eq 'measured 2\.(59|60)' || die "measured ratio not printed"
w '// PROPORTION: w_x@0.9 / x = 1.0 +- 0.1'
out=$(python3 "$PR" --scad "$tmp/f.scad" --stl "$tmp/f.stl" 2>&1); [ $? -eq 3 ] || die "wrong head width not FAIL"
w ''; out=$(python3 "$PR" --scad "$tmp/f.scad" --stl "$tmp/f.stl" 2>&1); [ $? -eq 0 ] && echo "$out" | grep -q '^SKIP' || die "undeclared not SKIP"

# reference silhouettes drawn independently with Pillow (front view = X horizontal, Z up)
python3 - "$tmp" <<'PY'
import sys
from PIL import Image, ImageDraw
t = sys.argv[1]
S = 10  # px per mm
im = Image.new("L", (20 * S, 52 * S), 255); d = ImageDraw.Draw(im)
d.rectangle([0, 12 * S, 20 * S - 1, 52 * S - 1], fill=0)          # body, z 0..40 (image y down)
d.ellipse([4 * S, 0, 16 * S - 1, 12 * S - 1], fill=0)              # head, z 40..52
im.save(f"{t}/ref_ok.png")
im = Image.new("L", (20 * S, 52 * S), 255); d = ImageDraw.Draw(im)
d.polygon([(10 * S, 0), (20 * S - 1, 52 * S - 1), (0, 52 * S - 1)], fill=0)  # a cone: wrong figure
im.save(f"{t}/ref_bad.png")
PY
w '// SILHOUETTE: front ref_ok.png >= 0.9'
out=$(python3 "$SI" --scad "$tmp/f.scad" --stl "$tmp/f.stl" 2>&1) || die "matching silhouette failed"
w '// SILHOUETTE: front ref_bad.png >= 0.9'
out=$(python3 "$SI" --scad "$tmp/f.scad" --stl "$tmp/f.stl" 2>&1); [ $? -eq 3 ] || die "wrong silhouette not FAIL"
echo "$out" | grep -q 'IoU' || die "IoU not printed"
# wired into validate_scad.sh single-file mode
printf '// EXPECTED_BBOX: [20, 20, 52]\n// EXPECTED_THROUGH_HOLES: 0\n// PROPORTION: z/x = 3.0 +- 0.1\n// SILHOUETTE: front ref_bad.png >= 0.9\n%s\n' "$fig" > "$tmp/g.scad"
out=$(cd "$tmp" && bash "$V" g.scad 2>&1)
echo "$out" | grep -q '^CHECK_RESULT proportions=FAIL' || die "validate: no proportions=FAIL"
echo "$out" | grep -q '^CHECK_RESULT silhouette=FAIL' || die "validate: no silhouette=FAIL"
exit 0
