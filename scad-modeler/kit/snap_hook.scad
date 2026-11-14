// kit/snap_hook.scad — hook on a spring beam (P1).
//
// Local origin: centre of the mounting base. bbox = [beam_w, beam_t, beam_l].
// The beam stands along Z; the hook is at the top, protruding by `undercut`.
// The lower beam is set back by `undercut` so the hook fits in the
// declared bbox (Y ≤ beam_t).

include <lib.scad>

module kit_snap_hook(beam_l, beam_w, beam_t, hook_h, undercut) {
    assert(beam_t >= 1.2,
        str("ERROR: beam ", kit_fmt(beam_t), " mm → ", kit_fmt(beam_t), " < ",
            kit_fmt(1.2), " mm → increase beam_t to ", kit_fmt(1.2)));
    assert(undercut <= 0.3 * beam_t,
        str("ERROR: undercut ", kit_fmt(undercut), " mm → ", kit_fmt(undercut), " > ",
            kit_fmt(0.3 * beam_t), " (30 % of beam) → reduce undercut to ",
            kit_fmt(0.3 * beam_t), " or increase beam_t"));
    assert(hook_h >= undercut + 0.5,
        str("ERROR: hook_h ", kit_fmt(hook_h), " mm → ", kit_fmt(hook_h), " < undercut + 0.5 = ",
            kit_fmt(undercut + 0.5), " mm → increase hook_h to ", kit_fmt(undercut + 0.5)));
    assert(beam_l >= 4 * beam_t,
        str("ERROR: beam too short ", kit_fmt(beam_l), " mm → ", kit_fmt(beam_l), " < 4×",
            kit_fmt(beam_t), " = ", kit_fmt(4 * beam_t),
            " mm → will have no spring; increase beam_l"));
    assert(hook_h < beam_l,
        str("ERROR: hook_h ", kit_fmt(hook_h), " mm → ", kit_fmt(hook_h), " ≥ beam_l=",
            kit_fmt(beam_l), " mm → increase beam_l or reduce hook_h"));

    union() {
        // Beam: lower part set back by undercut (room for the hook).
        translate([0, -beam_t / 2 + undercut, 0])
            cube([beam_w, beam_t - undercut, beam_l]);
        // Hook: top part across the full beam_t.
        translate([0, -beam_t / 2, beam_l - hook_h])
            cube([beam_w, beam_t, hook_h]);
    }
}

// --- bbox and declaration helpers (must match gen/emit_part.py) -------------

function kit_bbox_snap_hook(beam_l, beam_w, beam_t, hook_h, undercut) =
    [beam_w, beam_t, beam_l];

function kit_through_holes_snap_hook() = 0;
