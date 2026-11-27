// ~60 deg from vertical (r grows 17.3 over 10): a real overhang region far past 45.
$fn = 48;
cylinder(h = 10, r1 = 10, r2 = 10 + 10 * tan(60));
