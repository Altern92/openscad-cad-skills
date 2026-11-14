// examples/all_modules.scad — all 8 kit v0 modules in one render.
//
// This is a PREVIEW_FILE: a view, not a printable part. So the gates
// do not check connectivity/bbox (see the PREVIEW_FILE branch in validate_scad.sh).
// Each module is called with its own fixture parameters, laid out
// in a row so the render can be checked visually.

// PREVIEW_FILE

include <../../kit/lib.scad>
include <../../kit/plate.scad>
include <../../kit/plate_with_holes.scad>
include <../../kit/bracket_l.scad>
include <../../kit/box.scad>
include <../../kit/lid.scad>
include <../../kit/boss.scad>
include <../../kit/hole_pattern.scad>
include <../../kit/snap_hook.scad>

$fn = 64;

// 1. plate 120×80×6, R8
translate([0, 0, 0])
    kit_plate(w = 120, d = 80, t = 6, corner_r = 8);

// 2. plate_with_holes 80×50×6, M4, inset 8, R5
translate([160, 0, 0])
    kit_plate_with_holes(w = 80, d = 50, t = 6, hole = "M4", inset = 8, corner_r = 5);

// 3. bracket_l
translate([280, 0, 0])
    kit_bracket_l(w = 60, d = 40, h = 50, t = 4, hole = "M4");

// 4. box 120×80×40
translate([0, 120, 0])
    kit_box(w = 120, d = 80, h = 40, wall = 2.4, floor = 2.4, corner_r = 6);

// 5. lid 120×80 (t 3, lip 1.8)
translate([160, 120, 0])
    kit_lid(w = 120, d = 80, t = 3, lip = 1.8, clearance = 0.2, wall = 2.4);

// 6. boss Ø24, bore Ø12, h 12
translate([320, 120, 0])
    kit_boss(d_out = 24, d_bore = 12, h = 12);

// 7. hole_pattern 3×2, M3
translate([0, 240, 0])
    kit_hole_pattern(nx = 3, ny = 2, dx = 30, dy = 25, hole = "M3", t = 6);

// 8. snap_hook
translate([160, 240, 0])
    kit_snap_hook(beam_l = 20, beam_w = 8, beam_t = 2, hook_h = 1.5, undercut = 0.5);
