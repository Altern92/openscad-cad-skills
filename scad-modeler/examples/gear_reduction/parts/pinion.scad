// Pinion (driver gear). Local origin: its own axis, centered on thickness.
// EXPECTED_BBOX and EXPECTED_THROUGH_HOLES are required (P15); EXPECTED_HOLE measures the
// bore flat-to-flat -- see check_dimensions.py / check_topology.py / check_features.py.
include <../params.scad>
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

// EXPECTED_HOLE: [0, 0, 0, "Z", 5.0]
// EXPECTED_BBOX: [13.58, 13.442, 8]   // z = gear_thickness; x/y = tooth tips, measured (BOSL2 2.0.750)
// EXPECTED_THROUGH_HOLES: 1   // the shaft bore
// SENSITIVE_TO: gear_thickness
module pinion() {
    spur_gear(mod=gear_module, teeth=pinion_teeth, thickness=gear_thickness,
               shaft_diam=shaft_d, pressure_angle=20, backlash=0.15);
}
pinion();
