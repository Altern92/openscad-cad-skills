// Shared helpers for parts in the shell frame (origin: footprint centre, z = 0 on the base top).
include <params.scad>

// Plate frame: x across, y along the slope from the front edge, z = plate normal (0 = plate top).
module plate_frame() translate([0, -gf_w / 2, h_front]) rotate([tilt, 0, 0]) children();
function key_xy(i, j) = [(i - (key_cols - 1) / 2) * key_pitch, key_s0 + (j + 0.5) * key_pitch];
module rrect(w, h, r) linear_extrude(h) offset(r) square(w - 2 * r, center = true);
