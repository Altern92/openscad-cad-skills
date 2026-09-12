// Reproduces server_rack_modular_v4/v8 parts/node.scad exactly (2026-09-12).
// Declared bbox 26.0; a 24-facet sphere in the minkowski() makes it 25.9786.
$fa = 2; $fs = 0.3;
node_s = 26;
fillet = 2.5;

minkowski() {
    cube([node_s - fillet, node_s - fillet, node_s - fillet], center = true);
    sphere(r = fillet / 2, $fn = 24);
}
