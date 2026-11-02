// kit/lid.scad — dangtis su vidiniu lizdu (lip), kuris įeina į box vidų (P1).
//
// Lokali pradžia: apatinio paviršiaus centras — t. y. LIZDO apačia.
// Lizdas (lip) yra z ∈ [0, lip], plokštė — z ∈ [lip, lip + t].
// bbox = [w, d, t + lip]; deklaruojami through-holes = 0.
//
// Lizdo išorė = box anga atėmus `clearance` per pusę:
//   lip_outer = w - 2*box_wall - 2*clearance
// Dangtis daromas tai pačiai dėžutei, todėl box sienelė = `wall`.

include <lib.scad>

function kit_lid_lip_outer(w, box_wall, clearance) =
    w - 2 * box_wall - 2 * clearance;

// `hole` ("" = be skylių): varžtų kiaurymės kampuose per plokštę IR lizdą.
module kit_lid(w, d, t = 3, lip = 1.8, clearance = 0.2, wall = 2.4, corner_r = 0,
               hole = "", inset = 0) {
    clearance_min = 0.15;
    lip_min = 1.0;
    t_min = 1.6;
    lip_outer_w = kit_lid_lip_outer(w, wall, clearance);
    lip_outer_d = kit_lid_lip_outer(d, wall, clearance);
    // Lizdo kampų spindulys: turi tilpti į dėžutės vidinį kampą (corner_r - wall)
    // su clearance tarpu, todėl atimame ir sienelę, ir tarpą.
    lip_r = kit_max2(corner_r - wall - clearance, 0);
    has_holes = hole != "";
    hole_d = has_holes ? kit_hole_d(hole) : 0;

    assert(clearance >= clearance_min,
        str("KLAIDA: tarpas ", kit_fmt(clearance), " mm → ", kit_fmt(clearance),
            " < ", kit_fmt(clearance_min), " mm → FDM detalės nesisujungs; didink clearance iki ",
            kit_fmt(clearance_min)));
    assert(lip >= lip_min,
        str("KLAIDA: lizdas ", kit_fmt(lip), " mm → ", kit_fmt(lip), " < ",
            kit_fmt(lip_min), " mm → dangtis nulaikys; didink lip iki ", kit_fmt(lip_min)));
    assert(t >= t_min,
        str("KLAIDA: dangčio storis ", kit_fmt(t), " mm → ", kit_fmt(t), " < ",
            kit_fmt(t_min), " mm → didink t iki ", kit_fmt(t_min)));
    assert(wall > 2 * clearance,
        str("KLAIDA: sienelė ", kit_fmt(wall), " mm per plona tarpui ", kit_fmt(clearance),
            " mm → ", kit_fmt(wall), " ≤ ", kit_fmt(2 * clearance),
            " → didink wall arba mažink clearance"));
    assert(!has_holes || (hole_d >= 3.0 && hole_d <= 6.5),
        str("KLAIDA: hole ", hole, " = Ø", kit_fmt(hole_d), " mm → palaikoma 3.0–6.5 mm → naudok M3..M6"));
    assert(!has_holes || inset >= hole_d / 2 + 2.0,
        str("KLAIDA: dangčio inset ", kit_fmt(inset), " mm palieka ", kit_fmt(inset - hole_d / 2),
            " mm sienelę → ", kit_fmt(inset - hole_d / 2), " < 2.0 mm → didink inset iki ",
            kit_fmt(hole_d / 2 + 2.0)));
    assert(!has_holes || 2 * inset + hole_d <= kit_min2(w, d),
        str("KLAIDA: dangčio skylės su inset ", kit_fmt(inset), " netelpa į ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(2 * inset + hole_d), " > ", kit_fmt(kit_min2(w, d)),
            " → mažink inset arba didink dangtį"));
    assert(corner_r >= 0 && corner_r * 2 < kit_min2(w, d),
        str("KLAIDA: corner_r ", kit_fmt(corner_r), " netelpa į ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(kit_min2(w, d)),
            " → mažink corner_r"));
    assert(lip_outer_w > 2 * wall && lip_outer_d > 2 * wall,
        str("KLAIDA: lizdas ", kit_fmt(lip_outer_w), "×", kit_fmt(lip_outer_d),
            " per mažas sienelėms ", kit_fmt(wall), "×2 → didink dangtį arba mažink wall"));

    difference() {
        union() {
            // Plokštė viršuje.
            translate([0, 0, lip])
                kit_round_block(w, d, t, corner_r);
            // Lizdo žiedas apačioje (įeina į dėžutės vidų), su išpjovomis aplink
            // dėžutės kampinius varžtų statramsčius (boss_d = hole_d + 4.0).
            difference() {
                kit_round_block(lip_outer_w, lip_outer_d, lip, lip_r);
                if (has_holes)
                    for (p = kit_corner_points(w, d, inset))
                        translate([p[0], p[1], -1])
                            cylinder(h = lip + 2, d = hole_d + 4.0 + 2 * clearance, $fn = 64);
            }
        }
        // Išimti lizdo vidų — pjūvis baigiasi lygiai ties plokštės apačia (z = lip).
        translate([0, 0, -1])
            kit_round_block(lip_outer_w - 2 * wall, lip_outer_d - 2 * wall, lip + 1,
                            kit_max2(lip_r - wall, 0));
        if (has_holes)
            for (p = kit_corner_points(w, d, inset))
                translate([p[0], p[1], -1])
                    cylinder(h = t + lip + 2, d = hole_d, $fn = 64);
    }
}

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_lid(w, d, t = 3, lip = 1.8, clearance = 0.2, wall = 2.4,
                      corner_r = 0, hole = "", inset = 0) = [w, d, t + lip];

function kit_through_holes_lid(w, d, t = 3, lip = 1.8, clearance = 0.2, wall = 2.4,
                               corner_r = 0, hole = "", inset = 0) =
    hole != "" ? 4 : 0;
