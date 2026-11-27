// behavior_multishell: an upright column with 4 cups and a body "balls" = 4 ball studs seated in them
// (P28 / AC-A1,A2). TOP moves the top ball TOP mm away from its cup (the 2026-11-20 report).
// "base" is a plain block for the joint-body echo case (AC-A3); this file prints no ECHO.
PART = is_undef(PART) ? "" : PART;
TOP = is_undef(TOP) ? 0 : TOP;
$fn = 24;
Z = [10, 25, 40, 55];
module upright() difference() { cube([10, 10, 60]); for (z = Z) translate([10, 5, z]) sphere(d = 6); }
module balls() for (i = [0:3]) translate([10 + (i == 3 ? TOP : 0), 5, Z[i]]) sphere(d = 5.8);
module base() cube([20, 20, 5]);
if (PART == "upright") upright(); else if (PART == "balls") balls(); else if (PART == "base") base();
