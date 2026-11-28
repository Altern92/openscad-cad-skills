// flat top + a 45 deg chamfer (steeper than 20 deg): no stair-step line.
rotate([90,0,0]) linear_extrude(20) polygon([[0,0],[30,0],[30,10],[20,20],[0,20]]);
