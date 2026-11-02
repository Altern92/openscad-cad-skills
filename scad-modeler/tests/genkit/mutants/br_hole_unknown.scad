// mutacinis testas: br_hole_unknown
include </Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit/kit/lib.scad>
include </Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit/kit/bracket_l.scad>

$fn = 64;
kit_bracket_l(w = 60, d = 50, h = 40, t = 4, hole = "M7");
