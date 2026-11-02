// Proves check_features.py catches a hole whose diameter AND centre shifted
// together (inset = d/2 + wall_min): the distance from the OLD axis point to
// the NEAR wall stays d_old/2 = 2.75 mm even when an M5 (5.5) hole is replaced
// by M6 (6.6) shifted by +0.55 mm. Measuring only poly.exterior.distance(probe)
// passed this (audit 2026-11-02 §5 #3, found by geom_mutation.py on bracket_l).

$fn = 64;

// EXPECTED_BBOX: [30, 30, 6]
// EXPECTED_HOLE: [0, -10.25, 3, "Z", 5.5]

// Bug: M6 (6.6 mm) at y = -15 + 6.6/2 + 2 = -9.70 instead of M5 (5.5 mm) at -10.25.
difference() {
    translate([-15, -15, 0]) cube([30, 30, 6]);
    translate([0, -9.70, -1]) cylinder(d = 6.6, h = 8);
}

