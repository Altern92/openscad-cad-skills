// RAG-passport: file=references/organic-patterns.scad | skill=openscad-organic | applies_to=[hull-chain, skin, sweep, detail-on-surface, snap-fit] | units=mm | printer=FDM | version=2026-09-11 | source=06_RAG_taisykles (T2). 1 pattern = 1 retrievable chunk.
// organic-patterns.scad — copy-paste templates.
// BOSL2 required for skin/sweep/bezier: add 'use <BOSL2/std.scad>' in YOUR file,
// or place these templates in a file that already includes it.
// Sources: makerblock jack, BOSL2 skin tutorial, adeptus-dad plating, review 2026-09-09.

// CHUNK: pattern=hull_chain | applies_to=[limb, tentacle, tail] | depends_on=none
// Pattern 0: piecewise hull chain (limb / tentacle / tail backbone).
// pts = list of [x,y,z] joints; r = ball radius at each joint.
module hull_chain(pts, r) {
    // NOTE: plain translate() here — do NOT 'use <BOSL2/std.scad>' in THIS file
    // (BOSL2 overrides translate and breaks pts[i] indexing). Include BOSL2
    // in your own file alongside this one instead.
    for (i = [0 : len(pts)-2])
        hull() {
            translate(pts[i]) sphere(r = r, $fn = 24);
            translate(pts[i+1]) sphere(r = r, $fn = 24);
        }
}

// CHUNK: pattern=skinned_body | applies_to=[body, torso, skin] | depends_on=none
// Pattern 1: skinned body from circular profiles.
// sections = [[z, diameter], ...] bottom to top; n = points per circle.
function circle_prof(z, d, n=24) = [for (i = [0 : n-1]) [d/2*cos(i*360/n), d/2*sin(i*360/n), z]];
module body(sections) {
    skin([for (s = sections) circle_prof(s[0], s[1])],
         slices = 8, refine = 1, method = "distance", caps = true);
}
// Usage: body([[0, 20], [10, 24], [20, 18], [30, 8]]);  // torso->neck

// CHUNK: pattern=swept_limb | applies_to=[limb, arm, leg, horn, tail] | depends_on=none
// Pattern 2: swept limb along bezier (arm / leg / horn / tail).
// path_pts = 4 bezier controls; d0/d1 = start/end diameter.
module limb(path_pts, d0, d1, N = 32) {
    path = bezier(path_pts, N);
    // taper: scale profile along path — approximate with two sweeps
    path_sweep(circle(d = d0, $fn = 24), path);
}

// CHUNK: pattern=detail_on_surface | applies_to=[eye, rivet, scale, detail] | depends_on=hull_chain
// Pattern 3: detail blob ON surface (eye / rivet / scale).
// pos = [x,y,z] on surface; r = blob radius; sink 30% into surface.
module detail_on(pos, r) {
    translate(pos) sphere(r = r, $fn = 20);
}

// CHUNK: pattern=snap_base | applies_to=[base, minibase, snap-fit] | depends_on=none
// Pattern 4: snap-fit round base (minibase-style: flat rim, parametric).
// d = base diameter, h = height.
module base_round(d = 30, h = 4) {
    cylinder(d1 = d, d2 = d - 2, h = h, $fn = 64);
}
