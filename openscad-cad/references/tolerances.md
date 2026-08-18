# Fit tolerances — reference values from real prints

## Read this first: two different errors, two different fixes

A hole that comes out too tight has two independent causes, and they must be
corrected in different places. Correcting one twice, or both in the same place,
makes the fit worse rather than better.

| Layer | Cause | Size | Where it is corrected |
|---|---|---|---|
| **Tessellation (CAD)** | OpenSCAD builds circles as *inscribed* polygons, so a hole's flat-to-flat size is `d·cos(180/n)`, not `d`. Deterministic, exactly computable, has nothing to do with the printer. | `d·(1−cos(180/n))`. At `$fa=2, $fs=0.3`: ~0.003 mm at Ø20, ~0.030 mm at Ø200. At OpenSCAD's *defaults* (`$fa=12, $fs=2`): ~0.11 mm at Ø20 — 35× worse. | `true_hole_d()` in `patterns.scad` (Pattern 0) |
| **Process bias (printer)** | FDM lays holes down undersized and outer surfaces oversized; varies with material, nozzle, layer height, speed, orientation. Statistical, must be measured. | Typically an order of magnitude larger than the tessellation error. | The clearance values in the table below, or a per-printer calibration profile |

Two consequences worth stating plainly:

- **Set `$fa`/`$fs` before blaming the printer.** At OpenSCAD's stock defaults
  the CAD-side error alone is comparable to a fit clearance. `$fa = 2; $fs = 0.3;`
  pushes it to a few microns, where it stops mattering.
- **Do not stack compensations.** If you apply `true_hole_d()` *and* enable the
  slicer's hole/XY expansion for the same hole, both enlarge it. Pick one owner
  per layer: `true_hole_d()` owns the geometry error, the slicer or the
  clearance value owns the process error.

Compensate **holes only**. On an external cylinder the polygon's vertices are
the widest points, so a pin already measures its nominal diameter across
corners — enlarging it tightens the fit instead of loosening it.

## Empirical clearance values


Clearance values that came out of actual fit decisions on real parts in this
project set, not guesses. Use these as starting points instead of re-deriving
a clearance from scratch each time; adjust from here if a specific print
comes back too tight/loose and note the correction back into this table.

| Fit | Clearance | When to use | Source |
|---|---|---|---|
| Loose drop-in / easy removal | **1.5mm/side** | Default for a Gridfinity locating pocket around a rectangular item (tool box, tin) when grid space isn't tight — item lifts out one-handed, no wiggle needed. | `gridfinity_hardware_storage_inserts/insert_B.scad` and siblings (94×128mm tool box pocket) |
| Loose drop-in, grid-constrained | **1mm/side** | Same as above, but the bin's usable infill (grid size × 42mm − 2×0.95mm wall) barely clears the item — e.g. widest point 205mm against a 208.1mm 5-wide bin only leaves ~1.1mm slack at 1mm/side. Drop below 1.5mm only when the grid genuinely can't grow (printer bed limit, existing box count) — verify the resulting slack is still ≥ ~1mm before committing to it, not just "whatever remains." | `helping_hands_base_insert/helping_hands_base_insert.scad` |
| Snug friction fit | **0.5mm/side** | A part that must grip by friction alone (e.g. a sleeve that slides onto a motor body and stays via friction, no screws) — tight enough to resist sliding under normal handling, still loose enough to hand-assemble without a press. | `nema23_fan_shroud/nema23_fan_shroud.scad` (`motor_clearance = 1` — see note) |

Note on the shroud's motor sleeve: that specific part used **1mm/side**, not
0.5mm — an unusually large motor cross-section (57mm) where 0.5mm/side felt
too tight to slide on by hand over the full 60mm sleeve length. Treat 0.5mm as
the starting point for a *short* friction sleeve (under ~20mm of contact
length) and lean toward 1mm/side as the contact length or the mating surface
size grows, since a longer/larger friction fit is much less forgiving of
being even slightly undersized (or slightly warped from printing) than a
short one.

These three rows are a small empirical sample (one person, one printer, a
handful of parts) — good starting points, not calibrated process data. For a
fit that has to work first try, print a coupon on your own machine and material
and measure it rather than trusting the table.

General principles behind all three rows:
- These are all **per-side** (radius/offset) values — double for total
  diametral/gap clearance.
- FDM printing tends to print holes/pockets slightly undersized and
  bosses/pins slightly oversized relative to the model — these values already
  bias toward "loose enough to still work after that," not the theoretical
  CAD-perfect clearance.
- When grid/space is genuinely not a constraint, default to 1.5mm/side and
  only tighten it once a real constraint (bed size, existing layout) forces
  the question — don't preemptively tighten for no reason.
