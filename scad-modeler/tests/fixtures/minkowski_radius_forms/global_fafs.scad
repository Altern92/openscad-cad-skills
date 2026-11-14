// No $fn on the sphere: facets come from $fa (file) and $fs (on the call).
$fa = 12;
minkowski() {
    cube([20, 20, 20], center = true);
    sphere(r = 1, $fs = 0.5);
}
