// All dimensions for the assembly live here -- nothing in a part file
// should be a bare number that isn't either a local cosmetic detail or
// traceable back to this file (SKILL.md §2).
$fa = 2; $fs = 0.3;
global_clearance = 0.2; // mm, general running clearance

gear_module   = 1.0;   // mm, module shared by both gears (must match to mesh)
pinion_teeth  = 11;
spur_teeth    = 66;
gear_thickness = 8;    // mm
shaft_d       = 5;     // mm, both gears bore to this

ratio = spur_teeth / pinion_teeth;
center_distance = gear_module * (pinion_teeth + spur_teeth) / 2;

assert(ratio > 5.5 && ratio < 6.5, "reduction ratio drifted from target ~6:1");
assert(shaft_d < gear_module * pinion_teeth * 0.5,
       "shaft bore too large for the pinion's own pitch diameter");
