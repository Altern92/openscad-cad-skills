// Driven gear (spur). Local origin: its own axis, centered on thickness.
include <../params.scad>
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

// EXPECTED_HOLE: [0, 0, 0, "Z", 5.0]
// EXPECTED_BBOX: [67.95, 67.997, 8]   // z = gear_thickness; x/y = tooth tips, measured (BOSL2 2.0.750)
// EXPECTED_THROUGH_HOLES: 1   // the shaft bore
// SENSITIVE_TO: gear_thickness
module spur() {
    spur_gear(mod=gear_module, teeth=spur_teeth, thickness=gear_thickness,
               shaft_diam=shaft_d, pressure_angle=20, backlash=0.15);
}
spur();
