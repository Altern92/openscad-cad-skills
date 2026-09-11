// Sub-module B, clear of A -- no overlap between the two named features.

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [20, 20, 20]
translate([25, 0, 0]) cube([20, 20, 20]);
