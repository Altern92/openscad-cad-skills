module beam(len = 211) { cube([len, 10, 10]); }
module rail(len = undef) { assert(len != undef, "len required"); cube([len, 5, 5]); }
beam(len = 211);
module post(h = 88.9) { cube([18, 18, h]); }   // numeric default, but every caller passes h
post(h = 2 * 44.45);
// nas_post shape (server_rack v4): side = +/-1 is a mirror sign, not a dimension
module post2(side = 1) { mirror([side < 0 ? 1 : 0, 0, 0]) cube(5); }
post2();
