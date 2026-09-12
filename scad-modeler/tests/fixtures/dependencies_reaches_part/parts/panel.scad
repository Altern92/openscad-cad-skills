// panel.scad reads 'wall' and is exported separately, so a change to 'wall'
// reaches a part file -- class C2, not C1.
include <../params.scad>
module panel() { cube([40, 20, wall]); }
panel();
