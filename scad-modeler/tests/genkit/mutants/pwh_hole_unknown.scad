// mutation test: pwh_hole_unknown
include <../../../kit/lib.scad>
include <../../../kit/plate_with_holes.scad>

$fn = 64;
kit_plate_with_holes(w = 80, d = 50, t = 6, hole = "M7", inset = 8);
