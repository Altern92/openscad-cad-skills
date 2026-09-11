// Same geometry shape as connectivity_disconnected_fail, but here the
// multi-shell result is DELIBERATE and declared -- the escape hatch that
// keeps the default-on check from being wrong for a legitimately
// multi-solid part (e.g. a printed-in-place hinge pin shipped in one STL).

$fa = 2; $fs = 0.3;

// EXPECTED_BODIES: 2

translate([0, 0, 0]) cylinder(r = 9, h = 4);
translate([30, 0, 0]) cylinder(r = 9, h = 4);
