# Fit tolerances — reference values from real prints

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
