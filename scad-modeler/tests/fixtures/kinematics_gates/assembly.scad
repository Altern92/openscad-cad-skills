// kinematics_gates: base (static) + arm hinged on a Y pin at (0,0,10) + link on a ball at the arm tip.
// A = arm angle about the pin. Echoes ARM_TILT for the angle gate.
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
A = is_undef(A) ? 0 : A;
$fn = 32;
echo(ARM_TILT = A, ARM_TWIN = -1.5 * A, ARM_LIE = A / 4);   // several names in one echo: the parser must read all; ARM_LIE understates the turn
module base() { translate([-6, -6, 0]) cube([12, 12, 10]); }
module arm() { translate([0, 0, 10]) rotate([0, -A, 0]) { rotate([90, 0, 0]) cylinder(d=6, h=8, center=true); translate([0, -2, -2]) cube([40, 4, 4]); translate([40, 0, 0]) sphere(d=5); } }
module tip() { translate([0, 0, 10]) rotate([0, -A, 0]) translate([40, 0, 0]) sphere(d=5); }
module link() { translate([0, 0, 10]) rotate([0, -A, 0]) translate([40, 0, 0]) translate([0, -2, 2]) cube([4, 4, 20]); }
module morph() { translate([0, -2, 8]) cube([10 + A / 2, 4, 4]); }   // not rigid: grows with A
module twin() { translate([0, 0, 10]) rotate([0, -A, 0]) { translate([40, 0, 0]) sphere(d=5); translate([20, 0, 6]) sphere(d=5); } }
if (PART == "base") base();
else if (PART == "arm") arm();
else if (PART == "link") link();
else if (PART == "twin") twin();
else if (PART == "morph") morph();
else { base(); arm(); link(); }
