// The correct version of bore_reachability_sealed_fail: the bore passes all the
// way through the tower, so the declared path from outside to the seat is clear.

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [20, 20, 30]

difference() {
    cube([20, 20, 30]);
    // bore spans x = -20 .. 40 -- through both faces
    translate([10, 10, 10]) rotate([0, 90, 0]) cylinder(d = 8, h = 60, center = true);
}
