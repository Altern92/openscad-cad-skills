// Reproduction of the failure mode check_dimensions.py exists to catch:
// geometry that renders, compiles, and *looks* right but is the wrong size.
// Here the outer width comes from a hardcoded literal instead of the declared
// width parameter -- a units slip / parameter that didn't thread through.

$fa = 2; $fs = 0.3;

// EXPECTED_BBOX: [40, 20, 10]

declared_width = 40;   // the design intent, declared above

// the bug: the literal 30 is used instead of declared_width
cube([30, 20, 10]);
