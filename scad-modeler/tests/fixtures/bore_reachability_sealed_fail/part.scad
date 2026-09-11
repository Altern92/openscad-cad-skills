// Direct reproduction of INCIDENTS.md 2026-08-19 ("bearing bores never reached
// the tower's true exterior surface"): a bearing tower whose bore measures the
// right diameter (check_features.py is happy) and which is one connected
// watertight solid (check_connectivity.py is happy) -- but the bore never
// reaches the exterior, so nothing can be inserted.
//
// The pocket is drilled from the +X face and stops 4mm short of the -X face:
// the declared path from outside to the seat runs through solid material.

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [20, 20, 30]

difference() {
    cube([20, 20, 30]);
    // pocket spans x = 4 .. 24 -- enters through +X, stops inside
    translate([14, 10, 10]) rotate([0, 90, 0]) cylinder(d = 8, h = 20, center = true);
}
