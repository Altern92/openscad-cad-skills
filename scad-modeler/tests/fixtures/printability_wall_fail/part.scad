// A uniform 0.3mm shell -- well under the 0.8mm default minimum
// (2x the 0.4mm default nozzle diameter).
$fa = 6; $fs = 0.5;
difference() {
    cube([20, 20, 20]);
    translate([0.3, 0.3, 0.3]) cube([19.4, 19.4, 19.4]);
}
