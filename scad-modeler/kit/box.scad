// kit/box.scad — atviro viršaus dėžutė (korpusas) (P1).
//
// Lokali pradžia: apatinio paviršiaus centras. bbox = [w, d, h].
// Sienelės `wall`, dugnas `floor`; viršus atviras.
// `hole` ("" = be skylių): 4 kampinės varžtų statramsčių (boss) kiaurymės,
// suderintos su `kit_lid(..., hole, inset)`.

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
        str("KLAIDA: sienelė ", kit_fmt(wall), " mm → ", kit_fmt(wall), " < ",
            kit_fmt(wall_min), " mm (FDM minimumas) → didink wall iki ", kit_fmt(wall_min)));
    assert(2 * wall < w && 2 * wall < d,
        str("KLAIDA: sienelės ", kit_fmt(wall), "×2 neišsitenka ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(2 * wall), " ≥ ", kit_fmt(min_side),
            " → didink dėžutę arba mažink wall"));
    assert(floor >= wall_min && floor < h,
        str("KLAIDA: dugnas ", kit_fmt(floor), " mm → turi būti ", kit_fmt(wall_min),
            " ≤ floor < h=", kit_fmt(h), " → nustatyk floor tarp ", kit_fmt(wall_min),
            " ir ", kit_fmt(h)));
    assert(corner_r >= 0 && corner_r * 2 < min_side,
        str("KLAIDA: corner_r ", kit_fmt(corner_r), " netelpa į ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(min_side),
            " → mažink corner_r"));
    assert(!has_holes || (hole_d >= 3.0 && hole_d <= 6.5),
        str("KLAIDA: hole ", hole, " = Ø", kit_fmt(hole_d), " mm → palaikoma 3.0–6.5 mm → naudok M3..M6"));
    assert(!has_holes || inset >= hole_d / 2 + boss_wall,
        str("KLAIDA: dėžutės inset ", kit_fmt(inset), " mm palieka ", kit_fmt(inset - hole_d / 2),
            " mm sienelę → ", kit_fmt(inset - hole_d / 2), " < 2.0 mm → didink inset iki ",
            kit_fmt(hole_d / 2 + boss_wall)));
    assert(!has_holes || 2 * inset + hole_d <= min_side,
        str("KLAIDA: dėžutės skylės su inset ", kit_fmt(inset), " netelpa į ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(2 * inset + hole_d), " > ", kit_fmt(min_side),
            " → mažink inset arba didink dėžutę"));

    difference() {
        union() {
            difference() {
                kit_round_block(w, d, h, corner_r);
                // Vidinė ertmė: atvira viršuje, todėl pjūvis aukštesnis už h.
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

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_box(w, d, h, wall = 2.4, floor = 2.4, corner_r = 0,
                      hole = "", inset = 0) = [w, d, h];

function kit_through_holes_box(w = 0, d = 0, h = 0, wall = 2.4, floor = 2.4,
                               corner_r = 0, hole = "", inset = 0) =
    hole != "" ? 4 : 0;
