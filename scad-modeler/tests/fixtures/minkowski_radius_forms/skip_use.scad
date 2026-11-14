// use<> does not import variables in OpenSCAD: 'fillet' is undefined here.
use <params_expr.scad>
minkowski() {
    cube([20, 20, 20], center = true);
    sphere(r = fillet / 2, $fn = 12);
}
