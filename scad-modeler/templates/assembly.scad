// assembly.scad — TEMPLATE. Copy to <project>/scad/assembly.scad.
//
// WHY THIS FILE EXISTS
// --------------------
// validate_scad.sh renders every parts/*.scad and then, to run the collision
// checks, renders each part AGAIN positioned in assembly coordinates with
//     openscad -D 'MODE="part"' -D 'PART="<name>"' assembly.scad
//
// That only works if this file GUARDS its own defaults:
//
//     MODE = is_undef(MODE) ? "assembly" : MODE;
//
// A plain `MODE = 1;` (or MODE = "assembly";) REASSIGNS the variable and
// silently defeats -D, so every "part" render produces the WHOLE ASSEMBLY.
// Measured on server_rack_modular_v4 (2026-09-12): 17 positioned STLs of
// ~12.5MB each, and check_collisions.py then reported "penetration depth
// 170.000 mm" for all 136 pairs — 136 meaningless collisions out of 17
// identical copies. validate_scad.sh now trips on this and refuses to run the
// collision checks, but the fix is here, not there.
//
// ALSO: use <...>, never include <...>, for part files. Every part file ends
// with an unconditional top-level call to its own module (that is what makes
// it render standalone; see templates/part_template.scad). `include` runs
// that call too, so the part renders once at the origin AND once at its
// at() position — silently doubling its geometry. `use` imports the module
// without executing the top level.

include <layout.scad>

// One line per PRINTED part. Keep the order identical to layout.scad's table.
use <parts/panel.scad>
use <parts/frame_module.scad>
use <parts/bracket.scad>

// --- Modes. Guarded, so -D can override. Both lines are mandatory. ---------
MODE = is_undef(MODE) ? "assembly" : MODE;  // assembly | part | exploded
PART = is_undef(PART) ? "" : PART;

// Modules are not values in OpenSCAD, so PART needs an explicit name dispatch:
// there is no way to look a module up by string and call it.
module part_by_name(name) {
    if (name == "panel") panel();
    else if (name == "frame_module") frame_module();
    else if (name == "bracket") bracket();
    else assert(false, str(
        "Unknown part '", name, "'. full_assembly() below and parts/*.scad ",
        "basenames must agree with layout.scad's part names and this dispatch."
    ));
}

module full_assembly() {
    at("panel")        panel();
    at("frame_module") frame_module();
    at("bracket")      bracket();
}

if (MODE == "assembly") {
    full_assembly();
    // BOM: part name, material, quantity.
    echo(str("BOM panel x1; frame_module x1; bracket x2"));
} else if (MODE == "part") {
    // Used by validate_scad.sh for the collision checks. Must render EXACTLY
    // one part, positioned — not the whole assembly.
    at(PART) part_by_name(PART);
} else if (MODE == "exploded") {
    // Same parts, each offset along its natural axis, so a human can see the
    // stack. Keep every offset a multiple of a parameter, never a magic number.
    full_assembly();
}
