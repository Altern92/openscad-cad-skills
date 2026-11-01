// Repro INCIDENTS.md 2026-09-04: beam default 211 vs computed 216.5.
module beam(len = 211, w = 10) { cube([len, w, w]); }
beam();
