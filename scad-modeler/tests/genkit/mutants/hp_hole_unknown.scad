// mutacinis testas: hp_hole_unknown
include </Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit/kit/lib.scad>
include </Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit/kit/hole_pattern.scad>

$fn = 64;
kit_hole_pattern(nx = 3, ny = 2, dx = 30, dy = 25, hole = "M7", t = 6);
