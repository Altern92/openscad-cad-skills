// No $fn on the sphere inside a module: a caller can pass $fn/$fa/$fs, so
// the file's globals are not known to apply. Skipped.
$fa = 12; $fs = 0.5;
module rb() {
    minkowski() {
        cube([20, 20, 20], center = true);
        sphere(r = 1);
    }
}
rb($fn = 8);
