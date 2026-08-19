// Where each PART sits in the shared assembly coordinate system.
// Origin: pinion's own axis, on the base plate's top face. X = toward the
// spur gear's axis, Z = up.
include <params.scad>
// BOSL2 redefines translate()/rotate() to also track a $transform special
// variable (used internally by attachable()/spur_gear()); at()'s own
// translate()/rotate() calls below must be BOSL2's versions, not the plain
// builtins, or a part positioned through at() that itself uses a BOSL2
// module fails with "Ignoring unknown variable $transform" under
// --hardwarnings -- confirmed by hitting this directly (INCIDENTS.md,
// 2026-08-19). A module's translate()/rotate() binding is fixed at the
// scope where the module is DEFINED (here), not where it's called from, so
// this include has to live in this file, not just in the part files.
// BOSL2/std.scad does NOT itself include gears.scad (checked directly) --
// gears.scad declares $parent_gear_pa (and siblings) as undef at its own
// top level, which is what makes reading them elsewhere in the call chain
// not trigger "Ignoring unknown variable" under --hardwarnings. A part
// file's own `include <BOSL2/gears.scad>` does NOT help here either: `use`
// imports only modules/functions from a file, never its top-level variable
// assignments (confirmed earlier this session, references/setup-notes.md)
// -- and assembly.scad only `use`s the part files. Both includes are
// required, in this order (gears.scad's own header comment documents the
// same pair).
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

LAYOUT = [
    ["pinion", [0, 0, 0], [0, 0, 0]],
    ["spur",   [center_distance, 0, 0], [0, 0, 0]],
];

function layout_pos(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][1] : layout_pos(name, i+1);
function layout_rot(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][2] : layout_rot(name, i+1);

module at(name) {
    pos = layout_pos(name); rot = layout_rot(name);
    assert(pos != undef, str("Layout entry not found: ", name));
    translate(pos) rotate(rot) children();
}
