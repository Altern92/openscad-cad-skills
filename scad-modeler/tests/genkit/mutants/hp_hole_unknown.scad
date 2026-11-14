// mutation test: hp_hole_unknown
include <../../../kit/lib.scad>
include <../../../kit/hole_pattern.scad>

$fn = 64;
kit_hole_pattern(nx = 3, ny = 2, dx = 30, dy = 25, hole = "M7", t = 6);
