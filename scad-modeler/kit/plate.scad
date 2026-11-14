// kit/plate.scad — rectangular plate, with optional rounded corners
// and a top-edge chamfer (P1).
//
// Local origin: bottom face centre. bbox = [w, d, t].

include <lib.scad>

module kit_plate(w, d, t, corner_r = 0, chamfer = 0) {
    min_side = kit_min2(w, d);

    assert(t >= 1.2,
        str("ERROR: thickness ", kit_fmt(t), " mm → ", kit_fmt(t),
            " < ", kit_fmt(1.2), " mm (FDM minimum) → increase t to ", kit_fmt(1.2)));
    assert(corner_r * 2 < min_side,
        str("ERROR: corner_r ", kit_fmt(corner_r), " too large for ", kit_fmt(w), "×",
            kit_fmt(d), " plate → ", kit_fmt(corner_r * 2), " ≥ ", kit_fmt(min_side),
            " → increase width or reduce corner_r"));
    assert(corner_r >= 0 && chamfer >= 0 && chamfer < t,
        str("ERROR: chamfer ", kit_fmt(chamfer), " mm → must be 0 ≤ chamfer < t=",
            kit_fmt(t), " → reduce chamfer or increase t"));

    if (chamfer > 0) {
        // Body + top chamfer: the top part narrows by `chamfer`
        // from each edge, so the bbox stays [w, d, t].
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

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_plate(w, d, t, corner_r = 0, chamfer = 0) = [w, d, t];

function kit_through_holes_plate() = 0;
