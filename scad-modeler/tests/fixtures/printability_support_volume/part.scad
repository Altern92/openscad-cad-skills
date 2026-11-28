// same mushroom raised on a wider pad r20 h3: column ends on the pad top (drop 8), 628.3*8 = 5027 mm^3.
$fn = 96;
cylinder(h = 3, r = 20);
cylinder(h = 13, r = 5);
translate([0,0,11]) cylinder(h = 2, r = 15);
