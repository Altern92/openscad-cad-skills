// 40 mm long ramp rising 7.05 mm (10 deg from horizontal), up-facing: stair stepping.
rotate([90,0,0]) linear_extrude(20) polygon([[0,0],[40,0],[40,2+40*tan(10)],[0,2]]);
