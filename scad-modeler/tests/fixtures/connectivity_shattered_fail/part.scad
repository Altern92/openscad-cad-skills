// Reproduction of a real CADAM model defect found by testbase_cadam (2026-09-12):
// benchmarks/02-knurled-control-knob.scad renders to 155920 triangles that split
// into 3122 disconnected components -- a knurled pattern whose elements never
// merged with the body they decorate. It LOOKS right in a render (the slivers
// are 0.03mm and invisible), is not a solid, and the old checker reported
// "2 disconnected bodies" for it while printing all 3122, so the suggested
// EXPECTED_BODIES: 2 was wrong too.
//
// Deliberately NO "// EXPECTED_BODIES:" -- a single printed part splitting into
// hundreds of islands is an error by default.

$fa = 6; $fs = 2;

// the body the knurl is supposed to decorate
cylinder(r = 10, h = 5);

// the "knurl": tiny detached blocks at a radius that never touches the body.
// 60 angles * 4 heights = 240 islands, all far more than MAX_BODIES_SHOWN,
// so this also exercises the capped listing.
for (a = [0 : 6 : 354])
    for (z = [0 : 2 : 6])
        rotate([0, 0, a]) translate([14, 0, z]) cube([0.6, 0.6, 0.6], center = true);
