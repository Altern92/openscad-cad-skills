// kit/bracket_l.scad — L formos laikiklis (P1).
//
// Lokali pradžia: apatinio paviršiaus centras. bbox = [w, d, h].
// Horizontali plokštė: w×d×t, z ∈ [0, t].
// Vertikali plokštė: w×t×h, gale (y ∈ [d/2 - t, d/2]).
// Deklaruojamos 2 kiaurymės — abi horizontalioje plokštėje.

include <lib.scad>

module kit_bracket_l(w, d, h, t, hole) {
    hole_d = kit_hole_d(hole);
    wall_min = 2.0;
    min_side = kit_min2(w, d);
    // Po VIENĄ kiaurymę KIEKVIENOJE lentynoje (taip prašoma realiuose
    // prašymuose: „su skyle abiejose lentynose").
    //   horizontali: ašis Z, centras (0, hole_y)
    //   vertikali:   ašis Y, centras (0, h - hole_inset)
    hole_inset = hole_d / 2 + wall_min;
    hole_y = -d / 2 + hole_inset;
    hole_vz = h - hole_inset;

    assert(hole_d > 0,
        str("KLAIDA: hole ", hole, " nežinomas žymėjimas → naudok M3, M4, M5, M6 arba Ø mm → pakeisk hole"));
    assert(t >= 2.5,
        str("KLAIDA: L laikiklio storis ", kit_fmt(t), " mm → ", kit_fmt(t),
            " < ", kit_fmt(2.5), " mm → apkrovos neatlaikys; didink t iki ", kit_fmt(2.5)));
    assert(h > t + 2,
        str("KLAIDA: vertikali dalis ", kit_fmt(h), " mm → ", kit_fmt(h), " ≤ ",
            kit_fmt(t + 2), " mm → per žema ", kit_fmt(t), " mm storiui; didink h iki ",
            kit_fmt(t + 2)));
    assert(hole_d + 2 * wall_min <= min_side,
        str("KLAIDA: skylė Ø", kit_fmt(hole_d), " netelpa ", kit_fmt(w), "×", kit_fmt(d),
            " su ", kit_fmt(wall_min), " mm sienele → ", kit_fmt(hole_d + 2 * wall_min),
            " > ", kit_fmt(min_side), " → didink laikiklį arba mažink hole"));
    assert(hole_vz - hole_d / 2 >= t + wall_min,
        str("KLAIDA: vertikalios lentynos skylė Ø", kit_fmt(hole_d), " netelpa h=",
            kit_fmt(h), " → reikia h ≥ ", kit_fmt(t + wall_min + hole_d / 2 + hole_inset),
            " → didink h arba mažink hole"));

    difference() {
        union() {
            // Horizontali plokštė.
            kit_round_block(w, d, t, 0);
            // Vertikali plokštė ties galu.
            translate([0, d / 2 - t / 2, h / 2])
                cube([w, t, h], center = true);
        }
        // Horizontali lentyna: kiaurymė per Z.
        translate([0, hole_y, -1])
            cylinder(h = t + 2, d = hole_d, $fn = 64);
        // Vertikali lentyna: kiaurymė per Y.
        translate([0, d / 2 - t - 1, hole_vz])
            rotate([-90, 0, 0])
                cylinder(h = t + 2, d = hole_d, $fn = 64);
    }
}

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_bracket_l(w, d, h, t, hole) = [w, d, h];

function kit_through_holes_bracket_l() = 2;
