// kit/lid.scad — lid with an inner lip that fits inside the box (P1).
//
// Local origin: bottom face centre — i.e. the bottom of the LIP.
// The lip is z ∈ [0, lip], the plate z ∈ [lip, lip + t].
// bbox = [w, d, t + lip]; declared through-holes = 0.
//
// Lip outside = box opening minus `clearance` per side:
//   lip_outer = w - 2*box_wall - 2*clearance
// The lid is made for the same box, so box wall = `wall`.

include <lib.scad>

function kit_lid_lip_outer(w, box_wall, clearance) =
    w - 2 * box_wall - 2 * clearance;

// `hole` ("" = no holes): corner screw holes through the plate AND the lip.
module kit_lid(w, d, t = 3, lip = 1.8, clearance = 0.2, wall = 2.4, corner_r = 0,
               hole = "", inset = 0) {
    clearance_min = 0.15;
    lip_min = 1.0;
    t_min = 1.6;
    lip_outer_w = kit_lid_lip_outer(w, wall, clearance);
    lip_outer_d = kit_lid_lip_outer(d, wall, clearance);
    // Lip corner radius: must fit the box inner corner (corner_r - wall)
    // with the clearance gap, so subtract both the wall and the gap.
    lip_r = kit_max2(corner_r - wall - clearance, 0);
    has_holes = hole != "";
    hole_d = has_holes ? kit_hole_d(hole) : 0;

    assert(clearance >= clearance_min,
        str("ERROR: clearance ", kit_fmt(clearance), " mm → ", kit_fmt(clearance),
            " < ", kit_fmt(clearance_min), " mm → FDM parts will not fit together; increase clearance to ",
            kit_fmt(clearance_min)));
    assert(lip >= lip_min,
        str("ERROR: lip ", kit_fmt(lip), " mm → ", kit_fmt(lip), " < ",
            kit_fmt(lip_min), " mm → lid will not hold; increase lip to ", kit_fmt(lip_min)));
    assert(t >= t_min,
        str("ERROR: lid thickness ", kit_fmt(t), " mm → ", kit_fmt(t), " < ",
            kit_fmt(t_min), " mm → increase t to ", kit_fmt(t_min)));
    assert(wall > 2 * clearance,
        str("ERROR: wall ", kit_fmt(wall), " mm too thin for clearance ", kit_fmt(clearance),
            " mm → ", kit_fmt(wall), " ≤ ", kit_fmt(2 * clearance),
            " → increase wall or reduce clearance"));
    assert(!has_holes || (hole_d >= 3.0 && hole_d <= 6.5),
        str("ERROR: hole ", hole, " = Ø", kit_fmt(hole_d), " mm → supported 3.0–6.5 mm → use M3..M6"));
    assert(!has_holes || inset >= hole_d / 2 + 2.0,
        str("ERROR: lid inset ", kit_fmt(inset), " mm leaves ", kit_fmt(inset - hole_d / 2),
            " mm wall → ", kit_fmt(inset - hole_d / 2), " < 2.0 mm → increase inset to ",
            kit_fmt(hole_d / 2 + 2.0)));
    assert(!has_holes || 2 * inset + hole_d <= kit_min2(w, d),
        str("ERROR: lid holes with inset ", kit_fmt(inset), " do not fit in ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(2 * inset + hole_d), " > ", kit_fmt(kit_min2(w, d)),
            " → reduce inset or enlarge the lid"));
    assert(corner_r >= 0 && corner_r * 2 < kit_min2(w, d),
        str("ERROR: corner_r ", kit_fmt(corner_r), " does not fit in ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(kit_min2(w, d)),
            " → reduce corner_r"));
    assert(lip_outer_w > 2 * wall && lip_outer_d > 2 * wall,
        str("ERROR: lip ", kit_fmt(lip_outer_w), "×", kit_fmt(lip_outer_d),
            " too small for walls ", kit_fmt(wall), "×2 → enlarge the lid or reduce wall"));

    difference() {
        union() {
            // Plate on top.
            translate([0, 0, lip])
                kit_round_block(w, d, t, corner_r);
            // Lip ring at the bottom (fits inside the box), with cut-outs around
            // the box corner screw bosses (boss_d = hole_d + 4.0).
            difference() {
                kit_round_block(lip_outer_w, lip_outer_d, lip, lip_r);
                if (has_holes)
                    for (p = kit_corner_points(w, d, inset))
                        translate([p[0], p[1], -1])
                            cylinder(h = lip + 2, d = hole_d + 4.0 + 2 * clearance, $fn = 64);
            }
        }
        // Hollow out the lip — the cut ends exactly at the plate bottom (z = lip).
        translate([0, 0, -1])
            kit_round_block(lip_outer_w - 2 * wall, lip_outer_d - 2 * wall, lip + 1,
                            kit_max2(lip_r - wall, 0));
        if (has_holes)
            for (p = kit_corner_points(w, d, inset))
                translate([p[0], p[1], -1])
                    cylinder(h = t + lip + 2, d = hole_d, $fn = 64);
    }
}

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_lid(w, d, t = 3, lip = 1.8, clearance = 0.2, wall = 2.4,
                      corner_r = 0, hole = "", inset = 0) = [w, d, t + lip];

function kit_through_holes_lid(w, d, t = 3, lip = 1.8, clearance = 0.2, wall = 2.4,
                               corner_r = 0, hole = "", inset = 0) =
    hole != "" ? 4 : 0;
