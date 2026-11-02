// kit/plate_with_holes.scad — stačiakampė plokštė su skylėmis kampuose (P1).
//
// Lokali pradžia: apatinio paviršiaus centras. bbox = [w, d, t].
// Skylės centruotos pagal `inset` nuo krašto iki skylės CENTRO.
// `hole` — "M3".."M6" arba Ø mm; skersmuo išsprendžiamas kit/lib.scad.

include <lib.scad>

module kit_plate_with_holes(w, d, t, hole, inset,
                            corner_r = 0, pattern = "corners") {
    hole_d = kit_hole_d(hole);
    wall_min = 2.0;
    min_side = kit_min2(w, d);
    inset_min = hole_d / 2 + wall_min;

    assert(hole_d > 0,
        str("KLAIDA: hole ", hole, " nežinomas žymėjimas → naudok M3, M4, M5, M6 arba Ø mm → pakeisk hole"));
    assert(hole_d >= 3.0 && hole_d <= 6.5,
        str("KLAIDA: hole ", hole, " = Ø", kit_fmt(hole_d), " mm → ",
            kit_fmt(hole_d), " < ", kit_fmt(3.0), " arba > ", kit_fmt(6.5),
            " mm → naudok M3..M6"));
    assert(inset >= inset_min,
        str("KLAIDA: inset ", kit_fmt(inset), " mm palieka ", kit_fmt(inset - hole_d / 2),
            " mm sienelę → ", kit_fmt(inset - hole_d / 2), " < ", kit_fmt(wall_min),
            " mm → didink inset iki ", kit_fmt(inset_min)));
    assert(2 * inset + hole_d <= min_side,
        str("KLAIDA: skylės ", hole, " su inset ", kit_fmt(inset), " netelpa į ",
            kit_fmt(w), "×", kit_fmt(d), " → ", kit_fmt(2 * inset + hole_d), " > ",
            kit_fmt(min_side), " → mažink inset arba didink plokštę"));
    assert(t >= 1.2,
        str("KLAIDA: storis ", kit_fmt(t), " mm → ", kit_fmt(t),
            " < ", kit_fmt(1.2), " mm (FDM minimumas) → didink t iki ", kit_fmt(1.2)));
    assert(corner_r * 2 < min_side,
        str("KLAIDA: corner_r ", kit_fmt(corner_r), " per didelis ", kit_fmt(w), "×",
            kit_fmt(d), " plokštei → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(min_side),
            " → didink plotį arba mažink corner_r"));

    difference() {
        kit_round_block(w, d, t, corner_r);
        for (p = kit_hole_points(w, d, inset, pattern))
            translate([p[0], p[1], -1])
                cylinder(h = t + 2, d = hole_d, $fn = 64);
    }
}

// Skylu centrai pagal `pattern`: "corners" (4) arba "corners6" (4 + 2 ilgesnės pusės viduryje).
function kit_hole_points(w, d, inset, pattern) =
    pattern == "corners6"
        ? concat(kit_corner_points(w, d, inset),
                 w >= d ? [[0, d / 2 - inset], [0, -d / 2 + inset]]
                        : [[w / 2 - inset, 0], [-w / 2 + inset, 0]])
        : kit_corner_points(w, d, inset);

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_plate_with_holes(w, d, t, hole, inset,
                                   corner_r = 0, pattern = "corners") = [w, d, t];

function kit_through_holes_plate_with_holes(pattern = "corners") =
    pattern == "corners6" ? 6 : 4;
