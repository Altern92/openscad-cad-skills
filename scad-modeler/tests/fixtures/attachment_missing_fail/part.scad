// Direct reproduction of INCIDENTS.md 2026-09-11 ("side panels: (a) no
// fastening at all"): a side panel that shipped as a bare plate with zero
// attachment features. It passes connectivity (one solid) and dimensions
// (exactly the declared size) while being impossible to fasten to anything.
//
// The declared attachment point sits where the M3 boss belongs -- 4.5mm out
// from the panel face -- and falls in empty air, because the boss was removed
// "to make the assembly fit" and never restored.

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [3, 60, 40]

// the panel itself: thin plate at x=0
cube([3, 60, 40], center = true);

// NOTE: no boss here. [4.5, 20, 15] is 3mm clear of the panel face, in air.
