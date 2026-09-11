// Proves check_features.py catches the inscribed-polygon failure it exists for:
// a hole that is correct across CORNERS but undersized ACROSS FLATS, because
// OpenSCAD built the circle as a coarse polygon with its vertices on the ideal
// circle. A bounding-box check cannot see this, and a render looks fine.
//
// Declared target is Ø8. At $fn=8 the across-flats size is 8*cos(180/8) =
// 7.39mm -- 0.61mm under target, well past the 0.05mm default tolerance.

$fn = 8;

// EXPECTED_BBOX: [30, 30, 6]
// EXPECTED_HOLE: [15, 15, 0, "Z", 8.0]

difference() {
    translate([0, 0, 0]) cube([30, 30, 6]);
    translate([15, 15, -1]) cylinder(d = 8, h = 8);
}
