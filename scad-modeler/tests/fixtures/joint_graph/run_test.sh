#!/usr/bin/env bash
# P4 (2026-11-01): D class, 13 incidents -- a part shipped with nothing holding it to the
# rest (side panels with no fastening passed connectivity and dimensions). Every printable
# part of a multi-part project needs >= 1 joint: a joints.json contact or an
# attachments.json entry (part or "to"), or `// NO_JOINT: <reason>`.
set -uo pipefail
J="$SCAD_MODELER_SCRIPTS/check_joint_graph.py"; V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
P="$tmp/p"; mkdir -p "$P/parts"
for n in a b c; do printf '// EXPECTED_BBOX: [5, 5, 5]\n// EXPECTED_THROUGH_HOLES: 0\ncube(5);\n' > "$P/parts/$n.scad"; done
printf '// PREVIEW_FILE: variants side by side\ncube(1);\n' > "$P/parts/preview_x.scad"
printf '{"contacts": [{"pair": ["a", "b"], "joint_type": "bolted"}]}\n' > "$P/joints.json"
printf '[{"name": "c_to_a", "part": "c", "to": "a", "at": [2,2,2], "feature": "m3"}]\n' > "$P/attachments.json"
j() { (cd "$P" && python3 "$J" --project-dir . 2>&1); }

out=$(j); [ $? -eq 0 ] || die "all joined: not PASS"
rm "$P/attachments.json"; out=$(j); rc=$?
[ "$rc" -eq 3 ] || die "c unjoined: exit $rc, want 3"
echo "$out" | grep -q 'parts/c.scad' || die "c not named"
echo "$out" | grep -q 'preview_x' && die "PREVIEW_FILE part counted"
sed -i '' '1i\
// NO_JOINT: loose tray, sits in the drawer
' "$P/parts/c.scad"; out=$(j); [ $? -eq 0 ] || die "NO_JOINT with reason not accepted"
sed -i '' 's#^// NO_JOINT: .*#// NO_JOINT:#' "$P/parts/c.scad"; out=$(j); [ $? -eq 3 ] || die "empty NO_JOINT reason accepted"
sed -i '' '/^\/\/ NO_JOINT:/d' "$P/parts/c.scad"
rm "$P/joints.json"; out=$(j); [ $? -eq 3 ] || die "no joint files: not FAIL"
out=$(cd "$P" && bash "$V" --all 2>&1)
echo "$out" | grep -q '^CHECK_RESULT joints=FAIL' || die "validate: no joints=FAIL"
rm "$P/parts/b.scad" "$P/parts/c.scad"; out=$(j); rc=$?
[ "$rc" -eq 0 ] && echo "$out" | grep -q '^SKIP' || die "single part: not SKIP"
exit 0
