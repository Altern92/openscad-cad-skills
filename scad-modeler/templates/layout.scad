// ============================================================
// layout.scad -- where each printed part sits in the shared assembly
// coordinate system. See SKILL.md §3 for the full explanation and
// §6 for how assembly.scad is supposed to consume this file.
//
// State the coordinate system explicitly before the table -- origin,
// what each axis means -- so a position number is checkable against
// a real reference point, not just "whatever made it render right."
// Origin: <e.g. "center of the rear differential, on the axle
//          centerline">. X=<...>, Y=<...>, Z=<...>.
// ============================================================

include <params.scad>

LAYOUT = [
    // ["<part_name>", [x, y, z], [rx, ry, rz]],
    ["<part_a>", [0, 0, 0], [0, 0, 0]],
    ["<part_b>", [0, 0, 0], [0, 0, 0]],
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
