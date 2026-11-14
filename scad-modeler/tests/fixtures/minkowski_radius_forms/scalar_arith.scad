r = 2; gap = 0.4;   // two statements on one line
minkowski() {
    cube([20, 20, 20], center = true);
    sphere(r = (r - 0.5 + gap) / 2, $fn = 20);
}
