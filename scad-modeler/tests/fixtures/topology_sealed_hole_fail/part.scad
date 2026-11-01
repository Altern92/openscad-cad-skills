// EXPECTED_THROUGH_HOLES: 2
// B class (16/95 incidents): a bore that looks right from above but is sealed
// by a 0.4 mm skin. Bbox, connectivity and printability all pass.
$fn = 48;
difference() {
    cube([40, 20, 5]);
    translate([10, 10, -1]) cylinder(d = 5, h = 7);
    translate([30, 10, -1]) cylinder(d = 5, h = 5.6);   // stops 0.4 below the top
}
