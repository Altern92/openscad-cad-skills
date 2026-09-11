// The correct version of attachment_missing_fail: the M3 boss the fastener
// goes through is actually modelled at the declared attachment point.

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [9, 60, 40]

// the panel itself: thin plate at x=0
cube([3, 60, 40], center = true);

// the M3 boss, standing 6mm off the panel face at the declared point
translate([4.5, 20, 15]) rotate([0, 90, 0]) cylinder(d = 8, h = 6, center = true);
