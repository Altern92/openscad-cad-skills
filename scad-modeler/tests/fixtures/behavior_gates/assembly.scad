// behavior_gates fixture: base on the ground, post on the base, arm swinging about the post top (A deg),
// a column the arm hits at A=45, a foot plate under the base (FOOT = its size). GAP lifts the arm off the post (the INC-2026-11-18-01 floating arm).
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
A = is_undef(A) ? 0 : A;
include <inc.scad>   // GAP0: the cache key must follow includes
GAP = is_undef(GAP) ? GAP0 : GAP;
FOOT = is_undef(FOOT) ? 40 : FOOT;
module base() difference() { cube([40, 40, 5]); translate([30, 30, 2]) cube(1); }   // a sealed void: not a loose piece
module post() translate([0, 0, 5]) cube([5, 5, 30]);
module arm() translate([2.5, 2.5, 35 + GAP]) rotate([0, 0, A]) translate([0, -2, 0]) cube([30, 4, 3]);
SINK = is_undef(SINK) ? 0 : SINK;   // audit A4: the column pushed SINK mm down, through the ground plane
module column() translate([15, 15, 5 - SINK]) cube([4, 4, 33 + SINK]);
module foot() translate([0, 0, -5]) cube([FOOT, FOOT, 5]);
STRAY = is_undef(STRAY) ? 0 : STRAY;   // a second piece of the post body, STRAY mm away from everything
CHAIN = is_undef(CHAIN) ? 0 : CHAIN;   // a piece 0.2 mm off the post: held through the post, not directly
module post_x() { post(); if (STRAY > 0) translate([60 + STRAY, 0, 0]) cube(3); if (CHAIN > 0) translate([-3.2, 0, 10]) cube(3); }
module part_by_name(n) {
    if (n == "base") base(); else if (n == "post") post_x(); else if (n == "arm") arm();
    else if (n == "column") column(); else if (n == "foot") foot();
    else assert(false, str("unknown part ", n));
}
if (MODE == "assembly") { base(); post(); arm(); column(); foot(); }
else part_by_name(PART);
