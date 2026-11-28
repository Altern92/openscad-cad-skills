// Purchased-part envelopes (P28, 2026-11-28) for collision / fastener checks, used like a NopSCADlib
// vitamin (references/hardware.md). Only numbers with a source are built in; a value no source gives
// (marked ◇ below) has no default: the caller passes the measured value, or the module refuses.
// Every envelope is an outer bound, not a detailed model: round parts are circumscribed polygons
// (a plain cylinder() is inscribed and would be up to 2 % too small at $fn = 48).
ENV_FN = 48;
module env_cyl(d, h, center = false) { rotate([0, 0, 180 / ENV_FN]) cylinder(d = d / cos(180 / ENV_FN), h = h, center = center, $fn = ENV_FN); }

// TowerPro MG996R servo. Overall 40.7 x 19.7 x 42.9 mm (L x W x H incl. output spline), 55 g:
// HobbyKing / Core Electronics listings and datasheet mirrors (datasheetcafe.com/mg996r-datasheet-digital-servo),
// read 2026-11-28. Clones vary (counterfeits common): measure yours if the fit is tight.
MG996R = [40.7, 19.7, 42.9];
// Mounting tabs: spacing, width, thickness and height above the base are not in those sources (◇;
// commonly quoted 49.5 x 10 mm hole pattern is unverified) -> pass all four or get no tabs.
module mg996r(tab_span = undef, tab_w = undef, tab_t = undef, tab_z = undef) {
    translate([-MG996R[0] / 2, -MG996R[1] / 2, 0]) cube(MG996R);
    tabs = [tab_span, tab_w, tab_t, tab_z];
    if (len([for (v = tabs) if (!is_undef(v)) v]) > 0) {
        assert(len([for (v = tabs) if (is_num(v) && v > 0) v]) == 4,
               "mg996r: tab_span, tab_w, tab_t, tab_z are not published (◇): measure and pass all four");
        assert(tab_span > MG996R[0], "mg996r: tab_span must exceed the 40.7 mm body");
        translate([-tab_span / 2, -tab_w / 2, tab_z]) cube([tab_span, tab_w, tab_t]);
    }
}

// INJORA 80 mm dual-rate oil shock (1/10 crawler): 80 mm eye to eye extended, 62 mm compressed,
// 18 mm travel. Source: bigsquidrc.com/injora-80-120mm-dual-rate-shocks-for-1-10-scale-crawlers
// (read 2026-11-28); a buyer reported a pair labelled 80 mm measuring 90 mm, so measure yours.
// Body / spring diameter and eye size are not published (◇): body_d must be passed.
INJORA_80 = [80, 62, 18];   // extended, compressed, travel
module injora_shock80(travel_used = 0, body_d = undef) {
    assert(is_num(body_d) && body_d > 0, "injora_shock80: body_d (spring OD) is not published (◇): measure and pass it");
    assert(travel_used >= 0 && travel_used <= INJORA_80[2], str("injora_shock80: travel_used ", travel_used,
           " outside 0..", INJORA_80[2], " mm (bottoms out / tops out)"));
    env_cyl(body_d, INJORA_80[0] - travel_used);   // eye centre to eye centre along +Z
}

// RC4WD Z-S0398 rod end (front_axle_v4 ball joints). RC4WD publishes neither its dimensions nor its
// swing angle (the rod-ends PDF "angle of bend" is the bent shank, checked 2026-11-18): every number ◇.
// The module exists so the part is modelled (INC-2026-11-18-01: unmodelled rod ends hid a floating axle),
// with the caller's measured envelope.
module rc4wd_z_s0398(length = undef, head_d = undef, head_t = undef) {
    assert(is_num(length) && is_num(head_d) && is_num(head_t) && length > head_d / 2,
           "rc4wd_z_s0398: no published dimensions (◇): measure length, head_d, head_t and pass them");
    env_cyl(head_d, head_t, center = true);
    rotate([0, 90, 0]) env_cyl(head_t, length);
}

PART = is_undef(PART) ? "" : PART;   // -D PART=... renders one for the fixture
if (PART == "mg996r") mg996r();
if (PART == "mg996r_tabs") mg996r(tab_span = 54, tab_w = 18, tab_t = 2.5, tab_z = 26);
if (PART == "mg996r_half_tabs") mg996r(tab_span = 54);
if (PART == "shock") injora_shock80(travel_used = is_undef(T) ? 0 : T, body_d = is_undef(BD) ? undef : BD);
if (PART == "rod_end") rc4wd_z_s0398();
