include <../params.scad>
module diff_cavity() {
    cylinder(r = diff_ring_outer_r + gear_spin_clearance, h = 10);
}
module jackshaft_bearing_pockets() {
    cylinder(d = jackshaft_bearing_od + bearing_press_fit, h = 10);
}
