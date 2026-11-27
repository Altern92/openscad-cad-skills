// 40 x 4 x 2 slab on two 0.3 mm posts under ONE end (x 0-2): a cantilever, not a 4 mm bridge.
translate([0, 0, 0.3]) cube([40, 4, 2]);
translate([0.2, 0.2, 0]) cube([1.8, 0.3, 0.4]);
translate([0.2, 3.5, 0]) cube([1.8, 0.3, 0.4]);
