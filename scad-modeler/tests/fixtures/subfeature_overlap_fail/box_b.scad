// Sub-module B, solo export. Deliberately overlapping A: spans x 10..30, so
// x 10..20 is shared with A -- a 10x20x20 = 4000mm3 unintended overlap between
// two features that both live inside one part's union().

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [20, 20, 20]
translate([10, 0, 0]) cube([20, 20, 20]);
