// ============================================================
// patterns.scad -- reusable OpenSCAD snippets pulled from real, tested
// parts in this project set (not written from scratch here). Each pattern
// below cites the project it was first solved in. This is a reference
// library, not a standalone model -- `use <patterns.scad>` the specific
// module(s) you need rather than rendering this file directly (it has
// deliberately no unconditional trailing call).
// ============================================================


// ------------------------------------------------------------
// PATTERN 0: circular-hole tessellation compensation
// Source: derived from OpenSCAD's own facet math, not from a project --
// see references/tolerances.md for the error-layer explanation.
//
// OpenSCAD builds circles as regular polygons whose vertices sit ON the ideal
// circle (inscribed). A shaft entering a hole binds on the polygon's apothem
// a = r*cos(180/n), not on r -- so EVERY modelled hole is undersized
// flat-to-flat by r*(1 - cos(180/n)) per side, before the printer contributes
// anything at all.
//
// This is a pure geometry error and it is exactly correctable. It is NOT the
// printer's hole bias -- that is a separate layer and belongs in a calibration
// profile. Applying both to the same hole double-counts; keep them separate:
//     tessellation  -> corrected here
//     process bias  -> corrected by the calibration value you add to d_target
//
// APPLY TO HOLES, NOT TO PINS. For an external cylinder the polygon's vertices
// are the widest points, so a pin already measures its nominal diameter across
// corners -- enlarging it would make the fit tighter, not looser.
//
// Usage:
//   difference() {
//       cube([20, 20, 10]);
//       translate([10, 10, -1]) cylinder(d = true_hole_d(8.2), h = 12);
//   }
//   // or, equivalently:
//   translate([10, 10, -1]) true_hole(d = 8.2, h = 12);
// ------------------------------------------------------------

// Facet count for a circle of radius r -- mirrors OpenSCAD's own fragment
// calculation (verified against upstream source, 2026-08-18). $fn wins if set;
// otherwise the finer of the angle limit and the size limit applies, with a
// floor of 5. The r < GRID_FINE (2^-20) short-circuit to 3 is omitted here: it
// only fires below a micron of radius.
function scad_fragments(r) =
    ($fn > 0) ? max(3, floor($fn))
              : ceil(max(min(360 / $fa, r * 2 * PI / $fs), 5));

// Diametral undersize of a modelled hole of nominal diameter d, flat-to-flat.
function across_flats_deficit(d) =
    d * (1 - cos(180 / scad_fragments(d / 2)));

// Model diameter that yields d_target measured flat-to-flat. The facet count
// is taken at the target size; the resulting change in n is second-order and
// below the numeric floor at any practical size.
function true_hole_d(d_target) =
    d_target / cos(180 / scad_fragments(d_target / 2));

function true_hole_r(r_target) = true_hole_d(2 * r_target) / 2;

module true_hole(d, h, center = false) {
    cylinder(d = true_hole_d(d), h = h, center = center);
}


// ------------------------------------------------------------
// PATTERN 1: single rectangular locating pocket in a Gridfinity bin
// Source: gridfinity_hardware_storage_inserts/insert_B.scad (and C/D/F)
//
// Documented as a snippet, not a module here, on purpose: it's just the
// gridfinity-rebuilt-openscad library's own bin_render() + compartment_
// cutter(), and a wrapper module in THIS file can't call compartment_
// cutter() itself -- confirmed by testing: `use <patterns.scad>` only
// exposes patterns.scad's own module names to the caller, it does NOT
// give patterns.scad access to modules the caller separately use'd (e.g.
// cutouts.scad) -- OpenSCAD resolves a module's body against its own
// file's scope, not the caller's. See references/tolerances.md for the
// clearance value to use.
//
// Usage (inside your insert's own file, after use'ing the gridfinity
// library's utility/bin/cutouts modules and building `bin1` via new_bin()):
//   bin_render(bin1) {
//       compartment_cutter([item_w + 2*clearance, item_d + 2*clearance, pocket_depth],
//                           center_top=true);
//   }
// ------------------------------------------------------------


// ------------------------------------------------------------
// PATTERN 2: irregular-contour locating pocket in a Gridfinity bin
// Source: helping_hands_base_insert/helping_hands_base_insert.scad
//
// For an item whose footprint isn't a rectangle (traced/measured as a
// polygon outline) -- offsets the outline outward by `clearance`, extrudes
// it into a pocket, and centers it on the outline's own bounding-box
// center so it lands in the middle of the bin regardless of where the
// original points were measured from.
//
// `outline` = list of [x,y] points (any consistent origin -- the
// centering math below removes the original offset for you).
//
// Usage:
//   bin_render(bin1) {
//       gridfinity_contour_pocket(outline=base_outline, clearance=1.0, pocket_depth=13);
//   }
// ------------------------------------------------------------
module gridfinity_contour_pocket(outline, clearance, pocket_depth) {
    xs = [for (p = outline) p.x];
    ys = [for (p = outline) p.y];
    center = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2];

    translate([-center.x, -center.y, -pocket_depth])
    linear_extrude(pocket_depth)
    offset(r = clearance)
    polygon(outline);
}


// ------------------------------------------------------------
// PATTERN 3: friction-fit sleeve with a wire/cable exit slot
// Source: nema23_fan_shroud/nema23_fan_shroud.scad
//
// A rectangular sleeve that slides onto a rectangular body (a motor, a
// bracket) and grips it by friction alone -- see references/tolerances.md
// for the clearance/side to use, and its note on friction fits scaling
// with contact length/size. `notch_side` cuts a slot through one wall so
// a cable/wire can exit without being pinched.
//
// Usage:
//   difference() {
//       friction_sleeve(body_w=57, clearance=1, wall=2.5, sleeve_len=60);
//       sleeve_wire_notch(body_w=57, wall=2.5, sleeve_len=60,
//                          notch_side="right", notch_w=16, notch_h=9);
//   }
// ------------------------------------------------------------
module friction_sleeve(body_w, clearance, wall, sleeve_len) {
    inner = body_w + 2*clearance;
    outer = inner + 2*wall;
    difference() {
        cube([outer, outer, sleeve_len]);
        translate([wall, wall, -1])
            cube([inner, inner, sleeve_len + 2]);
    }
}

module sleeve_wire_notch(body_w, clearance, wall, sleeve_len, notch_side, notch_w, notch_h) {
    inner = body_w + 2*clearance;
    outer = inner + 2*wall;
    x = (notch_side == "right") ? outer - wall - 1 : -1;
    translate([x, (outer - notch_w)/2, -1])
        cube([wall + 2, notch_w, notch_h]);
}


// ------------------------------------------------------------
// PATTERN 4: bent duct / tube via segmented hull()
// Source: nema23_fan_shroud/nema23_fan_shroud.scad
//
// A smooth curved tube (e.g. a fan duct that has to bend around an
// obstruction) approximated as N short straight segments, each built by
// hull()-ing two circles at slightly different positions/rotations along
// the arc. This was genuinely non-obvious to derive correctly the first
// time (getting arc_pos/arc_rot wrong gives a duct that kinks or
// self-intersects instead of curving smoothly) -- reuse this rather than
// re-deriving it.
//
// The arc lies in the plane containing the bend axis; as written here it
// curves from "straight out along -X" toward "+Z" as angle increases (the
// original use case: a duct exiting a wall and curving toward the front
// of a motor). For a different bend plane/direction, adjust arc_pos/
// arc_rot's axes the same way you'd re-derive any parametric curve --
// don't just swap axis labels without re-checking in a render.
//
// Call twice to make a hollow duct: once with the outer diameter as a
// solid, once with the inner (air-path) diameter to subtract.
//
// Usage:
//   difference() {
//       bent_duct(start=[0, 32, 30], radius=45, bend_angle=40, d=61, segments=16);
//       bent_duct(start=[0, 32, 30], radius=45, bend_angle=40, d=56, segments=16);
//   }
// ------------------------------------------------------------
function _bent_duct_arc_pos(start, radius, a) =
    start + [-radius*sin(a), 0, radius*(1 - cos(a))];
function _bent_duct_arc_rot(a) = [0, -(90 + a), 0];

module bent_duct(start, radius, bend_angle, d, segments) {
    for (i = [0 : segments - 1]) {
        a1 = i * bend_angle / segments;
        a2 = (i + 1) * bend_angle / segments;
        hull() {
            translate(_bent_duct_arc_pos(start, radius, a1))
                rotate(_bent_duct_arc_rot(a1))
                cylinder(d=d, h=0.02, center=true, $fn=48);
            translate(_bent_duct_arc_pos(start, radius, a2))
                rotate(_bent_duct_arc_rot(a2))
                cylinder(d=d, h=0.02, center=true, $fn=48);
        }
    }
}
