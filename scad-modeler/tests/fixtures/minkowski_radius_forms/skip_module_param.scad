// Real form: server_rack_modular/v1_archive/scad/rack_params.scad:50.
// Inside the module 'r' is the PARAMETER, not the file-level r = 5. Using 5
// would invent a tolerance; the term must be skipped.
r = 5;
module rounded_box(size, r) {
    minkowski() {
        cube([size[0] - 2*r, size[1] - 2*r, size[2] - 2*r], center = true);
        sphere(r, $fn = 48);
    }
}
rounded_box([20, 20, 20], 1);
