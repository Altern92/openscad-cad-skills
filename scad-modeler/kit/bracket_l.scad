// kit/bracket_l.scad — L-shaped bracket (P1).
//
// Local origin: bottom face centre. bbox = [w, d, h].
// Horizontal plate: w×d×t, z ∈ [0, t].
// Vertical plate: w×t×h, at the back (y ∈ [d/2 - t, d/2]).
// 2 through-holes are declared — both in the horizontal plate.

include <lib.scad>

module kit_bracket_l(w, d, h, t, hole) {
    hole_d = kit_hole_d(hole);
    wall_min = 2.0;
    min_side = kit_min2(w, d);
    // ONE through-hole in EACH flange (as real requests ask:
    // "with a hole in both flanges").
    //   horizontal: axis Z, centre (0, hole_y)
    //   vertical:   axis Y, centre (0, h - hole_inset)
    hole_inset = hole_d / 2 + wall_min;
    hole_y = -d / 2 + hole_inset;
    hole_vz = h - hole_inset;

    assert(hole_d > 0,
        str("ERROR: hole ", hole, " unknown designation → use M3, M4, M5, M6 or Ø mm → change hole"));
    assert(t >= 2.5,
        str("ERROR: L bracket thickness ", kit_fmt(t), " mm → ", kit_fmt(t),
            " < ", kit_fmt(2.5), " mm → will not carry the load; increase t to ", kit_fmt(2.5)));
    assert(h > t + 2,
        str("ERROR: vertical part ", kit_fmt(h), " mm → ", kit_fmt(h), " ≤ ",
            kit_fmt(t + 2), " mm → too low for ", kit_fmt(t), " mm thickness; increase h to ",
            kit_fmt(t + 2)));
    assert(hole_d + 2 * wall_min <= min_side,
        str("ERROR: hole Ø", kit_fmt(hole_d), " does not fit ", kit_fmt(w), "×", kit_fmt(d),
            " with ", kit_fmt(wall_min), " mm wall → ", kit_fmt(hole_d + 2 * wall_min),
            " > ", kit_fmt(min_side), " → enlarge the bracket or reduce hole"));
    assert(hole_vz - hole_d / 2 >= t + wall_min,
        str("ERROR: vertical flange hole Ø", kit_fmt(hole_d), " does not fit h=",
            kit_fmt(h), " → need h ≥ ", kit_fmt(t + wall_min + hole_d / 2 + hole_inset),
            " → increase h or reduce hole"));

    difference() {
        union() {
            // Horizontal plate.
            kit_round_block(w, d, t, 0);
            // Vertical plate at the back.
            translate([0, d / 2 - t / 2, h / 2])
                cube([w, t, h], center = true);
        }
        // Horizontal flange: through-hole along Z.
        translate([0, hole_y, -1])
            cylinder(h = t + 2, d = hole_d, $fn = 64);
        // Vertical flange: through-hole along Y.
        translate([0, d / 2 - t - 1, hole_vz])
            rotate([-90, 0, 0])
                cylinder(h = t + 2, d = hole_d, $fn = 64);
    }
}

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_bracket_l(w, d, h, t, hole) = [w, d, h];

function kit_through_holes_bracket_l() = 2;
