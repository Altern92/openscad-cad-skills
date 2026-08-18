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

## What accuracy FDM can actually hold — and why ISO fit labels don't apply

Primary source for this section, **read in full**: Gebre, Cristofolini, Zago &
Gallo, "Influence of Geometry and Size on Precision and Accuracy in Fused
Deposition Modeling (FDM) Additive Manufacturing", *Material Design & Processing
Communications* 2026:7177386, DOI 10.1155/mdp2/7177386 (open access, 22 pp).
Conditions: **Bambu Lab X1-Carbon, PLA, 0.16 mm layers, manufacturer-recommended
unoptimised settings**, 100% infill for the capability specimens. Measured by
CMM. That is close to a typical hobby setup, which is why the numbers below are
worth anything to us — but they are one machine and one material.

**Verification status (2026-08-18).** Fully confirmed against the primary
source -- the user retrieved the actual PDF (automated fetching was blocked by
a Cloudflare bot-challenge on both the publisher and the author's institutional
repository; the paper is genuine CC-BY open access, just not reachable by
script) and every number below was checked line-by-line against it. All of
Table 3 (IT grades), all of Table 5 (cylinder deviations, recomputed
independently from the paper's own nominal/measured columns -- see
`scripts/` history), the cylindricity range (0.034-0.089mm), and the 3mm/12mm
measured intervals matched exactly. One error found and fixed: this file
previously said "milling and turning occupy IT7-IT10" -- the paper's actual
Table 4 has **milling at IT9-11**, not IT7-10; only turning reaches IT7-10.
One nuance worth knowing if replicating this: the cylinder/curve numbers
below come from the GBTA specimens, printed at **15% gyroid infill**, not the
100% infill used for the staircase/IT-grade specimens -- the paper states infill
shouldn't matter much for these dimensions (deviation is dominated by contour
deposition and boundary cooling, not infill), but it's a different print
setting than the IT-grade table above.

**Achievable IT grade by nominal size and axis** (Table 3, at 95% confidence
with Pm, Pmk ≥ 1.33):

| Nominal | X | Y | Z |
|---|---|---|---|
| 3 mm | IT13 | IT13 | **IT14** |
| 6 mm | IT12 | IT12 | IT13 |
| 9 mm | IT11 | IT13 | IT13 |
| 12–15 mm | IT12 | IT13 | IT13 |
| 18 mm | IT13 | IT13 | IT13 |
| 24–30 mm | IT12–13 | IT12 | IT12 |
| 36 mm | IT11 | IT11 | IT11 |
| 39–94 mm | IT10–11 | IT10 | — |

Two things follow that matter more than the headline "IT9–IT14":

- **Small features are the worst case, and small features are most of what we
  print.** Everything from 3–18 mm sits at IT12–IT14. The good grades only
  appear above ~36 mm.
- **Z is equal or worse than X/Y**, most clearly at the small end (IT14 vs IT13
  at 3 mm). Build direction is a dimensional decision, not just a strength one.

Measured intervals give the practical band directly: nominal 3 mm came out
2.90–3.05 mm on X, nominal 12 mm came out 11.87–12.08 mm. **Roughly ±0.08 mm at
3 mm and ±0.11 mm at 12 mm** — an order of magnitude more than any tessellation
error, which is why the CAD-layer correction above is necessary but nowhere near
sufficient.

**External cylinders print undersize, and by a roughly constant absolute
amount** (Table 5, vertical and horizontal cylinders Ø10–50 mm):

| Nominal Ø | Vertical | Horizontal |
|---|---|---|
| 10 mm | −0.108 mm (−1.08%) | −0.076 mm (−0.76%) |
| 20 mm | −0.147 mm (−0.74%) | −0.098 mm (−0.49%) |
| 30 mm | −0.145 mm (−0.48%) | −0.106 mm (−0.35%) |
| 40 mm | −0.139 mm (−0.35%) | −0.103 mm (−0.26%) |
| 50 mm | −0.130 mm (−0.26%) | −0.156 mm (−0.31%) |

Every single cylinder came out negative. Absolute deviation stays near
−0.08…−0.16 mm regardless of size, so the *percentage* error explodes on small
features — which is the whole reason IT grade improves with size. Cylindricity
stayed tight (0.034–0.089 mm): the form is right, the size is not.

**A conflict with the folklore, stated openly.** The common maker heuristic —
and the "General principles" note further down this file — says holes print
undersize and pins/bosses print *oversize*. This paper measures external
cylinders printing **undersize** by up to 0.16 mm. Both can be true at different
scales: extrusion-width and elephant-foot effects dominate at small features,
while PLA thermal shrinkage (−0.26% to −1.08% here) dominates from ~10 mm up.
Do not assume a pin will come out fat. Measure.

**What this paper does *not* establish.** Its benchmark artefact is a door-handle
geometry and, in the authors' own words, "geometrical features such as internal
holes or unsupported overhangs are not explicitly included and would require
dedicated benchmark artifacts." Hole undersizing is stated as *expected* from
prior work, not measured here. So: undersizing of **external** cylindrical and
curved features is measured; **internal hole** behaviour on FDM remains
inferred, and is exactly what your own calibration coupon has to settle.

**The practical consequence: do not label a printed fit with an ISO 286
designation.** An H7 hole is IT7. The best grade this machine reached anywhere
near a normal fit size was IT11 at Ø9 mm, and IT12–IT13 was typical — four to
six grades coarser than H7. Writing "H7/g6" on a printed part is a
precision-machining label over a process that cannot realise it: the same
pseudo-rigour as claiming a full gear rating without material data. The paper's
own Table 4 makes the point by comparison — turning reaches IT7–IT10 and
milling IT9–IT11, both finer than FDM's IT9–IT14 (this study), with FDM's own
X/Y/Z columns bottoming out no better than IT9.

Use functional fit classes plus a measured per-printer offset instead — describe
what the joint must **do** (free clearance, guided slide, locating, light press),
not which machining grade it pretends to hold.

Two limits on all of the above: it is **one printer, one material** (the authors
say so explicitly — "specific to the PLA material and printer configuration
adopted in this study"), and the deviations were position-dependent within the
build chamber, with Z-direction error statistically tied to plate position from
uneven fan cooling. Treat these numbers as the right *shape* of the problem and
a sane starting point, not as your machine's constants.

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
  CAD-perfect clearance. **Caveat, added after reading the measured data above:
  the "pins print oversize" half of this is not safe above ~10 mm.** Gebre et al.
  measured every external cylinder from Ø10–50 mm coming out 0.08–0.16 mm
  *under* nominal, because PLA thermal shrinkage overtakes extrusion-width
  effects as features grow. The heuristic holds at small scale; don't extrapolate
  it upward.
- When grid/space is genuinely not a constraint, default to 1.5mm/side and
  only tighten it once a real constraint (bed size, existing layout) forces
  the question — don't preemptively tighten for no reason.
