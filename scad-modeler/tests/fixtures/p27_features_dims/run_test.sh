#!/usr/bin/env bash
# P27 (Fable calculation audit): AC-17 a solid pin is not a hole (check_features), AC-18 the tessellation
# bound excuses only a SHORTER extent (check_dimensions)
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"
fail=0
cat > pin.scad <<'S'
// EXPECTED_HOLE: [10, 0, 10, "Z", 8]
$fn = 48;
cube([60, 30, 4], center = true);
translate([10, 0, 0]) cylinder(d = 8, h = 15);      // SOLID pin where the hole is declared
translate([-15, 0, 0]) cylinder(d = 20, h = 15);    // a bigger boss in the same slice
S
sed -e 's/cylinder(d = 8, h = 15);      \/\/ SOLID pin where the hole is declared/difference() { cylinder(d = 14, h = 15); translate([0, 0, -1]) cylinder(d = 8, h = 17); }/' pin.scad > bore.scad
for f in pin bore; do "$OPENSCAD" --backend=Manifold -o $f.stl $f.scad >/dev/null 2>&1; done
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_features.py" --stl pin.stl --scad pin.scad 2>&1); r=$?
[ $r -ne 0 ] || { echo "AC-17: solid pin passed as a hole: $o" >&2; fail=1; }
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_features.py" --stl bore.stl --scad bore.scad 2>&1); r=$?
[ $r -eq 0 ] || { echo "AC-17 baseline: a real Ø8 bore in a boss failed: $o" >&2; fail=1; }
for fn in 6 0; do
    printf '// EXPECTED_BBOX: [200, 100, 10]\n$fn = %s;\ncube([203, 100, 10]);\n' $fn > long$fn.scad
    "$OPENSCAD" --backend=Manifold -o long$fn.stl long$fn.scad >/dev/null 2>&1
    o=$(python3 "$SCAD_MODELER_SCRIPTS/check_dimensions.py" --stl long$fn.stl --scad long$fn.scad 2>&1); r=$?
    [ $r -ne 0 ] || { echo "AC-18: 203 mm passed as 200 at \$fn=$fn: $o" >&2; fail=1; }
done
printf '// EXPECTED_BBOX: [20, 20, 5]\n$fn = 6;\ncylinder(d = 20, h = 5);\n' > hex.scad
"$OPENSCAD" --backend=Manifold -o hex.stl hex.scad >/dev/null 2>&1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_dimensions.py" --stl hex.stl --scad hex.scad 2>&1); r=$?
[ $r -eq 0 ] || { echo "AC-18 baseline: a \$fn=6 cylinder (inscribed, shorter in Y) failed: $o" >&2; fail=1; }
exit $fail
