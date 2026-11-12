// 40x40x20 block the screws thread into; M4 pilots d3.3 from +Y face at z5 (x0) and a second along X at z5 (fail fixture) -- pass fixture screws the side one at z15
difference() {
    translate([-20, -20, 0]) cube([40, 40, 20]);
    translate([0, 21, 5]) rotate([90, 0, 0]) cylinder(d = 3.3, h = 26, $fn = 32);
    translate([21, 0, 15]) rotate([0, -90, 0]) cylinder(d = 3.3, h = 26, $fn = 32);
}
