// Same 60 x 20 footprint with r=3 rounded corners.
$fn = 32;
linear_extrude(10) offset(r = 3) offset(delta = -3) square([60, 20]);
