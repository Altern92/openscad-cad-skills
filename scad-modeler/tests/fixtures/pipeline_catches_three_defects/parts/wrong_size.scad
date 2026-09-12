// DEFECT 2 -- renders fine, looks right, is the wrong size.
// Catches a wrong -D override or a parameter that did not thread through.
include <../params.scad>
// EXPECTED_BBOX: [40, 20, 15]
cube([30, 20, 15], center = true);
