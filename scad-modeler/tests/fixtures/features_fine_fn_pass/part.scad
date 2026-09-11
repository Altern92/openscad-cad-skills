// The correct version of features_coarse_fn_fail: same Ø8 hole, fine enough
// segments that the across-flats deficit is negligible.

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [30, 30, 6]
// EXPECTED_HOLE: [15, 15, 0, "Z", 8.0]

difference() {
    translate([0, 0, 0]) cube([30, 30, 6]);
    translate([15, 15, -1]) cylinder(d = 8, h = 8);
}
