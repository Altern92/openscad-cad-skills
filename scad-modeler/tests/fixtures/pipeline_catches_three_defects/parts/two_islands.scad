// DEFECT 1 -- a single printed part that renders as two disconnected solids.
// Reproduces INCIDENTS.md 2026-08-19 (a leg-radius fix for one collision broke
// the legs' contact with the disc they were supposed to hold up).
include <../params.scad>
// EXPECTED_BBOX: [50, 10, 10]
cube([10, 10, 10], center = true);
translate([40, 0, 0]) cube([10, 10, 10], center = true);
