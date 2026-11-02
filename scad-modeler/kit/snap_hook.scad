// kit/snap_hook.scad — kablys su spyruokline sija (P1).
//
// Lokali pradžia: tvirtinimo pagrindo centras. bbox = [beam_w, beam_t, beam_l].
// Sija stovi išilgai Z; kablys — viršutinėje dalyje, atšoka per `undercut`.
// Sijos apatinė dalis atitraukta per `undercut`, kad kablys tilptų į
// deklaruojamą bbox (Y ≤ beam_t).

include <lib.scad>

module kit_snap_hook(beam_l, beam_w, beam_t, hook_h, undercut) {
    assert(beam_t >= 1.2,
        str("KLAIDA: sija ", kit_fmt(beam_t), " mm → ", kit_fmt(beam_t), " < ",
            kit_fmt(1.2), " mm → didink beam_t iki ", kit_fmt(1.2)));
    assert(undercut <= 0.3 * beam_t,
        str("KLAIDA: undercut ", kit_fmt(undercut), " mm → ", kit_fmt(undercut), " > ",
            kit_fmt(0.3 * beam_t), " (30 % sijos) → mažink undercut iki ",
            kit_fmt(0.3 * beam_t), " arba didink beam_t"));
    assert(hook_h >= undercut + 0.5,
        str("KLAIDA: hook_h ", kit_fmt(hook_h), " mm → ", kit_fmt(hook_h), " < undercut + 0.5 = ",
            kit_fmt(undercut + 0.5), " mm → didink hook_h iki ", kit_fmt(undercut + 0.5)));
    assert(beam_l >= 4 * beam_t,
        str("KLAIDA: sija per trumpa ", kit_fmt(beam_l), " mm → ", kit_fmt(beam_l), " < 4×",
            kit_fmt(beam_t), " = ", kit_fmt(4 * beam_t),
            " mm → neturės spyruokliškumo; didink beam_l"));
    assert(hook_h < beam_l,
        str("KLAIDA: hook_h ", kit_fmt(hook_h), " mm → ", kit_fmt(hook_h), " ≥ beam_l=",
            kit_fmt(beam_l), " mm → didink beam_l arba mažink hook_h"));

    union() {
        // Sija: apatinė dalis atitraukta per undercut (kabliui vietos).
        translate([0, -beam_t / 2 + undercut, 0])
            cube([beam_w, beam_t - undercut, beam_l]);
        // Kablys: viršutinė dalis per visą beam_t.
        translate([0, -beam_t / 2, beam_l - hook_h])
            cube([beam_w, beam_t, hook_h]);
    }
}

// --- bbox ir deklaracijų pagalbinės (turi sutapti su gen/emit_part.py) ------

function kit_bbox_snap_hook(beam_l, beam_w, beam_t, hook_h, undercut) =
    [beam_w, beam_t, beam_l];

function kit_through_holes_snap_hook() = 0;
