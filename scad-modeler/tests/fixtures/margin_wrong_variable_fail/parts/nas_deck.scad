include <../params.scad>
_deck_t = nas_deck_thickness;
_socket_depth = post_socket_depth;

assert(_deck_t > 0);
assert(_socket_depth > 0, "standard socket depth must be positive");

// BUG (the real incident): a new, deck-specific local variable is
// introduced for geometry, but the assert above still checks the OLD
// _socket_depth instead.
_deck_socket_depth = 2.4;
_deck_socket_d = post_socket_d;

module nas_deck() {
    difference() {
        cube([module_width, module_depth, _deck_t]);
        translate([10, 10, -0.01])
            cylinder(d=_deck_socket_d, h=_deck_socket_depth + 0.02, $fn=32);
    }
}
