// Audit 2026-11-02 §5 #7: a 0.2 mm modelling error on a 180 mm part hides
// inside the derived tessellation bound at $fn=64 (~0.22 mm). The extents
// here are planes, so the real bbox error is 0 and the author declares a
// tight tolerance -- the 0.2 mm slip must now FAIL.
$fn = 64;

// EXPECTED_BBOX: [180, 60, 6]
// EXPECTED_BBOX_TOL: 0.01

// the bug: 179.8 instead of the declared 180
cube([179.8, 60, 6]);
