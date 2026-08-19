// Driven gear (spur). Local origin: its own axis, centered on thickness.
include <../params.scad>
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

// EXPECTED_HOLE: [0, 0, 0, "Z", 5.0]
module spur() {
    spur_gear(mod=gear_module, teeth=spur_teeth, thickness=gear_thickness,
               shaft_diam=shaft_d, pressure_angle=20, backlash=0.15);
}
spur();
