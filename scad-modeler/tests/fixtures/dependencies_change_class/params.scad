// Minimal reproduction of the change-propagation graph. The point of the
// check is that a parameter used inside a formula is traced TO that formula,
// so a one-value edit can name what it touched instead of triggering the
// blanket "re-run everything" rule (references/change_propagation.md).
panel_thickness = 3;
post_d = 18;
derived_gap = post_d / 2 - panel_thickness;
