// kit/plate.scad — stačiakampė plokštė, pasirinktinai apvalintais kampais
// ir viršutinės briaunos nuožulna (P1).
//
// Lokali pradžia: apatinio paviršiaus centras. bbox = [w, d, t].

include <lib.scad>

module kit_plate(w, d, t, corner_r = 0, chamfer = 0) {
    min_side = kit_min2(w, d);

    assert(t >= 1.2,
        str("KLAIDA: storis ", kit_fmt(t), " mm → ", kit_fmt(t),
            " < ", kit_fmt(1.2), " mm (FDM minimumas) → didink t iki ", kit_fmt(1.2)));
    assert(corner_r * 2 < min_side,
        str("KLAIDA: corner_r ", kit_fmt(corner_r), " per didelis ", kit_fmt(w), "×",
            kit_fmt(d), " plokštei → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(min_side),
            " → didink plotį arba mažink corner_r"));
    assert(corner_r >= 0 && chamfer >= 0 && chamfer < t,
        str("KLAIDA: chamfer ", kit_fmt(chamfer), " mm → turi būti 0 ≤ chamfer < t=",
            kit_fmt(t), " → mažink chamfer arba didink t"));

    if (chamfer > 0) {
        // Korpusas + viršutinė nuožulna: viršutinė dalis susiaurėja po
        // `chamfer` nuo kiekvieno krašto, todėl bbox lieka [w, d, t].
        linear_extrude(height = t - chamfer, convexity = 4)
            kit_round2d(w, d, corner_r);
        translate([0, 0, t - chamfer])
            linear_extrude(
                height = chamfer,
                scale = [(w - 2 * chamfer) / w, (d - 2 * chamfer) / d],
                convexity = 4)
                kit_round2d(w, d, corner_r);
    } else {
        kit_round_block(w, d, t, corner_r);
    }
}

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_plate(w, d, t, corner_r = 0, chamfer = 0) = [w, d, t];

function kit_through_holes_plate() = 0;
