// PURCHASED (vitamin): 30 Cherry-MX compatible switches -- envelopes (top housing, bottom housing, centre post).
// Local origin: shell frame. Not printed.
// EXPECTED_BBOX: [110.85, 90.902, 36.651]   // hand-computed from the plate frame (calculations.md)
// NO_THROUGH_HOLES_CHECK: purchased envelopes, solid by construction
// EXPECTED_BODIES: 30
// NO_RETENTION: each switch snaps into the plate with its own clips
include <../shell_frame.scad>

module vit_switches() color("dimgray")
    for (i = [0 : key_cols - 1], j = [0 : key_rows - 1]) plate_frame() translate(key_xy(i, j)) {
        translate([-mx_top_housing / 2, -mx_top_housing / 2, 0]) cube([mx_top_housing, mx_top_housing, mx_top_h]);
        translate([-mx_body / 2, -mx_body / 2, -mx_body_h]) cube([mx_body, mx_body, mx_body_h]);
        translate([0, 0, -mx_body_h - mx_pin_h]) cylinder(d = mx_post_d, h = mx_pin_h);
    }
vit_switches();
