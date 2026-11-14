// kit/box.scad — open-top box (enclosure body) (P1).
//
// Local origin: bottom face centre. bbox = [w, d, h].
// Walls `wall`, floor `floor`; top is open.
// `hole` ("" = no holes): 4 corner screw-boss bores,
// matched to `kit_lid(..., hole, inset)`.

include <lib.scad>

module kit_box(w, d, h, wall = 2.4, floor = 2.4, corner_r = 0,
               hole = "", inset = 0) {
    wall_min = 1.2;
    boss_wall = 2.0;
    min_side = kit_min2(w, d);
    has_holes = hole != "";
    hole_d = has_holes ? kit_hole_d(hole) : 0;
    boss_d = hole_d + 2 * boss_wall;

    assert(wall >= wall_min,
        str("ERROR: wall ", kit_fmt(wall), " mm → ", kit_fmt(wall), " < ",
            kit_fmt(wall_min), " mm (FDM minimum) → increase wall to ", kit_fmt(wall_min)));
    assert(2 * wall < w && 2 * wall < d,
        str("ERROR: walls ", kit_fmt(wall), "×2 do not fit ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(2 * wall), " ≥ ", kit_fmt(min_side),
            " → enlarge the box or reduce wall"));
    assert(floor >= wall_min && floor < h,
        str("ERROR: floor ", kit_fmt(floor), " mm → must be ", kit_fmt(wall_min),
            " ≤ floor < h=", kit_fmt(h), " → set floor between ", kit_fmt(wall_min),
            " and ", kit_fmt(h)));
    assert(corner_r >= 0 && corner_r * 2 < min_side,
        str("ERROR: corner_r ", kit_fmt(corner_r), " does not fit in ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(min_side),
            " → reduce corner_r"));
    assert(!has_holes || (hole_d >= 3.0 && hole_d <= 6.5),
        str("ERROR: hole ", hole, " = Ø", kit_fmt(hole_d), " mm → supported 3.0–6.5 mm → use M3..M6"));
    assert(!has_holes || inset >= hole_d / 2 + boss_wall,
        str("ERROR: box inset ", kit_fmt(inset), " mm leaves ", kit_fmt(inset - hole_d / 2),
            " mm wall → ", kit_fmt(inset - hole_d / 2), " < 2.0 mm → increase inset to ",
            kit_fmt(hole_d / 2 + boss_wall)));
    assert(!has_holes || 2 * inset + hole_d <= min_side,
        str("ERROR: box holes with inset ", kit_fmt(inset), " do not fit in ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(2 * inset + hole_d), " > ", kit_fmt(min_side),
            " → reduce inset or enlarge the box"));

    difference() {
        union() {
            difference() {
                kit_round_block(w, d, h, corner_r);
                // Inner cavity: open at the top, so the cut is taller than h.
                translate([0, 0, floor])
                    kit_round_block(w - 2 * wall, d - 2 * wall, h - floor + 1,
                                    kit_max2(corner_r - wall, 0));
            }
            if (has_holes)
                intersection() {
                    kit_round_block(w, d, h, corner_r);
                    for (p = kit_corner_points(w, d, inset))
                        translate([p[0], p[1], 0])
                            cylinder(h = h, d = boss_d, $fn = 64);
                }
        }
        if (has_holes)
            for (p = kit_corner_points(w, d, inset))
                translate([p[0], p[1], -1])
                    cylinder(h = h + 2, d = hole_d, $fn = 64);
    }
}

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_box(w, d, h, wall = 2.4, floor = 2.4, corner_r = 0,
                      hole = "", inset = 0) = [w, d, h];

function kit_through_holes_box(w = 0, d = 0, h = 0, wall = 2.4, floor = 2.4,
                               corner_r = 0, hole = "", inset = 0) =
    hole != "" ? 4 : 0;
