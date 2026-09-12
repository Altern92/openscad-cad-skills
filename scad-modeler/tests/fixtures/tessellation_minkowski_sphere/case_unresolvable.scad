// A sphere whose radius is a computed expression the parser cannot resolve.
// Documented behaviour: the term is SKIPPED, never guessed -- an invented
// radius would silently widen the tolerance, which is the failure mode the
// whole module exists to prevent.
$fa = 2; $fs = 0.3;
wall = 2;
r_guess = wall * 1.5;

minkowski() {
    cube([20, 20, 20], center = true);
    sphere(r = r_guess + 0.25, $fn = 16);
}
