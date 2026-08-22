// Direct reproduction of the real jackshaft_bearing_wall_at_diff incident
// (INCIDENTS.md, 2026-08-18): the assert omits gear_spin_clearance and
// bearing_press_fit, which parts/gearbox_case.scad applies directly to
// the assert's own dependencies.
CD2 = 26.62;
diff_ring_outer_r = 12.0;
jackshaft_bearing_od = 22.0;
gear_spin_clearance = 0.4;
bearing_press_fit = 0.05;

jackshaft_bearing_wall_at_diff = CD2 - diff_ring_outer_r - jackshaft_bearing_od / 2;
assert(jackshaft_bearing_wall_at_diff > 1.0, "wall too thin");
