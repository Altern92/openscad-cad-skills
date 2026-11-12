// 3 mm cover panel on the +Y face, mounted after the screw: HEAD_HOLE=false reproduces INC-2026-11-08-01
HEAD_HOLE = is_undef(HEAD_HOLE) ? false : HEAD_HOLE;
difference() {
    translate([-20, 20, 0]) cube([40, 3, 20]);
    if (HEAD_HOLE) translate([0, 24, 5]) rotate([90, 0, 0]) cylinder(d = 8.5, h = 5, $fn = 32);
}
