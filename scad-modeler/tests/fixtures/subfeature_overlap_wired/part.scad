// Two named sub-features sharing one union(), written to overlap on purpose.
// The union() of two overlapping solids is still ONE valid watertight
// single-body shell, so check_connectivity.py and check_dimensions.py both
// stay clean while 180mm3 of material sits where it should not.
//
// SUBFEATURES: tower_main, motor_cradle

$fa = 2; $fs = 0.3;

part_height = 15;

module tower_main() {
    cuboid([10, 10, part_height]);
}

module motor_cradle() {
    translate([0, 0, part_height / 2]) cuboid([14, 6, 6]);
}

module part_geometry() {
    union() {
        tower_main();
        motor_cradle();
    }
}

// Same guarded switch as templates/part_template.scad -- without is_undef,
// -D 'SUBFEATURE="x"' is reassigned by this file and every solo render comes
// out as the whole part, which would make the overlap check compare the part
// against itself.
SUBFEATURE = is_undef(SUBFEATURE) ? "" : SUBFEATURE;

module subfeature_by_name(name) {
    if (name == "tower_main") tower_main();
    else if (name == "motor_cradle") motor_cradle();
    else assert(false, str("Unknown sub-feature '", name, "'"));
}

if (SUBFEATURE != "") subfeature_by_name(SUBFEATURE);
else part_geometry();

module cuboid(s) { cube(s, center = false); }
