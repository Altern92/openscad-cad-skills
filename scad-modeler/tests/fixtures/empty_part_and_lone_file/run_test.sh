#!/usr/bin/env bash
# P26 / AC-5, AC-6 (Fable audit e7, e10). A part that defined a module but called nothing was taken for a
# library and skipped, so --all passed with no part at all; a lone file printed connectivity=PASS without
# running the check. Now an empty render is a FAIL unless the file says // LIBRARY_FILE: <reason>, and the
# lone-file path runs connectivity.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
fail=0
res() { grep -o "CHECK_RESULT $1=[A-Z]*" <<< "$2" | head -1; }
mkdir -p "$tmp/p/parts"; cd "$tmp/p"
printf '// EXPECTED_BBOX: [60, 10, 10]\n// EXPECTED_THROUGH_HOLES: 0\nmodule a(){ cube(10); translate([50,0,0]) cube(10); }\n' > parts/a.scad
out=$(bash "$V" --all 2>&1); rc=$?
[ $rc -ne 0 ] && [ "$(res render "$out")" = "CHECK_RESULT render=FAIL" ] && grep -q <<< "$out" "renders nothing" \
    || { echo "AC-5: part with no top-level call passed (rc=$rc): $(grep CHECK_RESULT <<< "$out" | head -3)" >&2; fail=1; }
printf '// LIBRARY_FILE: shared helpers\nmodule a(){ cube(10); }\n' > parts/a.scad
printf '// EXPECTED_BBOX: [10, 10, 10]\n// EXPECTED_THROUGH_HOLES: 0\n// NO_JOINT: single part\ncube(10);\n' > parts/b.scad
out=$(bash "$V" --all 2>&1)
[ "$(res render "$out")" = "CHECK_RESULT render=PASS" ] \
    || { echo "AC-5: declared library not skipped: $(grep -E 'CHECK_RESULT render|renders' <<< "$out")" >&2; fail=1; }
cd "$tmp"; printf 'cube(10); translate([50,0,0]) cube(10);\n' > thing.scad
out=$(bash "$V" thing.scad 2>&1)
[ "$(res connectivity "$out")" = "CHECK_RESULT connectivity=FAIL" ] \
    || { echo "AC-6: lone file with 2 bodies: $(res connectivity "$out")" >&2; fail=1; }
printf 'cube(10);\n' > one.scad; out=$(bash "$V" one.scad 2>&1)
[ "$(res connectivity "$out")" = "CHECK_RESULT connectivity=PASS" ] \
    || { echo "AC-6: lone one-body file: $(res connectivity "$out")" >&2; fail=1; }
# AC-2 regression (2026-11-19): with no parts/*.scad the AC-2 grep got no file and read stdin, so a run whose
# stdin stayed open (deploy_to_canon.sh) hung for hours. Run with an open stdin and a 90 s limit.
H="$tmp/hang"; mkdir -p "$H/parts"; printf 'cube(1);\n' > "$H/assembly.scad"
( cd "$H" && bash "$V" --all < <(sleep 120) >/dev/null 2>&1 ) & hp=$!
for _ in $(seq 90); do kill -0 $hp 2>/dev/null || break; sleep 1; done
if kill -0 $hp 2>/dev/null; then
    pkill -P $hp 2>/dev/null; kill $hp 2>/dev/null; pkill -f "sleep 120" 2>/dev/null
    echo "AC-2: validate --all with no parts and an open stdin hung" >&2; fail=1
fi
exit $fail
