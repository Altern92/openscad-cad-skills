// 20 mm block with a 30 deg V groove (5 mm deep) cut in the top: the groove bottom is a sharp
// CONCAVE edge, which is not a knife; every convex edge is >= 90 deg.
difference() {
  cube([20,20,20]);
  translate([0,20,20.01]) rotate([90,0,0]) linear_extrude(20) polygon([[10,-5],[10-5.01*tan(15),0.01],[10+5.01*tan(15),0.01]]);
}
