fillet = 2.5;
minkowski() {
    cube([20, 20, 20], center = true);
    sphere(d = fillet, $fn = 24);
}
