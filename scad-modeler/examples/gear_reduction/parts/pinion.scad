// Pinion (driver gear). Local origin: its own axis, centered on thickness.
// // EXPECTED_BBOX and // EXPECTED_HOLE opt this part into automated
// dimensional/bore checks -- see check_dimensions.py / check_features.py.
include <../params.scad>
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

// EXPECTED_HOLE: [0, 0, 0, "Z", 5.0]
module pinion() {
    spur_gear(mod=gear_module, teeth=pinion_teeth, thickness=gear_thickness,
               shaft_diam=shaft_d, pressure_angle=20, backlash=0.15);
}
pinion();
