// All dimensions for the assembly live here -- nothing in a part file
// should be a bare number that isn't either a local cosmetic detail or
// traceable back to this file (SKILL.md §2).
include <BOSL2/std.scad>   // gear_dist() below; including BOSL2 twice is harmless
include <BOSL2/gears.scad>
$fa = 2; $fs = 0.3;
global_clearance = 0.2; // mm, general running clearance

gear_module   = 1.0;   // mm, module shared by both gears (must match to mesh)
pinion_teeth  = 11;
spur_teeth    = 66;
gear_thickness = 8;    // mm
shaft_d       = 5;     // mm, both gears bore to this

ratio = spur_teeth / pinion_teeth;
// NOT m*(z1+z2)/2 = 38.5: BOSL2 gives the 11T pinion an automatic profile shift (0.357), which
// pushes the gears apart to 38.845 mm. 38.5 jammed the teeth (P29, 2026-11-27).
center_distance = gear_dist(mod=gear_module, teeth1=pinion_teeth, teeth2=spur_teeth, pressure_angle=20);
// Phase: BOSL2 puts a tooth on +Y. Turned -90 the pinion points a tooth at the spur; the even 66T spur
// needs half a pitch more so a gap faces it.
pinion_spin = -90;
spur_spin = -90 + 180 / spur_teeth;

assert(ratio > 5.5 && ratio < 6.5, "reduction ratio drifted from target ~6:1");
assert(shaft_d < gear_module * pinion_teeth * 0.5,
       "shaft bore too large for the pinion's own pitch diameter");
