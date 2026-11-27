// Same tunnel 4 mm wide: bridge span 4 mm <= 5 mm prints without support.
difference() { cube([30, 20, 10]); translate([13, -1, -1]) cube([4, 22, 6]); }
