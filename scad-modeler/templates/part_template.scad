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
part_geometry();
