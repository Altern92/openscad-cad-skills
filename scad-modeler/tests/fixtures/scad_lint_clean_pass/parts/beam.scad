module beam(len = 211) { cube([len, 10, 10]); }
module rail(len = undef) { assert(len != undef, "len required"); cube([len, 5, 5]); }
beam(len = 211);
module post(h = 88.9) { cube([18, 18, h]); }   // numeric default, but every caller passes h
post(h = 2 * 44.45);
