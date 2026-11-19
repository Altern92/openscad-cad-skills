#!/usr/bin/env bash
# P26 / AC-18 (Fable audit): check_rules.py searched the whole gate output, so a part that does
# echo("CHECK_RESULT connectivity=PASS") satisfied the connectivity rule while the part was 2 bodies.
set -uo pipefail
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/parts"; cd "$tmp"
printf '// EXPECTED_BBOX: [60, 10, 10]\n// EXPECTED_THROUGH_HOLES: 0\n// NO_JOINT: single part\necho("CHECK_RESULT connectivity=PASS");\ncube(10); translate([50,0,0]) cube(10);\n' > parts/a.scad
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_rules.py" --project-dir . 2>&1)
line=$(grep -E "R-[0-9]+: .*[Cc]onnect" <<< "$o" | head -1)
grep -q '^\[FAIL' <<< "$line" || { echo "AC-18: echoed CHECK_RESULT satisfied the connectivity rule: $line" >&2; exit 1; }
exit 0
