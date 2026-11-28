#!/usr/bin/env bash
# Audits A9 + A10 (2026-11-28). A9: an exemption ["seat", "tower"] matched the PART prefix of
# motor_tower__cradle.stl (validate_scad.sh names solo renders <part>__<subfeature>.stl) and hid a 500 mm3
# overlap; names are now the exact sub-feature names. A10: a declared SUBFEATURE whose solo render is empty
# (typo in the dispatch) was only a stderr warning, and the remaining two passed the run.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; cd "$t"
echo 'cube(10);' > a.scad; echo 'translate([5,0,0]) cube(10);' > b.scad
"$OPENSCAD" --backend=Manifold -o motor_tower__cradle.stl a.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold -o motor_tower__bearing_seat.stl b.scad >/dev/null 2>&1
echo '[{"pair": ["seat", "tower"], "reason": "seat blends into tower"}]' > wrong.json
echo '[{"pair": ["bearing_seat", "cradle"], "reason": "seat blends into cradle"}]' > right.json
fail=0
python3 "$SCAD_MODELER_SCRIPTS/check_subfeature_overlap.py" --exempt wrong.json motor_tower__cradle.stl motor_tower__bearing_seat.stl >o 2>&1; r=$?
[ $r -eq 3 ] || { echo "A9: substring exemption hid the overlap (rc $r): $(cat o)"; fail=1; }
python3 "$SCAD_MODELER_SCRIPTS/check_subfeature_overlap.py" --exempt right.json motor_tower__cradle.stl motor_tower__bearing_seat.stl >o 2>&1; r=$?
[ $r -eq 0 ] || { echo "A9: exact exemption not honoured (rc $r): $(cat o)"; fail=1; }
mkdir parts; printf '%s\n' '$fa = 2; $fs = 0.3;' > params.scad
cat > parts/p.scad <<'S'
// SUBFEATURES: tower, cradle, boss
// EXPECTED_BBOX: [40, 10, 10]
// EXPECTED_THROUGH_HOLES: 0
SUBFEATURE = is_undef(SUBFEATURE) ? "" : SUBFEATURE;
module tower() cube([10,10,10]);
module cradle() translate([15,0,0]) cube([25,10,10]);
module boss() translate([5,0,0]) cube([10,10,10]);
if (SUBFEATURE=="tower") tower(); else if (SUBFEATURE=="cradle") cradle();
else if (SUBFEATURE=="bosss") boss(); else if (SUBFEATURE=="") union(){tower();cradle();boss();}
S
o=$(bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all 2>&1); r=$?
[ $r -ne 0 ] && grep -q "CHECK_RESULT subfeature_overlap=FAIL" <<< "$o" && grep -q "sub-feature 'boss' rendered nothing" <<< "$o" \
    || { echo "A10: missing sub-feature passed (rc $r): $(grep -i subfeature <<< "$o")"; fail=1; }
exit $fail
