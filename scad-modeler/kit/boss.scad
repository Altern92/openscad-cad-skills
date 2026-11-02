// kit/boss.scad — įvorė (stovas) su centrine kiauryme (P1).
//
// Lokali pradžia: apačios centras. bbox = [d_out, d_out, h].
// Kiaurymė eina per visą aukštį → deklaruojama THROUGH_HOLES=1 ir HOLE.

include <lib.scad>

module kit_boss(d_out, d_bore, h) {
    wall = (d_out - d_bore) / 2;

    assert(wall >= 1.5,
        str("KLAIDA: sienelė ", kit_fmt(wall), " mm → ", kit_fmt(wall), " < ",
            kit_fmt(1.5), " mm → sumažink d_bore iki ", kit_fmt(d_out - 3.0),
            " arba didink d_out"));
    assert(d_bore >= 2.0,
        str("KLAIDA: kiaurymė Ø", kit_fmt(d_bore), " mm → ", kit_fmt(d_bore), " < ",
            kit_fmt(2.0), " mm → didink d_bore iki ", kit_fmt(2.0)));
    assert(h >= 2.0,
        str("KLAIDA: įvorė ", kit_fmt(h), " mm → ", kit_fmt(h), " < ", kit_fmt(2.0),
            " mm → didink h iki ", kit_fmt(2.0)));

    difference() {
        cylinder(h = h, d = d_out, $fn = 64);
        translate([0, 0, -1])
            cylinder(h = h + 2, d = d_bore, $fn = 64);
    }
}

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_boss(d_out, d_bore, h) = [d_out, d_out, h];

function kit_through_holes_boss() = 1;

// Tarpo skylės deklaracija: [x, y, z, ašis, Ø] — ašies taškas apačioje.
function kit_hole_boss(d_out, d_bore, h) = [0, 0, 0, "Z", d_bore];
