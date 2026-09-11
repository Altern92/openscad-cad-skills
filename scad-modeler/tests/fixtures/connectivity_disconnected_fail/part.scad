// Reproduction of INCIDENTS.md 2026-08-19 (gearbox_frame): a fix for one
// collision widened the bearing tower's support legs from 7mm to 15mm radius.
// That solved the collision, but the legs at their NEW radius no longer
// touched the bearing disc (9mm radius) they were supposed to hold up --
// a permanent 3mm gap, two disconnected solids in one STL that still had a
// correct overall bounding box.
//
// Deliberately NO "// EXPECTED_BODIES:" declaration: the point of this
// fixture is that a single printed part silently splitting in two is an
// error by DEFAULT, with no declaration needed.

$fa = 2; $fs = 0.3;

// the bearing disc
translate([0, 0, 0]) cylinder(r = 9, h = 4);

// the support legs, at a radius that no longer reaches the disc
for (a = [0 : 90 : 270])
    rotate([0, 0, a]) translate([12, 0, 0]) cylinder(r = 2, h = 4);
// gap between disc edge (r=9) and legs' inner edge (r=10) -> disconnected
