#!/usr/bin/env bash
# INC-2026-11-07-01: a divider shelf had flush-seam contacts with four panels in joints.json, so the
# joint graph passed, yet nothing held it up (its screw holes sat over empty space). A contact only says
# two parts touch. Every part must declare what RETAINS it: attachments.json "part" (not just "to"),
# `// NO_RETENTION: <reason>`, or `// NO_JOINT: <reason>`.
set -uo pipefail
J="$SCAD_MODELER_SCRIPTS/check_joint_graph.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
P="$tmp/p"; mkdir -p "$P/parts"
for n in shelf panel; do printf '// EXPECTED_BBOX: [5, 5, 5]\n// EXPECTED_THROUGH_HOLES: 0\ncube(5);\n' > "$P/parts/$n.scad"; done
printf '{"contacts": [{"pair": ["shelf", "panel"], "joint_type": "flush_design_seam"}]}\n' > "$P/joints.json"
j() { (cd "$P" && python3 "$J" --project-dir . 2>&1); }

out=$(j); rc=$?
[ "$rc" -eq 3 ] || die "contact-only parts passed: exit $rc, want 3 (the incident)"
echo "$out" | grep -q 'FAIL: retention, parts/shelf.scad' || die "shelf retention gap not named"
echo "$out" | grep -q 'joined to nothing' && die "contact-joined part reported as unjoined"
printf '[{"name": "shelf_screw", "part": "shelf", "to": "panel", "at": [2,2,2], "feature": "m3 land"}]\n' > "$P/attachments.json"
out=$(j); rc=$?
[ "$rc" -eq 3 ] || die "panel only the \"to\" side, yet passed"
echo "$out" | grep -q 'parts/shelf.scad' && die "shelf has an attachment but still flagged"
echo "$out" | grep -q 'FAIL: retention, parts/panel.scad' || die "panel retention gap not named"
sed -i '' '1i\
// NO_RETENTION: screwed to the frame, frame not modelled here
' "$P/parts/panel.scad"; out=$(j); [ $? -eq 0 ] || die "NO_RETENTION with reason not accepted"
sed -i '' 's#^// NO_RETENTION: .*#// NO_RETENTION:#' "$P/parts/panel.scad"; out=$(j); [ $? -eq 3 ] || die "empty NO_RETENTION reason accepted"
sed -i '' 's#^// NO_RETENTION:#// NO_JOINT: clips onto a purchased rail#' "$P/parts/panel.scad"; out=$(j); [ $? -eq 0 ] || die "NO_JOINT reason not accepted as retention"
exit 0
