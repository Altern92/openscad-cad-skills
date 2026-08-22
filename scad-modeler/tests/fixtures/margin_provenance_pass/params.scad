// Same as margin_provenance_fail/, but the assert's formula now includes
// both clearance terms -- the fix that closes the real incident.
CD2 = 26.62;
diff_ring_outer_r = 12.0;
jackshaft_bearing_od = 22.0;
gear_spin_clearance = 0.4;
bearing_press_fit = 0.05;

jackshaft_bearing_wall_at_diff = CD2 - (diff_ring_outer_r + gear_spin_clearance) - (jackshaft_bearing_od + bearing_press_fit) / 2;
assert(jackshaft_bearing_wall_at_diff > 1.0, "wall too thin");
