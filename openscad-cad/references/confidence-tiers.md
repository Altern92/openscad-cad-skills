# Confidence tiers — what may be promised, and on what evidence

State the tier in the final response, with the assumptions it rests on. The
point is not ceremony: it is that "here is your model" means something very
different at Tier 1 than at Tier 4, and saying which one applies is the
difference between a useful deliverable and an overclaim.

`scad-modeler/scripts/doctor.py` reports the highest tier the *environment* can
support. That is a ceiling, not a grade — a part only reaches a tier when its
gates have actually been run and passed.

**Never claim a tier whose gates did not run.** If a gate is unavailable, say so
and drop a tier. Dropping is normal; overclaiming is not recoverable, because the
user finds out by printing.

---

## Tier 1 — Concept part

**Input:** a description, approximate size.
**Gates:** compiles; renders; geometry is non-empty; a human or model looked at
the render.
**May be said:** "this is the shape you described."
**May NOT be said:** anything about dimensions being correct, or about fit.

Looking at a render catches gross errors and nothing finer — see
`openscad-cad/SKILL.md` §1 on why visual inspection is a sanity layer rather
than a gate. Nothing numeric has been verified at this tier.

## Tier 2 — Envelope-verified part

**Input:** Tier 1 plus stated key dimensions.
**Gates:** Tier 1, plus `assert()`s in the model for the design invariants, plus
`check_dimensions.py` against a declared `EXPECTED_BBOX`.
**May be said:** "the outer envelope matches what you specified."
**May NOT be said:** that any hole, bore, or mating feature will fit.

A bounding box is nearly blind to inscribed-polygon undersizing, so it says
nothing about bores. This is the default tier for a bracket, an enclosure, or a
storage insert with generous clearances.

## Tier 3 — Fit-aware part

**Input:** Tier 2, plus fit intent per feature, print orientation, **and a
calibration profile for this printer and material**.
**Gates:** Tier 2, plus `check_features.py` on every fit-critical bore, plus
tessellation compensation applied (`true_hole_d()`, Pattern 0), plus the
measured process offset applied from the calibration profile.
**May be said:** "on the calibrated machine and material, this fit is expected
to work first try."
**May NOT be said:** the same about any other printer, material, or orientation.

**Why calibration is the hard gate here, not a nicety.** Measured on a Bambu Lab
X1-Carbon in PLA at 0.16 mm layers, features from 3–18 mm land at IT12–IT14,
with real intervals around ±0.08 mm at 3 mm and ±0.11 mm at 12 mm; every
external cylinder Ø10–50 mm came out 0.076–0.156 mm undersize. Those are the
same order as the clearance of a running fit. Tessellation compensation is
exact but two orders of magnitude smaller, so it cannot rescue an uncalibrated
fit. Without measured offsets, a fit claim is a guess with a number attached.
Source and caveats: `references/tolerances.md`.

## Tier 4 — Static assembly

**Input:** Tier 3 for each part, plus a shared coordinate system, plus declared
intentional contacts.
**Gates:** Tier 3 per part, plus `check_collisions.py` with a real
`--min-clearance` and an `--expected-contacts` file, on parts exported
positioned in assembly coordinates.
**May be said:** "in the assembled pose, nothing interferes and nothing is
closer than the stated clearance."
**May NOT be said:** that the mechanism works.

One static pose. A gearbox, hinge, latch or slider can be clear at 0° and
interfere at 37°.

## Tier 5 — Motion-verified assembly

**Input:** Tier 4, plus a `motion` block in `joints.json` declaring each moving
part's axis, origin and ratio, and the clearance the mechanism needs while
running.
**Gates:** Tier 4, plus `motion_sweep.py` passing across the declared range.
**May be said:** "at every sampled position of the declared motion, nothing
interferes and nothing is closer than the stated clearance."
**May NOT be said:** that the mechanism is proven clear.

The distinction in that last line is the whole tier. This is **sampling, not a
proof**: between two sampled positions nothing is checked. The adaptive pass
refines around the tightest configuration, which catches narrow clashes near a
minimum — in testing, a swinging arm's worst position was 354.5°, not the
obvious 0°, because its corner passes nearer than its flat end — but a clash
that is both narrow and far from the minimum can still slip between samples.
Quote the step size when claiming this tier, and say it was sampled.

Two more things gate honesty here rather than software: the ratios must be
right (meshing external gears turn opposite ways — a wrong sign sweeps a
mechanism that does not exist), and the declared range must actually cover the
motion the part will see in use.

## Out of scope entirely — not a tier

**Assembly sequence.** Whether a physical insertion path exists is unchecked. A
mechanism can pass Tier 5 and still be impossible to put together.

**Load, stress and stiffness.** No material data, so no calculation. A polymer
gear rating without material properties is arithmetic dressed as engineering,
and printed parts are anisotropic in a way generic values do not capture. If a
task needs this, say the skills stop at geometry and name what is unverified —
do not produce numbers that imply more.

---

## Defaults, so this is a contract and not an interrogation

Do not block on a questionnaire. Infer these, **state every one you assumed in
the final response**, and let the user upgrade the tier by supplying real data.

| Field | Default | Basis | What breaks if wrong |
|---|---|---|---|
| Units | mm | OpenSCAD convention | everything |
| Process | FDM/FFF | scope of these skills | fit and tolerance expectations |
| Nozzle | 0.4 mm | common consumer default | minimum feature and wall rules |
| Layer height | 0.2 mm | common consumer default | Z accuracy, hole roundness |
| Material | PLA | common consumer default | shrinkage, strength, heat |
| `$fa` / `$fs` | 2 / 0.3 | keeps tessellation error ~µm | at OpenSCAD's own defaults a Ø8 hole is 0.23 mm undersize |
| Orientation | strength first, then supports | FDM is anisotropic | functional strength, Z accuracy |
| Calibration | none | assume uncalibrated | caps the part at Tier 2 |
| Fit intent | none stated ⇒ clearance, not press | safe direction | false collision reports |
| Motion | none ⇒ treated as static | safe direction | missed dynamic interference |
| Critical dims | outer envelope only | minimal safe default | internal fits go unchecked |

Two of these are worth overriding on sight rather than defaulting: `$fa`/`$fs`,
because OpenSCAD's stock values put a Ø8 hole 0.23 mm under nominal on their
own; and orientation, because on FDM it is a structural decision, not a
support-material convenience.
