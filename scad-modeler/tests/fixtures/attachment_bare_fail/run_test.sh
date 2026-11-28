#!/usr/bin/env bash
# Audit A8 (2026-11-28): the INC-2026-09-11 bare side panel (3 x 229.7 x 200, no boss, hole or flange) passed,
# because a point inside a plain slab is "material". A part that is nothing but its bounding box carries no
# attachment feature -> FAIL. And "part" is now an exact name: "lid" no longer checks lid_hinge.stl.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; cd "$t"
echo 'cube([3, 229.7, 200]);' > side_panel.scad
echo 'cube([10, 10, 10]); translate([10, 4, 4]) cube([4, 2, 2]);' > lid_hinge.scad
for f in side_panel lid_hinge; do "$OPENSCAD" --backend=Manifold --render -o $f.stl $f.scad >/dev/null 2>&1 || { echo "render $f failed"; exit 1; }; done
echo '[{"name": "side_panel_to_post_front", "part": "side_panel", "at": [1.5, 225, 100], "feature": "m3_boss", "min_material_mm": 4.0}]' > a.json
echo '[{"name": "lid_pin", "part": "lid", "at": [5, 5, 5], "feature": "hinge"}]' > b.json
fail=0
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_attachment.py" --attachments a.json side_panel.stl 2>&1); r=$?
[ $r -eq 3 ] && grep -q "side_panel.stl is a bare block" <<< "$o" || { echo "bare panel passed (rc $r): $o"; fail=1; }
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_attachment.py" --attachments b.json lid_hinge.stl 2>&1); r=$?
[ $r -eq 4 ] || { echo "part 'lid' matched lid_hinge.stl (rc $r): $o"; fail=1; }
exit $fail
