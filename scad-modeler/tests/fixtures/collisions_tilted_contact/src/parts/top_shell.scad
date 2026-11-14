// top_shell: 15 deg wedge with the MX plate as its top face, 4 corner columns for M3 heat-set inserts.
// Local origin: footprint centre, z = 0 = bottom rim (sits on the base top).
// Print orientation: plate face down on the bed (slicer "place on face"); no supports.
// EXPECTED_BBOX: [125.5, 125.5, 49.627]
// EXPECTED_THROUGH_HOLES: 31   // 30 switch cutouts + USB cable cut-out in the back wall
// EXPECTED_HOLE: [55, 55, 0, "Z", 4.0]
// SENSITIVE_TO: wall
include <../shell_frame.scad>

module top_shell() {
    difference() {
        intersection() {
            union() {
                difference() {
                    rrect(gf_w, 100, gf_corner_r);
                    translate([0, 0, -1]) rrect(2 * inner_half, 102, gf_corner_r - wall);
                }
                plate_frame() translate([-gf_w / 2 - 10, -10, -plate_t]) cube([gf_w + 20, slope_len + 20, plate_t]);
                for (sx = [-1, 1], sy = [-1, 1]) translate([sx * col_xy, sy * col_xy, 0]) cylinder(d = col_d, h = 100);
            }
            rrect(gf_w, 100, gf_corner_r);
            plate_frame() translate([-gf_w, -50, -300]) cube([2 * gf_w, 2 * slope_len, 300]);
        }
        for (i = [0 : key_cols - 1], j = [0 : key_rows - 1]) plate_frame() translate(key_xy(i, j)) {
            cube([mx_cut, mx_cut, 20], center = true);                       // through cut
            translate([-mx_pocket / 2, -mx_pocket / 2, -plate_t - 1]) cube([mx_pocket, mx_pocket, plate_t - mx_lip + 1]);  // clip pocket
        }
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * col_xy, sy * col_xy, -0.01]) cylinder(d = insert_d, h = insert_hole_depth);
        translate([-usb_cut_w / 2, inner_half - 1, usb_z - usb_cut_h / 2]) cube([usb_cut_w, wall + 2, usb_cut_h]);
    }
}
top_shell();
