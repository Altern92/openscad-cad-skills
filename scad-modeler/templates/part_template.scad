// RAG-passport: file=templates/part_template.scad | skill=scad-modeler | applies_to=[part-file, local-coordinates, EXPECTED_BBOX, EXPECTED_HOLE, trailing-call] | units=mm | version=2026-09-11 | source=06_RAG_taisykles (T2) | kind=TEMPLATE (copy into project, do not edit here)
// ============================================================
// <part_name>.scad
// Local origin: <state the exact datum, e.g. "center of the bearing bore,
//                bore axis = Z" or "bottom face that mounts to the chassis">
// Material: <e.g. PETG>
// Print orientation: <e.g. flat face down, no supports needed>
// EXPECTED_BBOX: [40, 20, 15]   // update to match part_length/width/height below --
//                                 validate_scad.sh checks the rendered STL against
//                                 this automatically; delete the line to skip
//                                 (e.g. for an odd shape where a bbox isn't meaningful)
// EXPECTED_HOLE: [0, 0, 0, "Z", 8.0]  // one line per fit-critical bore: a point on
//                                 its axis, the axis, and the target across-flats
//                                 diameter. A bbox cannot see a bore that's too
//                                 tight; this measures it. Delete if the part has
//                                 no fit-critical round features.
// A single printed part must render as ONE connected body by default --
// validate_scad.sh checks this automatically (check_connectivity.py), no
// declaration needed. Only add EXPECTED_BODIES if this file is genuinely,
// deliberately more than one disconnected solid (rare):
// EXPECTED_BODIES: 2   // delete this line unless that's really true
// ============================================================

include <../params.scad>
include <BOSL2/std.scad>   // MUST be `include`, not `use` -- see setup-notes.md
                            // (delete this line if the part doesn't use BOSL2 attach/anchors)

// ------------------------------------------------------------
// Local dimensions (part-specific only -- shared/derived values
// belong in params.scad, not re-declared here)
// ------------------------------------------------------------
part_length = 40;
part_width = 20;
part_height = 15;
wall = 3;

// ------------------------------------------------------------
// Geometry module -- local coordinates only.
// Do NOT translate()/rotate() the whole part here -- that's
// layout.scad's job via at("<part_name>") in assembly.scad.
// ------------------------------------------------------------
// Example sub-features -- delete both (plus the SUBFEATURES: line and the two
// dispatch entries above) if this part has no internal sub-feature sharing its
// union(). As written they overlap slightly, so the overlap check has
// something to say when the template is used untouched.
module tower_main() {
    cuboid([10, 10, part_height]);
}

module motor_cradle() {
    translate([0, 0, part_height / 2]) cuboid([14, 6, 6]);
}

module part_geometry() {
    difference() {
        cuboid([part_length, part_width, part_height]) {
            // Example: a boss on the top face via BOSL2 attach --
            // delete this block if the part doesn't need it.
            // attach(TOP) cyl(h=8, d=10, anchor=BOTTOM);
        }
        // Cutouts (holes, pockets, ...) go here.
    }
}

// Always render unconditionally when this file runs standalone --
// $preview is the only real OpenSCAD mode flag (true in F5/quick-preview,
// false in F6/full render); there is no separate "$render" variable.
// ------------------------------------------------------------
// Named sub-features, for the overlap check.
//
// check_subfeature_overlap.py compares sub-features of ONE printed part
// against each other BEFORE union(). Once union()ed and exported the overlap
// is invisible: union() of two overlapping solids is still one valid,
// watertight, single-body shell, so check_collisions.py (separate STLs only)
// and check_connectivity.py both stay clean. Real incident (INCIDENTS.md
// 2026-08-19): a bearing tower overlapped an unrelated motor-mounting cradle
// inside the same part by 419mm3 and survived several rounds of green
// validation.
//
// List every sub-feature sharing this part's union() below, and give each one
// its own module. validate_scad.sh renders each SOLO (through the SUBFEATURE
// switch) and runs the overlap check on the set. Fewer than two names =
// nothing to compare = the check is skipped, so list them only when they
// genuinely share one union(); sub-features that are already separate printed
// parts belong in layout.scad instead.
//
// SUBFEATURES: tower_main, motor_cradle
//
// The switch is guarded exactly like assembly.scad's MODE/PART: a plain
// SUBFEATURE = something; would reassign the variable and silently defeat -D.
SUBFEATURE = is_undef(SUBFEATURE) ? "" : SUBFEATURE;

module subfeature_by_name(name) {
    if (name == "tower_main") tower_main();
    else if (name == "motor_cradle") motor_cradle();
    else assert(false, str(
        "Unknown sub-feature '", name, "' in this part file. The name must ",
        "match both its module here and the // SUBFEATURES: line above."
    ));
}

if (SUBFEATURE != "") subfeature_by_name(SUBFEATURE);
else part_geometry();
