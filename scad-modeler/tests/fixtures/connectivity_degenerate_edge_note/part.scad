// A near-tangent boolean leaves a sub-micron edge, and that sliver silently
// poisons every ray-based measurement taken on the mesh afterwards.
//
// Reproduction of a real part (server_rack_modular/scad/parts/frame_module.scad,
// measured 2026-09-12): watertight, ONE connected body, every volume-based
// check clean -- and a shortest edge of 0.000028 mm. check_printability.py read
// a "0.014 mm wall" off it and reported FAIL, 30x below anything the model
// declares. The same run on base.stl (healthy mesh, shortest edge 0.296 mm)
// reads a min wall of 0.252 mm, which matches its geometry.
//
// The 0.0005 mm offset below is what makes the difference: the cutter is
// effectively tangent, so the boolean leaves a crescent a fraction of a micron
// wide instead of a clean wall. Nothing looks wrong in the render.

$fa = 2; $fs = 0.3;

difference() {
    cylinder(r = 10, h = 20, $fn = 180);
    translate([0.0005, 0, 0]) cylinder(r = 10, h = 25, $fn = 180);
}
