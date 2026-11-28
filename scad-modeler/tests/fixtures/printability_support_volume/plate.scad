// mushroom: post r5 h10 + flat disk r15 h2 on top. Support = annulus pi*(15^2-5^2)=628.3 * 10 = 6283 mm^3.
$fn = 96;
cylinder(h = 10, r = 5);
translate([0,0,10]) cylinder(h = 2, r = 15);
