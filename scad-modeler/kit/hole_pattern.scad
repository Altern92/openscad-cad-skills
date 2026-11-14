// kit/hole_pattern.scad — nx × ny grid of holes in a plate (P1).
//
// Local origin: bottom face centre.
// Plate = nx*dx × ny*dy; holes at the cell centres (pitches dx, dy).
// bbox = [nx*dx, ny*dy, t]; through-hole count = nx * ny.
//
// NOTE (2026-11-01): the original docs/03 bbox formula
// "(nx-1)*dx + hole_d" made the holes TANGENT to the plate edge (wall 0 mm,
// not watertight — the gates caught topology FAIL). The 4th assert uses nx*dx —
// the same cell count. Agreed: plate = nx*dx × ny*dy, wall
// (dx - hole_d)/2 ≥ 2 mm per asserts 2/3.

include <lib.scad>

module kit_hole_pattern(nx, ny, dx, dy, hole, t) {
    hole_d = kit_hole_d(hole);
    wall_min = 2.0;
    w = nx * dx;
    d = ny * dy;

    assert(hole_d > 0,
        str("ERROR: hole ", hole, " unknown designation → use M3, M4, M5, M6 or Ø mm → change hole"));
    assert(nx >= 1 && ny >= 1 && nx * ny >= 2,
        str("ERROR: grid ", nx, "×", ny, " → ", nx * ny,
            " < 2 → a grid needs at least 2 holes; increase nx or ny"));
    assert(dx >= hole_d + 2 * wall_min,
        str("ERROR: pitch dx ", kit_fmt(dx), " mm → ", kit_fmt(dx), " < Ø",
            kit_fmt(hole_d), "+", kit_fmt(2 * wall_min), " → increase dx to ",
            kit_fmt(hole_d + 2 * wall_min)));
    assert(dy >= hole_d + 2 * wall_min,
        str("ERROR: pitch dy ", kit_fmt(dy), " mm → ", kit_fmt(dy), " < Ø",
            kit_fmt(hole_d), "+", kit_fmt(2 * wall_min), " → increase dy to ",
            kit_fmt(hole_d + 2 * wall_min)));
    assert(hole_d <= 0.5 * kit_min2(w, d),
        str("ERROR: hole Ø", kit_fmt(hole_d), " too large for grid ", kit_fmt(w), "×",
            kit_fmt(d), " → ", kit_fmt(hole_d), " > ", kit_fmt(0.5 * kit_min2(w, d)),
            " → reduce hole or increase the pitches"));

    difference() {
        linear_extrude(height = t, convexity = 4) square([w, d], center = true);
        for (i = [0 : nx - 1], j = [0 : ny - 1])
            translate([-w / 2 + dx / 2 + i * dx, -d / 2 + dy / 2 + j * dy, -1])
                cylinder(h = t + 2, d = hole_d, $fn = 64);
    }
}

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_hole_pattern(nx, ny, dx, dy, hole, t) = [nx * dx, ny * dy, t];

function kit_through_holes_hole_pattern(nx, ny, dx, dy, hole, t) = nx * ny;
