# P29: gear axes and centre distance (AC)

Tier: bounded (one checker function in `motion_sweep.py`, one example fix, one fixture). Approved by the user 2026-11-27.

Found while preparing a README demo: the flagship example `examples/gear_reduction` failed `validate_scad.sh --all`
(3 FAIL), its gears sat 0.345 mm too close (38.5 mm; BOSL2 `gear_dist()` with the 11T pinion's auto profile
shift 0.357 gives 38.845 mm), and the 0.5-2.0 mm `expected_interference_mm` window had been fitted to that jam.
Moving the spur a further 1.2 mm closer still passed `collisions` and the sweep.

- **AC-1** Given a revolute driver with `teeth`, when the part's real rotation axis in the positioned STL (the axis
  about which it is symmetric under one tooth pitch, found from its centre of mass) is more than 0.05 mm from the
  driver's `origin`/`axis`, then `motion_sweep.py` exits 3 and names the part and the offset. A part that is not
  symmetric about any such axis (keyway, set-screw flat) prints `NOT CHECKED: axis ...` and is not failed.
- **AC-2** Given a `gear_mesh` contact with `"module"` (optional `"pressure_angle"`, default 20, and
  `"profile_shift"`, default `"auto"` = BOSL2 `auto_profile_shift`), when the distance between the two drivers' axes
  differs from BOSL2 `gear_dist()` by more than 0.05 mm, then exit 3 with expected and actual distance. Without
  `"module"` it prints `NOT CHECKED: centre distance ...` (not PASS, not FAIL).
- **AC-3** Given the example, when `validate_scad.sh --all` runs, then rc 0: spur at `gear_dist()`, interference window
  from a fresh measurement, readable declarations, `NO_RETENTION` with a reason, a `behavior.json`.
- **AC-4** Given `tests/run_all.sh`, then fixture `p29_gear_axes` covers: correct pair rc 0; spur moved 1.2 mm with
  `joints.json` unchanged FAIL (AC-1); layout and joints both at 38.5 mm with `module` FAIL (AC-2); no `module` rc 0
  with `NOT CHECKED`; keyed gear `NOT CHECKED: axis`. Fixture `example_gear_reduction` runs the example's
  `validate_scad.sh --all` and requires rc 0.
- **AC-5** Full suite green; RC projects with `gear_mesh` re-validated and any new FAIL reported before changing them.
- **AC-6** A fresh agent that did not write the change reviews it.

## P29b: fixes after the fresh review (AC-6)

The review reproduced 7 defects in the first version; each now has a fixture case in `p29_gear_axes`:
keyed gear skipped the distance check silently (now uses the declared origin and says so); the distance used
declared origins even when real axes were measured (now measured axes, labelled); helical pairs false-FAILed
(contact `"helical"` passed to `gear_dist()`); a gear_mesh whose drivers lack `teeth` / share no motion was
skipped silently (now `NOT CHECKED`); a bad `profile_shift` crashed (now usage error, exit 4); no case near the
0.05 mm tolerance (0.1 mm must fail, 0.03 mm must pass); a tilted gear passed (inertia-axis tilt measured at the
rim, fails above 0.05 mm). Mutants killed: tolerance 0.3, helical ignored, tilt check off.
