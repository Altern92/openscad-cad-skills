#!/usr/bin/env bash
# P32/P36 (wave 2): check_fits.py -- hole = peg + clearance, ISO 286 classes, untoleranced near-contacts.
# (a) clearance 0.2 PASS (b) hole 0.3 mm too small FAIL (c) H7/g6 in class PASS (d) out of class FAIL
# (e) undeclared 0.2 mm gap over 100 mm2 WARN, --strict FAIL (f) declared pair / far apart / no fits SKIP
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
C="$SCAD_MODELER_SCRIPTS/check_fits.py"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
mk() { mkdir -p "$t/$1/build/positioned"; python3 "$here/make_stls.py" "$t/$1/build/positioned" "${@:2}" || exit 1; }
fit() { echo "{\"contacts\": [{\"pair\": [\"peg\", \"plate\"], \"joint_type\": \"loose_fit\", \"fit\": {\"peg\": \"peg\", \"hole\": \"plate\", $1}}]}" > "$t/$2/joints.json"; }
mk clr 10.0 10.2;  fit '"clearance_mm": 0.2' clr
mk small 10.0 9.9; fit '"clearance_mm": 0.2' small
mk iso_ok 9.99 10.01;  fit '"iso286": "H7/g6", "nominal_mm": 10' iso_ok
mk iso_bad 9.99 10.05; fit '"iso286": "H7/g6", "nominal_mm": 10' iso_bad
mk iso_int 10.003 9.995; fit '"iso286": "H7/g6", "nominal_mm": 10' iso_int
mk iso_peg 9.97 10.01; fit '"iso286": "H7/g6", "nominal_mm": 10' iso_peg
out=$(python3 "$C" --project-dir "$t/clr" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^PASS: fits, 1 fit" <<< "$out" && grep -q "clearance 0.20" <<< "$out" || die "(a) clearance 0.2: expected PASS, rc=$rc"
out=$(python3 "$C" --project-dir "$t/small" 2>&1); rc=$?
[ $rc -eq 3 ] && grep -q "^FAIL: .*plate.*peg" <<< "$out" && grep -q "clearance -0.10" <<< "$out" || die "(b) hole 0.3 too small: expected FAIL exit 3, rc=$rc"
out=$(python3 "$C" --project-dir "$t/iso_ok" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^PASS: fits, 1 fit" <<< "$out" || die "(c) H7/g6 in class: expected PASS, rc=$rc"
out=$(python3 "$C" --project-dir "$t/iso_bad" 2>&1); rc=$?
[ $rc -eq 3 ] && grep -q "^FAIL: .*H7" <<< "$out" || die "(d) hole outside H7: expected FAIL, rc=$rc"
out=$(python3 "$C" --project-dir "$t/iso_peg" 2>&1); rc=$?
[ $rc -eq 3 ] && grep -q "^FAIL: .*g6" <<< "$out" || die "(d2) peg outside g6: expected FAIL, rc=$rc"
out=$(python3 "$C" --project-dir "$t/iso_int" 2>&1); rc=$?
[ $rc -eq 3 ] && grep -q "^FAIL: .*interference" <<< "$out" || die "(d3) peg 10.003 in hole 9.995 (H7/g6, each within meas-tol of its class): expected FAIL interference, rc=$rc"
# (e) near contact
mkdir -p "$t/near/build/positioned"; python3 "$here/make_stls.py" "$t/near/build/positioned" near 0.2
out=$(python3 "$C" --project-dir "$t/near" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^WARN: .*blk_a.*blk_b.*untoleranced" <<< "$out" && ! grep -q "^SKIP" <<< "$out" || die "(e) near contact: expected WARN exit 0, rc=$rc"
out=$(python3 "$C" --project-dir "$t/near" --strict 2>&1); rc=$?
[ $rc -eq 3 ] && grep -q "^FAIL: .*untoleranced" <<< "$out" || die "(e) --strict: expected FAIL exit 3, rc=$rc"
echo '{"contacts": [{"pair": ["blk_b", "blk_a"], "joint_type": "touch"}]}' > "$t/near/joints.json"
out=$(python3 "$C" --project-dir "$t/near" --strict 2>&1); rc=$?
[ $rc -eq 0 ] && ! grep -q "WARN" <<< "$out" || die "(f) declared pair must not WARN, rc=$rc"
rm "$t/near/joints.json"; rm -rf "$t/far"; mkdir -p "$t/far/build/positioned"; python3 "$here/make_stls.py" "$t/far/build/positioned" near 2.0
out=$(python3 "$C" --project-dir "$t/far" --strict 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^SKIP" <<< "$out" || die "(f) 2 mm gap, no fits: expected SKIP, rc=$rc"
mkdir "$t/none"; out=$(python3 "$C" --project-dir "$t/none" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^SKIP" <<< "$out" || die "(f) no positioned STLs: expected SKIP, rc=$rc"
fit '"clearance_mm": 0.2' none; echo '{"contacts": [{"pair": ["peg","nosuch"], "fit": {"peg": "peg", "hole": "nosuch", "clearance_mm": 0.2}}]}' > "$t/clr/joints.json"
python3 "$C" --project-dir "$t/clr" >/dev/null 2>&1; [ $? -eq 4 ] || die "unknown part name: expected exit 4"
# (g) AC-F1: mate() from patterns.scad renders a peg and its cutter that check_fits.py measures as the declared clearance
mkdir -p "$t/mate/build/positioned"; P="$here/../../../../openscad-cad/references/patterns.scad"
cat > "$t/mate/w.scad" <<SCAD
include <$P>
PIN_D = 10; PIN_CLEARANCE = 0.2;
if (MODE == "peg") mate(PIN_D, 20, PIN_CLEARANCE, removing = false);
else difference() { translate([-15, -15, 5]) cube([30, 30, 10]); translate([0, 0, 4]) mate(PIN_D, 12, PIN_CLEARANCE, removing = true); }
SCAD
for m in peg plate; do openscad -q -D "MODE=\"$m\"" -o "$t/mate/build/positioned/$m.stl" "$t/mate/w.scad" >/dev/null 2>&1 || die "(g) openscad failed on mate() $m"; done
echo '{"contacts": [{"pair": ["peg", "plate"], "fit": {"peg": "peg", "hole": "plate", "clearance_mm": 0.2}}]}' > "$t/mate/joints.json"
out=$(python3 "$C" --project-dir "$t/mate" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^PASS: fits, 1 fit" <<< "$out" || die "(g) mate(): expected PASS, rc=$rc"
# (h) every table cell up to 30 mm equals the printed textbook table
python3 "$here/book_table.py" "$C" | grep -q "^OK: 1[0-9][0-9] ISO 286 cells" || die "(h) ISO table differs from Bethune 2016"
exit 0
