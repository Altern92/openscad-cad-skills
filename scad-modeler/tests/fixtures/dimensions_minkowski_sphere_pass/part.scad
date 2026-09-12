// A fillet made by minkowski() with a COARSE sphere renders measurably below
// its nominal size, and that is not a modelling error.
//
// Reproduction of server_rack_modular_v4/v8 parts/node.scad (measured
// 2026-09-12): minkowski() of a 23.5mm cube and sphere(r = 1.25, $fn = 24)
// declares EXPECTED_BBOX [26, 26, 26] and renders 25.9786 -- short by exactly
// 2*r*(1 - cos(pi/24)) = 0.0214 mm, because a 24-facet sphere does not reach
// its own radius in most directions.
//
// Before the minkowski-sphere term existed, bbox_error_bound() evaluated the
// shortfall at the PART's radius with the FILE's global $fn (180 fragments at
// $fa=2/$fs=0.3 -> 0.0040mm), the 0.005mm floor swallowed it, and this part
// FAILED by 0.0164mm. Declaring 25.9786 instead would be encoding a facets
// artefact into the design's own numbers.
//
// This fixture asserts the part PASSES. Its pair is dimensions_bbox_fail,
// which asserts a genuinely wrong size still FAILS -- widening the tolerance
// must not make that one pass.

$fa = 2; $fs = 0.3;
node_s = 26;
fillet = 2.5;

// EXPECTED_BBOX: [26, 26, 26]

translate([0, 0, 0])
    minkowski() {
        cube([node_s - fillet, node_s - fillet, node_s - fillet], center = true);
        sphere(r = fillet / 2, $fn = 24);
    }
