#!/usr/bin/env bash
# P5 (2026-11-01): the numbers the user approved live in acceptance.json, locked by
# sha256; a part may not declare anything else, and the file may not change unapproved.
set -uo pipefail
A="$SCAD_MODELER_SCRIPTS/acceptance.py"; V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
P="$tmp/p"; mkdir -p "$P/parts"
printf '{"parts": {"plate": {"bbox": [20, 10, 5], "through_holes": 0}}}\n' > "$P/acceptance.json"
part() { printf '// EXPECTED_BBOX: %s\n// EXPECTED_THROUGH_HOLES: %s\ncube([20,10,5]);\n' "$1" "$2" > "$P/parts/plate.scad"; }
part '[20, 10, 5]' 0
res() { (cd "$P" && bash "$V" --all 2>&1); }

# AC-1
out=$(cd "$P" && python3 "$A" approve 2>&1); [ $? -eq 4 ] || die "AC-1: no quote not exit 4"
out=$(cd "$P" && python3 "$A" approve --quote "  " 2>&1); [ $? -eq 4 ] || die "AC-1: blank quote not exit 4"
[ ! -f "$P/acceptance.lock" ] || die "AC-1: lock written without a quote"
# AC-3
out=$(res); echo "$out" | grep -q '^CHECK_RESULT acceptance=FAIL' || die "AC-3: unapproved not FAIL"
echo "$out" | grep -qi 'not approved' || die "AC-3: reason missing"
# AC-2
out=$(cd "$P" && python3 "$A" approve --quote "taip, tinka" 2>&1) || die "AC-2: approve failed"
grep -q '"quote": "taip, tinka"' "$P/acceptance.lock" || die "AC-2: quote not in lock"
want=$(shasum -a 256 "$P/acceptance.json" | cut -d' ' -f1); grep -q "$want" "$P/acceptance.lock" || die "AC-2: sha"
# AC-7
out=$(res); echo "$out" | grep -q '^CHECK_RESULT acceptance=PASS' || die "AC-7: matching not PASS"
# AC-5 weakened declaration
part '[20, 10, 3]' 0; out=$(res)
echo "$out" | grep -q '^CHECK_RESULT acceptance=FAIL' || die "AC-5: changed bbox not FAIL"
echo "$out" | grep -q 'plate' && echo "$out" | grep -q '20, 10, 5' || die "AC-5: message lacks part/values"
printf '// NO_BBOX: whatever\n// EXPECTED_THROUGH_HOLES: 0\ncube([20,10,5]);\n' > "$P/parts/plate.scad"; out=$(res)
echo "$out" | grep -q '^CHECK_RESULT acceptance=FAIL' || die "AC-5: NO_BBOX escape accepted"
part '[20, 10, 5]' 1; out=$(res)
echo "$out" | grep -q '^CHECK_RESULT acceptance=FAIL' || die "AC-5: changed through_holes not FAIL"
part '[20, 10, 5]' 0
# AC-4
printf '{"parts": {"plate": {"bbox": [20, 10, 3], "through_holes": 0}}}\n' > "$P/acceptance.json"; out=$(res)
echo "$out" | grep -q '^CHECK_RESULT acceptance=FAIL' || die "AC-4: edited spec not FAIL"
echo "$out" | grep -qi 'changed after approval' || die "AC-4: reason missing"
# AC-6
printf '{"parts": {"plate": {"bbox": [20, 10, 5], "through_holes": 0}, "lid": {"bbox": [1,1,1], "through_holes": 0}}}\n' > "$P/acceptance.json"
(cd "$P" && python3 "$A" approve --quote "taip" >/dev/null) ; out=$(res)
echo "$out" | grep -q '^CHECK_RESULT acceptance=FAIL' || die "AC-6: missing part not FAIL"
echo "$out" | grep -q 'lid' || die "AC-6: missing part not named"
# AC-8
out=$(cd "$P" && python3 "$A" emit 2>&1)
echo "$out" | grep -q '^// EXPECTED_BBOX: \[20, 10, 5\]' && echo "$out" | grep -q '^// EXPECTED_THROUGH_HOLES: 0' || die "AC-8: emit"
# AC-7 no acceptance.json -> SKIP
rm "$P/acceptance.json" "$P/acceptance.lock"; out=$(res)
echo "$out" | grep -q '^CHECK_RESULT acceptance=SKIP' || die "AC-7: absent not SKIP"
exit 0
