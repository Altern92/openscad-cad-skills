#!/usr/bin/env bash
# check_connectivity.py must NAME degenerate geometry, not just count bodies.
# A part can be one connected watertight body and still be full of sub-micron
# slivers, and a reader who only sees "OK: 1 connected body" will believe every
# other number reported about that part.
#
# The assertion is deliberately about the SHORTEST EDGE, not about a fixed
# count: the exact sliver count depends on the OpenSCAD/Manifold version, while
# "there is an edge far below any printable feature" is the durable fact.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_connectivity.py" --stl part.stl --scad part.scad 2>&1)
actual=$?
rm -f part.stl

# Still a PASS: one body is one body. Degenerate geometry is reported, not
# turned into a verdict the caller has to silence.
if [ "$actual" -ne 0 ]; then
    echo "expected exit 0 (the part is one connected body), got $actual" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -q "DEGENERATE GEOMETRY" || {
    echo "the degenerate sliver was not reported:" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q "shortest edge" || {
    echo "expected the note to quote the shortest edge:" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q "printability" || {
    echo "expected the note to say WHICH measurements this corrupts:" >&2
    echo "$out" >&2; exit 1; }

# A healthy mesh must stay silent -- otherwise the note is just noise on every
# part and stops being read.
cat > clean.scad <<'SCAD'
$fa = 2; $fs = 0.3;
difference() {
    cylinder(r = 10, h = 20, $fn = 180);
    translate([0, 0, 2]) cylinder(r = 8, h = 30, $fn = 180);
}
SCAD
"$OPENSCAD" --backend=Manifold --render -o clean.stl clean.scad >/dev/null 2>&1
clean_out=$(python3 "$SCAD_MODELER_SCRIPTS/check_connectivity.py" --stl clean.stl --scad clean.scad 2>&1)
rm -f clean.stl clean.scad
echo "$clean_out" | grep -q "DEGENERATE GEOMETRY" && {
    echo "a healthy mesh reported DEGENERATE GEOMETRY:" >&2
    echo "$clean_out" >&2
    exit 1
}
exit 0
