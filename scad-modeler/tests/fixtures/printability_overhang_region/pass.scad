// Three things that must NOT fail the 45 deg limit:
//  1. a true 45 deg cone;
//  2. a wedge whose underside is 45.5 deg from vertical: 0.5 deg past the limit, inside the 1 deg
//     facet tolerance (tessellation / STL rounding noise);
//  3. a 0.5 x 0.5 mm nub whose 0.25 mm^2 underside is below the 1 mm^2 region floor.
$fn = 48;
cylinder(h = 10, r1 = 10, r2 = 20);
translate([40, 0, 0]) rotate([90, 0, 0]) linear_extrude(20) polygon([[10.17, 0], [30, 0], [30, 10], [0, 10]]);
translate([80, 0, 0]) cube([10, 10, 10]);
translate([89.8, 0, 4]) cube([0.7, 0.5, 1]);
