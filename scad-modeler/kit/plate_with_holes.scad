// kit/plate_with_holes.scad — rectangular plate with corner holes (P1).
//
// Local origin: bottom face centre. bbox = [w, d, t].
// Holes are placed by `inset`, from the edge to the hole CENTRE.
// `hole` — "M3".."M6" or Ø mm; the diameter is resolved in kit/lib.scad.

include <lib.scad>

module kit_plate_with_holes(w, d, t, hole, inset,
                            corner_r = 0, pattern = "corners") {
    hole_d = kit_hole_d(hole);
    wall_min = 2.0;
    min_side = kit_min2(w, d);
    inset_min = hole_d / 2 + wall_min;

    assert(hole_d > 0,
        str("ERROR: hole ", hole, " unknown designation → use M3, M4, M5, M6 or Ø mm → change hole"));
    assert(hole_d >= 3.0 && hole_d <= 6.5,
        str("ERROR: hole ", hole, " = Ø", kit_fmt(hole_d), " mm → ",
            kit_fmt(hole_d), " < ", kit_fmt(3.0), " or > ", kit_fmt(6.5),
            " mm → use M3..M6"));
    assert(inset >= inset_min,
        str("ERROR: inset ", kit_fmt(inset), " mm leaves ", kit_fmt(inset - hole_d / 2),
            " mm wall → ", kit_fmt(inset - hole_d / 2), " < ", kit_fmt(wall_min),
            " mm → increase inset to ", kit_fmt(inset_min)));
    assert(2 * inset + hole_d <= min_side,
        str("ERROR: holes ", hole, " with inset ", kit_fmt(inset), " do not fit in ",
            kit_fmt(w), "×", kit_fmt(d), " → ", kit_fmt(2 * inset + hole_d), " > ",
            kit_fmt(min_side), " → reduce inset or enlarge the plate"));
    assert(t >= 1.2,
        str("ERROR: thickness ", kit_fmt(t), " mm → ", kit_fmt(t),
            " < ", kit_fmt(1.2), " mm (FDM minimum) → increase t to ", kit_fmt(1.2)));
    assert(corner_r * 2 < min_side,
        str("ERROR: corner_r ", kit_fmt(corner_r), " too large for ", kit_fmt(w), "×",
            kit_fmt(d), " plate → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(min_side),
            " → increase width or reduce corner_r"));

    difference() {
        kit_round_block(w, d, t, corner_r);
        for (p = kit_hole_points(w, d, inset, pattern))
            translate([p[0], p[1], -1])
                cylinder(h = t + 2, d = hole_d, $fn = 64);
    }
}

// Hole centres by `pattern`: "corners" (4) or "corners6" (4 + 2 at the middle of the longer sides).
function kit_hole_points(w, d, inset, pattern) =
    pattern == "corners6"
        ? concat(kit_corner_points(w, d, inset),
                 w >= d ? [[0, d / 2 - inset], [0, -d / 2 + inset]]
                        : [[w / 2 - inset, 0], [-w / 2 + inset, 0]])
        : kit_corner_points(w, d, inset);

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_plate_with_holes(w, d, t, hole, inset,
                                   corner_r = 0, pattern = "corners") = [w, d, t];

function kit_through_holes_plate_with_holes(pattern = "corners") =
    pattern == "corners6" ? 6 : 4;
