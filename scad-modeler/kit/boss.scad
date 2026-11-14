// kit/boss.scad — boss (standoff) with a central bore (P1).
//
// Local origin: bottom centre. bbox = [d_out, d_out, h].
// The bore runs the full height → declared as THROUGH_HOLES=1 and HOLE.

include <lib.scad>

module kit_boss(d_out, d_bore, h) {
    wall = (d_out - d_bore) / 2;

    assert(wall >= 1.5,
        str("ERROR: wall ", kit_fmt(wall), " mm → ", kit_fmt(wall), " < ",
            kit_fmt(1.5), " mm → reduce d_bore to ", kit_fmt(d_out - 3.0),
            " or increase d_out"));
    assert(d_bore >= 2.0,
        str("ERROR: bore Ø", kit_fmt(d_bore), " mm → ", kit_fmt(d_bore), " < ",
            kit_fmt(2.0), " mm → increase d_bore to ", kit_fmt(2.0)));
    assert(h >= 2.0,
        str("ERROR: boss ", kit_fmt(h), " mm → ", kit_fmt(h), " < ", kit_fmt(2.0),
            " mm → increase h to ", kit_fmt(2.0)));

    difference() {
        cylinder(h = h, d = d_out, $fn = 64);
        translate([0, 0, -1])
            cylinder(h = h + 2, d = d_bore, $fn = 64);
    }
}

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_boss(d_out, d_bore, h) = [d_out, d_out, h];

function kit_through_holes_boss() = 1;

// Clearance hole declaration: [x, y, z, axis, Ø] — axis point at the bottom.
function kit_hole_boss(d_out, d_bore, h) = [0, 0, 0, "Z", d_bore];
