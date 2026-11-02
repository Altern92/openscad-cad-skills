// kit/hole_pattern.scad — tinklelis nx × ny skylių plokštėje (P1).
//
// Lokali pradžia: apatinio paviršiaus centras.
// Plokštė = nx*dx × ny*dy; skylės — celių centruose (žingsniai dx, dy).
// bbox = [nx*dx, ny*dy, t]; kiaurymių skaičius = nx * ny.
//
// PASTABA (2026-11-01): pradinė docs/03 bbox formulė
// "(nx-1)*dx + hole_d" skyles darė LIESTINES plokštės kraštui (sienelė 0 mm,
// ne watertight — vartai pagavo topology FAIL). 4-as assert naudoja nx*dx —
// tas pats celių skaičius. Sutarta: plokštė = nx*dx × ny*dy, sienelė
// (dx - hole_d)/2 ≥ 2 mm pagal assert 2/3.

include <lib.scad>

module kit_hole_pattern(nx, ny, dx, dy, hole, t) {
    hole_d = kit_hole_d(hole);
    wall_min = 2.0;
    w = nx * dx;
    d = ny * dy;

    assert(hole_d > 0,
        str("KLAIDA: hole ", hole, " nežinomas žymėjimas → naudok M3, M4, M5, M6 arba Ø mm → pakeisk hole"));
    assert(nx >= 1 && ny >= 1 && nx * ny >= 2,
        str("KLAIDA: tinklelis ", nx, "×", ny, " → ", nx * ny,
            " < 2 → tinkleliui reikia bent 2 skylių; didink nx arba ny"));
    assert(dx >= hole_d + 2 * wall_min,
        str("KLAIDA: žingsnis dx ", kit_fmt(dx), " mm → ", kit_fmt(dx), " < Ø",
            kit_fmt(hole_d), "+", kit_fmt(2 * wall_min), " → didink dx iki ",
            kit_fmt(hole_d + 2 * wall_min)));
    assert(dy >= hole_d + 2 * wall_min,
        str("KLAIDA: žingsnis dy ", kit_fmt(dy), " mm → ", kit_fmt(dy), " < Ø",
            kit_fmt(hole_d), "+", kit_fmt(2 * wall_min), " → didink dy iki ",
            kit_fmt(hole_d + 2 * wall_min)));
    assert(hole_d <= 0.5 * kit_min2(w, d),
        str("KLAIDA: skylė Ø", kit_fmt(hole_d), " per didelė tinkleliui ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(hole_d), " > ", kit_fmt(0.5 * kit_min2(w, d)),
            " → mažink hole arba didink žingsnius"));

    difference() {
        linear_extrude(height = t, convexity = 4) square([w, d], center = true);
        for (i = [0 : nx - 1], j = [0 : ny - 1])
            translate([-w / 2 + dx / 2 + i * dx, -d / 2 + dy / 2 + j * dy, -1])
                cylinder(h = t + 2, d = hole_d, $fn = 64);
    }
}

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_hole_pattern(nx, ny, dx, dy, hole, t) = [nx * dx, ny * dy, t];

function kit_through_holes_hole_pattern(nx, ny, dx, dy, hole, t) = nx * ny;
