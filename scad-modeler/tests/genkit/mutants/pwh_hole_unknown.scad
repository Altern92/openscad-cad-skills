// mutacinis testas: pwh_hole_unknown
include </Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit/kit/lib.scad>
include </Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit/kit/plate_with_holes.scad>

$fn = 64;
kit_plate_with_holes(w = 80, d = 50, t = 6, hole = "M7", inset = 8);
