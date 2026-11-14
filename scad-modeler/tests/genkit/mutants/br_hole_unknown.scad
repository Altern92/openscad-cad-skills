// mutation test: br_hole_unknown
include <../../../kit/lib.scad>
include <../../../kit/bracket_l.scad>

$fn = 64;
kit_bracket_l(w = 60, d = 50, h = 40, t = 4, hole = "M7");
