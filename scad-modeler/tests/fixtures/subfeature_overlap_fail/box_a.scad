// Proves check_subfeature_overlap.py catches overlap BETWEEN two named
// sub-modules inside one part -- invisible to check_collisions.py, which only
// ever compares separately-exported STLs against each other. Once two
// sub-modules are union()-ed and exported as one part they no longer exist as
// distinguishable objects, and union() of two overlapping solids is still one
// valid watertight shell.
//
// Reproduction of INCIDENTS.md 2026-08-19: a bearing tower overlapped an
// unrelated motor-mounting cradle in the same part by 419mm3, invisible through
// several rounds of "all green" validation.
//
// This is the solo export of sub-module A (pre-union, same local coordinates).

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [20, 20, 20]
cube([20, 20, 20]);
