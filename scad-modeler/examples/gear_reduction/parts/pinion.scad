// Pinion (driver gear). Local origin: its own axis, centered on thickness.
// Size and bore declarations below (P15): the bore is measured flat-to-flat.
// NO_RETENTION: a bare gear pair -- the shafts and frame that hold it are outside this example
include <../params.scad>
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

// EXPECTED_HOLE: [0, 0, 0, "Z", 5.0]
// EXPECTED_BBOX: [13.442, 13.58, 8]   // z = gear_thickness; x/y = tooth tips, measured (BOSL2 2.0.750, gear_spin -90)
// EXPECTED_THROUGH_HOLES: 1   // the shaft bore
// SENSITIVE_TO: gear_thickness
module pinion() {
    spur_gear(mod=gear_module, teeth=pinion_teeth, thickness=gear_thickness,
               shaft_diam=shaft_d, pressure_angle=20, backlash=0.15, gear_spin=pinion_spin);
}
pinion();
