// arm body's own scad: the only place the angle echo lives (AC-A3). A = tilt in degrees.
A = is_undef(A) ? 0 : A;
echo(ARM_TILT = A);
translate([0, 0, 4]) cube([10, 10, 3]);
