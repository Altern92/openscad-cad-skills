include <../params.scad>
_deck_t = nas_deck_thickness;
_socket_depth = post_socket_depth;

assert(_deck_t > 0);

// FIX: the deck-specific local variable now has its own assert.
_deck_socket_depth = 2.4;
_deck_socket_d = post_socket_d;
assert(_deck_socket_depth * 2 < _deck_t, "deck sockets would intersect");
assert(_deck_socket_depth <= _socket_depth, "deck socket cannot be deeper than standard socket");

module nas_deck() {
    difference() {
        cube([module_width, module_depth, _deck_t]);
        translate([10, 10, -0.01])
            cylinder(d=_deck_socket_d, h=_deck_socket_depth + 0.02, $fn=32);
    }
}
