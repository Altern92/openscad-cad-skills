a = 1; b = 2;
minkowski() {
    cube([20, 20, 20], center = true);
    sphere(r = max(a, b) / 2, $fn = 16);
}
