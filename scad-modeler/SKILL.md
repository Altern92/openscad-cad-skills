---
name: scad-modeler
description: Use for complex, multi-part parametric OpenSCAD mechanical assemblies — things with gears, bearings, reductions, multiple interacting printed parts, or where getting a dimension wrong means two parts collide or don't mesh. Triggers on "gear ratio", "reduction", "bearing", "shaft", "assembly", "BOM", "center distance", "mechanical design", "RC car", "gearbox", "multi-part", "design a mechanism", "which architecture", "gearbox layout", or a brief vague enough that more than one mechanism would satisfy it — or requests to design several parts that must fit together and be validated, not just a single organizer/bracket. For a single simple part (an insert, a bracket, a cover, a shroud), use the openscad-cad skill instead — this skill's calculation-table + validation overhead is not worth it for those. This skill builds on openscad-cad (§2 render/export commands still apply) and adds: a gated planning stage that fixes the architecture before any numbers, mandatory engineering calculations before geometry, centralized part positions, per-part local coordinates, and automated dimensional, collision and motion validation.
---

# SCAD Modeler — Multi-Part Mechanical Assemblies

For a single self-contained part, use `openscad-cad` directly — this skill is for
assemblies where multiple parts must fit together correctly (gear meshes, bearing
press-fits, shaft alignments), where a wrong number means two parts collide or a
gear pair doesn't mesh, not just "the pocket is 2mm too small."

## 0. Before anything else: read project facts

Check the project's design docs (`CLAUDE.md` under Claude Code, `AGENTS.md`, or a
project `README`/`design_decisions.md`) for already-decided
facts: motor/component specs, gear ratios, tolerances, design decisions. Don't ask the
user to repeat facts that are already written down. If a needed fact is missing, ask
once rather than guessing — a wrong bearing bore or shaft diameter is not something a
render will catch; it only shows up when the part doesn't fit.

Also read `../INCIDENTS.md` now, not after something breaks. A bug logged
there and never re-read before writing similar geometry is a bug that will
recur — confirmed: the same "margin measured to a tower's center instead
of its edge" mistake was made on three separate towers in one project
before it was actually generalized, and a wall-clearance formula repeated
the identical reasoning error a session later even though an earlier
instance of it was already logged. Logging a root cause is not the same
as having fixed the reasoning that produced it; only actually reading the
log before writing the next similar feature closes that gap.

**New designs only** — before §0.5, run the intake/analysis stage: turn the
user's brief (plus info gathered from other AIs) into
`requirements.json`/`design_manifest.json` (gated by `check_intake.py`),
classify every component **printed vs purchased** (bearings, shafts,
fasteners are vitamins — never printed), and retrieve **2–3 similar past
variants** to adapt instead of starting from zero. Details:
`references/intake_and_analysis.md`; where it sits in the workflow:
`references/validation_decision_tree.md`.

## 0.5. Planning (mandatory before §1, for any assembly with 3+ parts or a genuinely uncertain architecture)

Don't write a single formula in §1 until the mechanical concept is settled
and every part's dependency order is sketched — a real project's calculation
work was wasted because architecture was decided *during* detailed
calculation, not before it (`../INCIDENTS.md`, 2026-08-18). Full workflow,
templates, and why (with correctly-scoped citations — the popular "10x-100x
cheaper to fix early" curve is software-cost data, not mechanical, and
shouldn't be cited as if it were) are in `references/planning.md`. Skip this
step only for a 1-2 part assembly with an already-obvious architecture.

Write it into `templates/plan.md` — copied to the project as `plan.md` —
because prose here is advice a model can skip under pressure; a script that
fails §7 isn't. `scripts/check_plan.py` fails if fewer than 2 architecture
options are listed with no declared exemption, if no `Decision` row is
confirmed, or if `layout.scad` names a part the plan never mentions — that
last one catches a part invented later, during detailing, that skipped
planning entirely, which is the failure mode that actually happened.

## 0.6. Physical assembly narrative (mandatory before geometry, per feature that interfaces with a bearing/shaft/fastener/purchased part or shares a `union()` with another feature)

Planning (§0.5) settles the architecture once, up front. This is different
and ongoing: apply it *every time* you're about to write geometry for a
feature matching the trigger above, throughout §4 — it's a per-feature gate,
not a one-time project step, despite living in the numbering up here for
visibility.

The checks in §7 verify that a model is *internally consistent* — the
mesh is watertight, a hole measures its declared diameter, separate parts
don't collide in their final position. None of that verifies the model is
*physically realizable*: whether it can be assembled, whether a purchased
component can actually be installed, whether two features that happen to
share one printed part collide with each other. A design can pass every
check in §7 and still be impossible to build — confirmed repeatedly in one
project (`../INCIDENTS.md`, 2026-08-19, three separate entries): a
belt-and-pulley stage that passed every geometry check but could never
physically be tensioned onto two fixed, non-adjustable pulleys; three
bearing bores that measured correctly but were sealed behind unbored
material with no path to the outside; a bearing tower that overlapped a
motor mount by 419mm³, invisible because both lived inside the same part's
`union()`. All three shipped as "done" before a human looked at the
physical mechanism and said, in effect, "I don't believe this will work" —
and was right each time.

Before writing the geometry for any such feature, answer in writing (a few
sentences in `calculations.md` or the plan, not a formal document):

- **Insertion path**: how does the physical bearing/shaft/fastener/belt
  actually get into this feature after the part is printed? Trace the
  literal path from outside the part to its final seated position, and
  confirm the material removed along that path is enough for it to travel
  the *whole* path, not just reach its final position — a hole that's the
  right diameter *at the seat* proves nothing about whether anything is in
  the way *between* the seat and the outside.
- **Shared-part neighbors**: what other named sub-features live inside the
  same `union()` as this one? What is the actual physical envelope (not
  the nominal/rounded one) of each, and do their envelopes overlap given
  the *current* position parameters — re-check this any time a position
  parameter either one depends on changes, even for an unrelated reason.
- **Retention**: once assembled, what actually stops this part from moving
  in the direction it's *not* supposed to move (axially, radially, under
  the actual load this mechanism sees — thrust from a worm gear, vibration,
  impact)? A shoulder that stops motion in one direction is not retention;
  it's half of retention.
- **Purchased-part fit**: if this interfaces with something not modeled as
  its own solid (§4.5 covers modeling it as a NopSCADlib vitamin — do that
  where practical), what installation step does that specific real object
  require (thread a belt around fixed pulleys, press a bearing past a
  shoulder, engage a set-screw) that geometry alone won't reveal?

This step exists because the failures above were not geometry mistakes —
the numbers were often internally consistent — they were physical
assembly steps nobody had described in words before writing the code that
was supposed to enable them. Skipping this because "the geometry checks
will catch it" is exactly the mistake that produced all three incidents
above — and §7 now closes two of the three with a real automated check
(`check_bore_reachability.py`, `check_subfeature_overlap.py`), not just
this narrative step; the belt/pulley case stays a judgment call no script
can make.

## 1. Calculation table (mandatory, before writing any geometry)

Write a Markdown table before touching OpenSCAD:

| Part | Formula | Value | Status |
|------|---------|-------|--------|
| Stage 1 ratio | driven_teeth / driver_teeth | 66/11 = 6.00 | OK |
| Center distance 1 | (T1+T2) × mod / 2 | (11+66)×1.0/2 = 38.5mm | OK |
| Bearing bore | per datasheet | 10mm | PATIKRINTI |

Mark anything not sourced from a datasheet/spec/prior decision as `PATIKRINTI` (verify)
— don't silently treat a guess as a fact. Resolve every `PATIKRINTI` (ask the user, or
look it up) before moving to step 2. This table becomes part of the final report.

## 2. `params.scad` — all dimensions, one place

One file, at the project root, containing every dimension used anywhere in the
assembly: component specs (motor, bearings, off-the-shelf parts), gear parameters,
tolerances, and everything derived from the calculation table above. Nothing in any
part file should be a bare number that isn't either a genuinely local/cosmetic detail
(a fillet radius on one specific part, say) or traceable back to this file.

Add `assert()` for anything that must hold for the design to make sense — a gear
ratio near a target, a positive wall thickness after clearance is subtracted, a
bearing bore that's actually bigger than the shaft it rides on. This isn't
decoration: `assert()` is a real top-level OpenSCAD statement (confirmed working)
and it stops the render with a clear message instead of silently producing a part
that's subtly wrong.

```openscad
// params.scad
$fa = 2; $fs = 0.3;
global_clearance = 0.2; // mm, general running clearance

// Motor: RS-550S (datasheet)
motor_d = 36; motor_l = 57; motor_shaft_d = 3.175;

// Gearing (module 1.0 throughout)
gear_module = 1.0;                     // NOT `module` -- that's an OpenSCAD keyword
pinion_teeth = 11; spur_teeth = 66;
ratio_1 = spur_teeth / pinion_teeth;
center_distance_1 = (pinion_teeth + spur_teeth) * gear_module / 2;

assert(ratio_1 > 5.5 && ratio_1 < 6.5, "Stage 1 ratio drifted from target ~6:1");
```

## 3. `layout.scad` — where each *part* sits in the assembly

This is for positioning separate, independently-printed parts relative to a shared
assembly coordinate system (e.g. "the motor mount sits 63mm behind the diff
housing") — a different problem from positioning a *feature within* a single part
(a boss on one housing), which is §4's job.

Define the coordinate system explicitly (origin, axis directions) as a comment, then
a lookup table + `at()` module:

```openscad
// layout.scad
include <params.scad>

// Origin: center of rear differential, on axle centerline. X=right, Y=front, Z=up.
LAYOUT = [
    ["rear_diff_housing", [0, 0, 0], [0, 0, 0]],
    ["rear_jackshaft",    [0, -center_distance_1, 0], [0, 0, 0]],
];

function layout_pos(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][1] : layout_pos(name, i+1);
function layout_rot(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][2] : layout_rot(name, i+1);

module at(name) {
    pos = layout_pos(name); rot = layout_rot(name);
    assert(pos != undef, str("Layout entry not found: ", name));
    translate(pos) rotate(rot) children();
}
```

(Verified: this recursive-lookup pattern and the bare `assert()` both run correctly
under the installed OpenSCAD.)

## 4. Part files — local coordinates, no assembly-level transforms

One file per part. Each part is modeled around its own sensible local origin (a
bearing bore center, a mounting face) — never `translate()`/`rotate()` the whole
part inside its own file; that's `layout.scad`'s job via `at()`. State the local
origin and intended print orientation in a comment at the top.

**For features *within* a part** (a boss on a face, a hole on a corner, ribs), prefer
BOSL2's attachment system over hand-computed `translate()` offsets.

Confirm BOSL2 is actually installed before relying on it — `python3
scripts/doctor.py` reports it, searching the platform's real library locations
and `$OPENSCADPATH`. It checks for `std.scad`, not just a folder named `BOSL2`,
because a directory with the right name is not evidence of a working install: on
one machine that folder once held a single stray `gears.scad`, `include
<BOSL2/std.scad>` failed to resolve, and the failure only surfaced mid-render
(`references/setup-notes.md`). If doctor reports it `INCOMPLETE`, fix it with
`git clone https://github.com/BelfrySCAD/BOSL2.git` into the library directory
doctor names.

## 4.5. Purchased hardware — position it too, not just its cavity

A bearing, motor, or screw's *cavity* gets checked (`EXPECTED_HOLE`), but
its own physical body is invisible to every check in §7 unless it's
positioned as real geometry somewhere — this skill's whole validation chain
only ever looks at `parts/*.scad`. Use
[NopSCADlib](https://github.com/nophead/NopSCADlib)'s real, dimensionally-
accurate solid models ("vitamins": `ball_bearing()`, `screw()`, `NEMA()`,
`BLDC()`, ...) instead of skipping this or hand-drawing a placeholder —
confirmed working end-to-end (2026-08-19): a positioned `ball_bearing()`
correctly passed `check_collisions.py` against a correctly-sized housing
pocket and correctly failed against a wrong one, no changes needed to the
checker itself. See `references/hardware.md` for setup, the vitamin file
naming convention, and the §8 BOM split (Printed vs. Purchased).

```openscad
include <BOSL2/std.scad>

cuboid([housing_w, housing_d, housing_h]) {
    attach(TOP) cyl(h=boss_h, d=boss_d, anchor=BOTTOM);       // boss on top face
    attach(TOP+FWD+RIGHT) screw_hole();                        // corner feature
}
```

Named anchors (`TOP`/`BOTTOM`/`LEFT`/`RIGHT`/`FWD`/`BACK`, combinable with `+` for
edges/corners) are less error-prone than recomputing `width/2 - offset` by hand at
every call site. Gotcha: chaining `attach()` calls without a `{ }` block attaches the
second one to the *first child*, not back to the parent — always use the block form
when attaching more than one feature.

See `templates/part_template.scad`.

## 5. Gears: use BOSL2, do not hand-write involute math

**Do not write a custom involute gear generator.** A from-scratch implementation was
tried and tested for this project already — it failed on two separate points: a
parameter literally named `module` (an OpenSCAD reserved keyword — this is a hard
parse error, confirmed), and mixing radians into `tan()`/`cos()`/`sin()`, which in
OpenSCAD always take **degrees** (confirmed: `tan(20)` = 0.364 correct, but
`tan(20*PI/180)` = 0.0061 — wrong by ~60x). Involute tooth geometry is exactly the
kind of math where a subtly wrong angle produces a tooth that *looks* plausible in a
render but doesn't mesh correctly — the failure mode is invisible until you either
measure carefully or print two parts and try to mate them.

BOSL2's `gears.scad` (part of the full install above) has this solved, including automatic
profile-shift correction for low tooth counts (relevant here — an 11-tooth pinion is
exactly the range prone to undercutting without it):

```openscad
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

spur_gear(mod=gear_module, teeth=pinion_teeth, thickness=15,
          shaft_diam=motor_shaft_d, pressure_angle=20, backlash=0.15);
```

Use `gear_dist(mod=gear_module, teeth1=t1, teeth2=t2)` for center distances instead
of the hand-rolled `(T1+T2)*mod/2` formula once profile shift is involved (the plain
formula is fine for equal/standard gears, but stops being exact once BOSL2's
`profile_shift="auto"` kicks in for small tooth counts).

**`layout.scad` needs both BOSL2 includes too, even though it never calls a
gear function directly.** BOSL2 redefines `translate()`/`rotate()` to track
internal special variables (`$transform`, and `gears.scad`'s own
`$parent_gear_*` set) that `spur_gear()` reads internally; a module's
`translate()`/`rotate()` binding is fixed at the scope where the module is
*defined*, not where it's called from, so `at()`'s own plain
`translate()`/`rotate()` in `layout.scad` won't see them unless
`layout.scad` itself has `include <BOSL2/std.scad>` and `include
<BOSL2/gears.scad>` at its own top level — a part file's own BOSL2 include
does not help, since `assembly.scad` only `use`s part files, and `use`
never propagates a file's top-level variable assignments. Without this,
`--hardwarnings` turns "Ignoring unknown variable" into a hard render
failure, but only when going through `at()` — the part file rendered
standalone looks fine, which is what made this easy to miss (confirmed
directly building `scad-modeler/examples/gear_reduction/`, `INCIDENTS.md`
2026-08-19).

If BOSL2 truly isn't available, MCAD's `involute_gears.scad` is another tested
option -- but check it's a complete install first (`doctor.py` reports it; a
partial MCAD drop-in has been found in the wild more than once). Either way: a
tested library beats a fresh implementation, every time, for gear math.

For **helical, herringbone or bevel** gears specifically, consider
[PolyGear](https://github.com/dpellegr/PolyGear) instead. Its README claims
"full control of the involute tooth profile, including pressure angle, backlash,
variable helix angle, addendum, dedendum and profile shifting", with the helix
angle variable *along the axis* so straight/spiral/herringbone/zerol are one
parameter sweep, all emitted as a single polyhedron. BOSL2 covers straight spur
gears well and is what has actually been test-rendered here, so it stays the
default -- switch only for a profile it handles poorly, and render-test before
trusting the result.

## 6. `assembly.scad` — MODE switch

Import each part file with `use`, **not** `include`. Every part file ends with an
unconditional top-level call to its own module (see §4/template — that's what makes
it render standalone). `include`-ing it into `assembly.scad` runs that call TOO, in
addition to the positioned `at(...)` call below — silently doubling that part's
geometry in the assembly (confirmed by reproducing it: an `include`d part renders
once unpositioned at the origin and once at its real `at()` position; switching the
same line to `use` removes the stray copy, and the part's own internal top-level
variables still resolve correctly inside its module even though `use` doesn't export
them into `assembly.scad`'s namespace — verified both ways with a minimal repro).

```openscad
// assembly.scad
include <layout.scad>
use <parts/rear_diff_housing.scad>
use <parts/rear_jackshaft.scad>

MODE = is_undef(MODE) ? "assembly" : MODE; // set via -D 'MODE="part"' -D 'PART="name"'
PART = is_undef(PART) ? "" : PART;

// Modules aren't values in OpenSCAD, so PART needs an explicit name dispatch --
// there's no way to look a module up by string and call it directly.
module part_by_name(name) {
    if (name == "rear_diff_housing") rear_diff_housing();
    else if (name == "rear_jackshaft") rear_jackshaft();
    else assert(false, str("Unknown part in layout: ", name));
}

if (MODE == "assembly") {
    at("rear_diff_housing") rear_diff_housing();
    at("rear_jackshaft")    rear_jackshaft();
} else if (MODE == "part") {
    at(PART) part_by_name(PART); // e.g. -D 'MODE="part"' -D 'PART="rear_jackshaft"'
} else if (MODE == "exploded") {
    // same as assembly, but with an extra offset per part along its natural axis
}
```

`MODE="part"` is also how you export each part *positioned* in assembly coordinates
for the collision check in §7 — render once per part name with that `-D` pair, not
from the unpositioned part file directly.

Emit a BOM via `echo()` at the end of assembly mode (part name, material, quantity).

If a project already uses **NopSCADlib**, don't hand-roll this: its README states
it has "Python scripts to generate Bills of Materials (BOMs), STL files for all
the printed parts, DXF files for CNC routed parts in a project and a manual
containing assembly instructions and exploded views by scraping markdown
embedded in OpenSCAD comments" (verified against the README, 2026-08-18). That
covers this section and §8's exploded views outright. Adopting it is a whole
framework, not a drop-in, so it's a project-level decision — but for a
multi-part assembly that needs real build documentation it is the cheaper path.

## 7. Validation cycle (mandatory, every part and the full assembly)

```bash
bash scripts/validate_scad.sh --all
```

This renders every `.scad` file it finds under `parts/` plus `assembly.scad`,
checks the OpenSCAD install, and fails loudly on an empty STL — see the script for
exact flags (`--hardwarnings`, `--check-parameters=true`,
`--check-parameter-ranges=true` are all confirmed-real flags on the installed
OpenSCAD build, verified via `--help`).

**Before any part is rendered, it runs an analytic pre-flight gate** (added
2026-08-21): every `assert()` in `params.scad` gets evaluated at near-zero
cost (no real geometry, just a trivial placeholder solid so OpenSCAD doesn't
treat a definitions-only file as an empty-object failure). This exists
because the single most expensive class of defect found across every
project this skill has been used on was **purely algebraic** — two circular
features' outer radii summing to more than their actual center distance
(`r1 + r2 > center_distance`) — something one `assert()` line catches for
free, instead of requiring a full render, mesh export, collision analysis,
and human interpretation to discover after the fact (a real case took 12
validation rounds). **Write an `assert()` in `params.scad` for every
geometric relationship you can bound in closed form** (two circles: sum of
radii vs. center distance; two boxes: interval separation on at least one
axis; coaxial parts: axial clearance) **before writing the geometry that
depends on it** — this is not optional bookkeeping, it is the cheapest check
in the entire chain and it runs first.

Before any of that, it also runs two **project-level** gates (once, not per
part), both opt-in by file existence: `check_assumptions.py` fails if
`calculations.md` has any `Criticality: Critical` row in its decisions log
(§0.5/`references/planning.md`) still unresolved, and
`check_service_envelope.py` fails if a `service_envelope.md` exists with a
blank field. These target "unverified initial assumptions" and "service-load
mismatch" specifically — research (2026-08-19) found these to be the two
most evidence-backed root causes of real mechanical failures, and nothing
else in this chain checks either one, since every other check validates
geometry *against* the calculation table, not whether the table's own inputs
were right.

It also runs a **connectivity check** on every part, by default, with no
declaration needed: a single printed part must render as one connected
solid. A fix to one collision can silently break contact between two OTHER
features that used to touch — a leg widened to clear a gear teeth can lose
contact with the disc it was supposed to hold up, while the overall bounding
box and every other check still passes clean (`INCIDENTS.md`, 2026-08-19).
`scripts/check_connectivity.py` catches this via `trimesh`'s connected-body
count; declare `// EXPECTED_BODIES: N` only for the rare part that's
genuinely meant to be more than one disconnected solid in one STL.

It also runs a **bounding-box check** on any part that declares one, catching
the failure mode visual inspection alone misses: a part that renders and
*looks* right but is subtly the wrong size. Declare it in the part file, next
to the part's own dimension variables:

```openscad
// EXPECTED_BBOX: [40, 20, 15]
```

`validate_scad.sh` greps for that comment and, if present, runs
`scripts/check_dimensions.py --stl <rendered.stl> --scad <part.scad>`. The
tolerance is **derived from the model's own facet resolution**, not fixed: per
axis it is `max(tessellation bound, 0.005mm)`, with `$fn`/`$fa`/`$fs` read from
the part file and one level of its `include`s. The former flat
`max(0.3mm, 1%)` was not a tessellation tolerance at all — at `$fa=2, $fs=0.3`
the real mesh error is ~0.003mm at Ø20 and ~0.030mm at Ø200, so it was 10–65×
too loose and would pass a part that was genuinely the wrong size. Pass
`--abs-tol/--rel-tol` to opt back into a flat tolerance for a part whose
declared bbox is deliberately a rounded nominal. No `EXPECTED_BBOX` = skipped.

**A bounding box is nearly blind to the error that actually breaks fits.**
OpenSCAD puts a polygon vertex at angle 0 (verified in upstream
`primitives.cc`), so the bbox touches the ideal radius on any axis where a
vertex lands — it sees the envelope, not the inscribed-polygon *across-flats*
deficit that makes a bore too tight. Green bbox check ≠ the bearing will seat.

For round fit-critical features, declare them and let them be measured:

```openscad
// EXPECTED_HOLE: [0, 0, 5, "Z", 8.0]   // axis point, axis, target across-flats Ø
```

`validate_scad.sh` then runs `scripts/check_features.py`, which slices the mesh
perpendicular to that axis and measures the shortest distance across the bore —
the dimension a shaft actually binds on. Default tolerance 0.05mm. It also
reports across-corners, and when a hole is short flat-to-flat while correct
across corners it names the cause: inscribed-polygon undersizing rather than a
wrong parameter.

How much this matters is entirely a function of facet resolution, which is why
it's worth checking: a Ø8 hole is undersized by 0.006mm at `$fa=2, $fs=0.3` —
negligible — but by **0.233mm at OpenSCAD's defaults**, which is a failed fit
that nothing else in this chain notices. Fix it with `true_hole_d()` from
`openscad-cad/references/patterns.scad` (Pattern 0) or by setting `$fa`/`$fs`
finer. See `references/tolerances.md` for which error layer is corrected where —
this is the CAD layer only, and the printer's own hole bias sits on top of it.

For assemblies of 3+ parts, also run interference/clearance checking:

```bash
python3 scripts/check_collisions.py --min-clearance 0.3 \
    --expected-contacts joints.json build/*.stl
```

It distinguishes three verdicts rather than one boolean, because "do they
overlap?" is the wrong question for a printed assembly:

- **Unintended interference** — overlap with nothing declaring it. Fail.
- **Insufficient clearance** — no overlap, but a gap below `--min-clearance`.
  Two parts 0.02mm apart pass a pure overlap test and fuse in the print, so
  without a threshold the check is close to meaningless. Default is 0 (overlap
  only); set it to something the process can actually resolve.
- **Intentional contact** — press fits, snap fits and threads are *supposed* to
  overlap. Declare them in `templates/joints.json` and they are range-checked
  by penetration depth (mm, matching the units `expected_interference_mm` is
  written in) instead of flagged; an undeclared overlap still fails, and a
  declared press fit whose parts don't touch fails too. A pair within range
  is ALSO required to touch in exactly one contiguous region by default — a
  max-over-all-contact-points depth can't tell a legitimate contact zone from
  that same zone plus a separate, unrelated structural collision hiding
  behind the same declared range; confirmed live, not hypothetical: a
  declared gear-mesh contact's overlap split into 7 disjoint regions, one
  entirely outside the meshing feature's own extent (`INCIDENTS.md`,
  2026-08-19). Add `"multi_region_ok": true` on the contact entry only for a
  joint that genuinely touches in several places on purpose (a splined
  shaft, say) — but that only bounds the *count* of regions, not *where*
  they are. For a stronger "contact witness" authorizing only the specific
  location the declaration's own derivation describes, add
  `"expected_bounds"` (added 2026-08-21): an assembly-space bounding box
  every detected region must fall inside, regardless of `multi_region_ok`
  or how many regions there are — a region outside it fails as
  `UNAUTHORIZED CONTACT REGION` even for an otherwise-in-range pair. Also
  since 2026-08-21: **`"derivation"` is required whenever
  `expected_interference_mm` is declared** — a non-empty, human-written
  trace back to the source parameters/formula the range came from. A
  hand-typed range with no stated origin is exactly how a wrong declaration
  goes unnoticed (confirmed in this skill's own example project: an initial
  range was copied from an unrelated test fixture rather than derived from
  the actual gear geometry).

Exit codes: `0` pass, `2` degraded (a mesh wasn't watertight, or a declared
interference couldn't be measured — treat as *not checked*, not as pass), `3`
fail, `4` usage error. The non-watertight case previously printed a warning and
carried on while claiming otherwise in its own docstring; FCL results on a
non-watertight mesh aren't trustworthy, so it now changes the verdict. Use
`--strict` to make it a hard fail.

This is **one static pose**. For anything that moves, sweep it:

```bash
python3 scripts/motion_sweep.py --joints joints.json build/*.stl
```

Add a `motion` block to the same `joints.json` (see `templates/joints.json`):
each driver gets an axis, an origin, and a `ratio` — its motion per unit of the
sweep parameter. **Meshing external gears turn opposite ways, so one ratio is
negative**; getting that sign wrong produces a sweep that proves nothing.

Give `teeth` on every revolute driver and the sweep collapses to one tooth
pitch — 18° instead of 360° for a 20-tooth gear, a 20× saving — applied only
when every driver agrees on the period, which happens exactly when the gears
really mesh. Declared contacts stay exempt: a press fit is meant to touch.

A coarse pass is followed by fine re-sampling around the tightest position,
because that is where a clash narrower than the step hides. In testing this
mattered: on a swinging arm the worst clearance was not at the obvious 0° but
at 354.5°, where the arm's *corner* passes nearer than its flat end, and only
the refinement pass found it.

**This is sampling, not proof.** A clash narrower than the step and far from the
global minimum can still be missed. Lower `--step-deg` before concluding a
design is clear, and never widen `min_clearance_mm` to make a failure go away.

**None of the above proves a bore is actually reachable from outside the
part.** `body_count==1`/`is_watertight==True` both report clean for a
bearing/shaft bore that is a fully enclosed internal cavity — a sealed
tunnel with no path to any exterior surface — because an enclosed void is
still one connected, perfectly valid watertight shell.
`check_features.py` also reports clean, since it correctly measures the
bore's diameter wherever it's told to probe, regardless of whether that
location can be reached from outside. This is a real, confirmed failure
mode, not a hypothetical: a gearbox frame with three bearing towers built
as a cylinder with a bore drilled perpendicular through its own center
axis passed every check above while every one of those three bores was
sealed behind ~8mm of solid, un-bored material — the part was completely
unassemblable and nothing in this chain said so (`INCIDENTS.md`,
2026-08-19, "bearing bores never reached the tower's true exterior
surface").

For any bore/pocket meant to receive a bearing, shaft, or fastener
**from outside the part after printing**, verify the path is actually
open — a point-containment scan along the bore's own axis, from well
outside the part to the seat position, checking that every sampled point
is NOT inside the solid. `scripts/check_bore_reachability.py` does this:
declare each bore's axis segment (a far-outside start point, the real
seat position as `end`) in a project-root `bores.json`, and
`validate_scad.sh --all` picks it up automatically once that file
exists, checking every rendered part STL. Manually:

```bash
python3 scripts/check_bore_reachability.py --bores bores.json build/*.stl
```

A wall centered exactly on a perpendicular tower's own axis is the
specific geometry that hides this: reaching the tower's true (curved)
exterior takes the tower's *full radius*, not a small fixed buffer, and a
bore that stops short leaves an enclosed cavity that every check above
calls clean. Do this for every bearing/shaft entry point declared in
§4.5, not just the ones that look tight in a render.

**Also not checked by anything above: overlap BETWEEN sub-features
inside the same single part.** `check_collisions.py` only ever compares
separately-exported STLs against each other — by the time two named
sub-modules (a tower, a wall, a boss) are `union()`-ed together and
exported as one part, they no longer exist as distinguishable objects, so
an overlap between them, however large, cannot be flagged: `union()` of
two overlapping solids is still one valid, watertight, single-body shell.
Confirmed: a bearing tower overlapped an unrelated motor-mounting cradle
in the same part by 419mm³, invisible through several rounds of "all
green" validation because both were part of one part's `union()`
(`INCIDENTS.md`, 2026-08-19).

For any part assembled from more than one named sub-module (a tower next
to a wall, a boss next to a cradle, ribs near a boss), export each
sub-module as its own solo STL (same local coordinate system, pre-union)
and check every pair with `scripts/check_subfeature_overlap.py`:

```bash
python3 scripts/check_subfeature_overlap.py sub_features/*.stl
```

Skip a pair only when the overlap is an intentional fusion (e.g. a boss
meant to blend into the tower it mounts on) — declare that explicitly with
`--exempt fusions.json`, the same way `joints.json` declares intentional
contact between separate parts in `check_collisions.py`, rather than
silently excluding it. This needs a mesh boolean engine (`pip install
manifold3d`) to measure overlap volume; without one it reports degraded,
not passed. Not wired into `validate_scad.sh` — solo sub-feature export is
an extra step the part file's author adds deliberately, the same way
assembly-positioned exports are a prerequisite for `check_collisions.py`,
not something the normal per-part render produces on its own.

Still not checked at all: load, strength, or manufacturability (minimum
wall thickness for the actual material/process, printability of
overhangs). Both need judgment, a datasheet, or a physical test — this
chain has no way to derive them from geometry alone.

This needs `trimesh`, `python-fcl` (trimesh's `CollisionManager` doesn't do
collision detection itself — it wraps FCL), and `scipy` (trimesh's own mesh
checks need it). All three confirmed necessary by actually running the script —
`pip install trimesh python-fcl scipy` (macOS Homebrew Python needs a venv for
this: `python3 -m venv .venv && source .venv/bin/activate` first, or it'll refuse
with an externally-managed-environment error). Both STL inputs must be watertight
and already expressed in the shared assembly coordinate system (i.e. exported from
`assembly.scad` with each part positioned via `at()`, not from an unpositioned part
file) or the check is meaningless.

Then render a preview and actually look at it, same as always:
```bash
openscad --backend=Manifold --render -o build/preview.png --imgsize=1200,900 --autocenter --viewall assembly.scad
```

Fix any failure at the source (wrong parameter, wrong layout position) — do not
loosen an `assert()` or a collision threshold to make a failure go away.

**After any geometry fix, re-run the whole cycle, not just the check you were
fixing.** A fix for one failure can silently break something else that was
previously fine and that nothing was watching — that's exactly how the
connectivity bug above happened: a leg radius was widened until
`check_collisions.py` said OK, and the session stopped there instead of
re-running `validate_scad.sh --all`, which would have caught the new
disconnection immediately. Stopping at the first green result for the thing
you were looking at is not the same as the part being right.

## 8. Final report

**Before writing it, run `python3 scripts/check_rules.py --project-dir .`
and cite its FULL output** (not a paraphrase) in the report, including its
list of MANUAL rules and your own explicit done/skipped/not-applicable
self-assessment for each one. This is the L3/L4 self-check loop from
`references/rules_enforcement.md`: rule-following that depends on being
remembered mid-conversation drifts under context load; a gate that has to
be run and quoted does not. A report that says "all checks passed" without
this citation is not distinguishable from one where a step was silently
skipped, which is the exact failure mode this exists to close.

After every check passes, report:
- Files created/changed.
- BOM: split **Printed** (material, print orientation, quantity) from
  **Purchased** (NopSCADlib vitamin or supplier part number, quantity) —
  see `references/hardware.md`. A print orientation on a bearing is a sign
  something was missed, not a style choice.
- Critical dimensions carried over from the calculation table (ratios, center
  distances, bearing fits) — these are what the user needs to double check against
  their own understanding of the mechanism.
- Any remaining `PATIKRINTI` items that couldn't be resolved.
- Suggested print orientation per part.

If a check failed during this session and you fixed it — not a routine
addition, an actual bug (a wrong test, a hang, a false pass, an inaccurate
claim caught by cross-checking) — append an entry to `../INCIDENTS.md` before
finishing, using its entry format. This is raw data for a later pattern-review
pass, not something to analyze now; just log it accurately.

## Reference files

- `references/validation_decision_tree.md` — Mermaid flowchart: "which check
  applies to my situation right now", across ~10 scripts with different
  triggers (mandatory/opt-in/manual). Navigation aid only, not authoritative
  — the prose below (with incident citations) wins if this ever drifts.
- `references/intake_and_analysis.md` — Stage 0/0.5: requirements JSON
  schema (confirmed/estimated/unknown status discipline), printed-vs-purchased
  decision criteria (NopSCADlib vitamins), similar-variant retrieval over past
  designs (direct read-through of past READMEs, not an embedding index — the
  archive is ~12 projects, too small for vector search to earn its cost).
- `references/mechanics_and_motion_planning.md` — motion taxonomy
  (rotation/translation/rolling/flexure), FDM fit-clearance tables,
  `design_manifest.json` motion block that auto-triggers the mechanics checks.
- `references/change_propagation.md` + `scripts/check_dependencies.py` — the
  "choice tree": param→part dependency DAG; on any edit, dirty-root from the
  changed variable and recompute only the affected chain in topological order,
  escalating to the full `--all` re-run on any parse uncertainty.
- `references/rules_enforcement.md` — why agents drift from written rules and
  the layered countermeasure (prompt reminders → deterministic gates →
  self-verification loop → machine-checkable rules manifest).
- `rules_manifest.yaml` + `scripts/check_rules.py` — L4: the single list of
  every rule in this skill, with a detector for whether it applies to the
  current project and, for rules with an automated gate, the exact command
  that proves it (not a description a model could paraphrase incorrectly).
  Rules with no automated gate (whether the §0.6 narrative was actually
  written, for example) print as MANUAL rather than being silently skipped —
  §8 requires citing this script's full output, including a stated verdict
  for every MANUAL rule. Needs `pyyaml`.
- `scripts/check_intake.py` — Stage 0 gate: validates
  `design_manifest.json`/`requirements.json` against the OpenSCADDesignSpec
  schema in `intake_and_analysis.md`, and fails on any parameter still
  `status: "unknown"` (an `estimated` value is fine and only reported —
  `unknown` means a question intake asked was never answered, which the
  same reference file calls the single biggest source of wrong designs).
  Needs `jsonschema`.
- `../INCIDENTS.md` — append-only log of real bugs found and fixed (§8). Not
  reviewed automatically; a later pass reads it for patterns worth promoting
  into a permanent rule here.
- `references/hardware.md` — §4.5: positioning purchased hardware
  (NopSCADlib "vitamins" -- bearings, motors, screws) as real, checkable
  geometry instead of an invisible cavity-only assumption. Confirmed
  end-to-end against `check_collisions.py` with no changes to the checker.
- `references/planning.md` — §0.5's full workflow: a 6-field decisions log
  (including the `Criticality` column `check_assumptions.py` enforces), a
  lightweight Pugh comparison for competing architectures, and a minimal
  dependency matrix for part ordering. Grounded in real design-process
  literature (Pahl & Beitz, DSM, Pugh) with citation caveats spelled out.
- `templates/plan.md` — copy to `plan.md` per project; the artifact
  `check_plan.py` enforces. Ships deliberately unfillable-by-accident (the
  raw template fails the check) — tested against 5 synthetic cases plus a
  real `validate_scad.sh` integration run before being wired in.
- `scripts/check_plan.py` — fails if §0.5 Planning didn't actually happen:
  fewer than 2 architecture options with no declared exemption, no
  confirmed `Decision` row, or a `layout.scad` part missing from the plan's
  parts table (a part invented later, during detailing, that skipped
  planning entirely — the most valuable of the three, and the exact gap
  that let the rear_axle incident happen). Opt-in: skips if no `plan.md`.
- `scripts/check_assumptions.py` — fails validation if a `Critical` row in
  the decisions log is still unresolved. Targets the single most
  evidence-backed root cause of real mechanical failures found in a
  2026-08-19 research pass (wrong/unverified design assumptions), which no
  geometry check can see. Opt-in: skips silently if `calculations.md` has no
  decisions-log table.
- `scripts/check_service_envelope.py` — fails if a `service_envelope.md`
  (`templates/service_envelope.md`) exists with a blank field. Targets the
  second most evidence-backed root cause (service-load/environment
  mismatch — vibration, thermal, wear, duty cycle). Opt-in: skips if the
  file doesn't exist.
- `scripts/validate_scad.sh` — render/validate every part + assembly, auto-discovers
  files under `parts/` (no manual list to keep in sync); also runs the bounding-box
  check below for any part that opts in.
- `scripts/check_connectivity.py` — confirms a part's rendered STL is a single
  connected body (default, no declaration needed) via `trimesh`'s connected-
  body count; a bbox and a between-STL collision check both miss a part that
  silently split into two disconnected islands. `// EXPECTED_BODIES: N` opts
  out for the rare genuinely-multi-body part. Needs only `trimesh`.
- `scripts/check_dimensions.py` — compares a rendered STL's bounding box against
  a part's declared `// EXPECTED_BBOX: [x, y, z]`, with the tolerance derived
  from `$fn`/`$fa`/`$fs`. Needs only `trimesh` (confirmed lighter than
  check_collisions.py — no scipy/python-fcl needed for this one).
- `scripts/check_plan.py` — the planning gate: refuses detail work while the
  architecture is unchosen, a blocking assumption stands, or a layout part never
  went through the plan. Exit 0/1/4.
- `scripts/motion_sweep.py` — interference and clearance through a declared
  motion cycle, with gear-tooth periodicity and adaptive refinement around the
  tightest position. Exit 0/2/3/4 like the others; `--json` for a machine-readable
  result.
- `scripts/selftest.py` — end-to-end acceptance test: builds a part whose
  answers are known in advance, runs the whole chain, and checks each tool
  reaches the right verdict — including that the bore check *fails* on an
  uncompensated bore. Run it once per machine before trusting the toolchain.
- `scripts/doctor.py` — detects OpenSCAD, libraries (by entry-point file, not by
  folder name), Python dependencies and any calibration profile; reports the
  highest confidence tier the environment supports. Run it before trusting
  anything environmental. Exit 0 ok / 2 degraded / 3 no OpenSCAD.
- `scripts/check_features.py` — measures declared bores flat-to-flat by
  sectioning the mesh, catching the undersizing a bbox check cannot see. Needs
  `trimesh`, `shapely`, `scipy`, `networkx`.
- `scripts/scad_tessellation.py` — OpenSCAD's facet-count formula plus the
  inscribed-polygon error bounds, and the `$fn`/`$fa`/`$fs` parser that follows
  one level of `include`. Imported by `check_dimensions.py`; read its header for
  why across-flats deficit and bbox deviation are different quantities.
- `scripts/check_collisions.py` — trimesh/FCL interference **and clearance**
  check between already-positioned part STLs, with declared intentional
  contacts. `manifold3d` is an optional extra: without a boolean engine a
  declared press fit can't be measured against its range and the run reports
  degraded rather than passing.
- `templates/plan.md` — the four planning gates, in the shape `check_plan.py`
  reads.
- `references/planning.md` — why concept precedes detail, minimal Pugh and
  dependency-matrix formats, and what the literature actually supports.
- `templates/joints.json` — starting point for declaring intentional contact
  pairs.
- `scripts/check_bore_reachability.py` — §0.6/§7: point-containment scan along
  a declared bore axis, catching a bore that's the right diameter at its seat
  but sealed behind unbored material somewhere between the seat and the
  outside — the exact failure `is_watertight`/`check_connectivity.py`/
  `check_features.py` all report clean on, since a sealed cavity is still one
  valid watertight shell. Opt-in via a project-root `bores.json`; auto-runs in
  `validate_scad.sh --all` once that file exists. Needs `trimesh`, `numpy`,
  `rtree`.
- `scripts/check_subfeature_overlap.py` — §0.6/§7: boolean-intersection
  overlap check between named sub-modules of the *same* part, exported solo
  before `union()` — the gap `check_collisions.py` structurally can't close,
  since two overlapping solids `union()`-ed into one part are still one
  valid, watertight, single-body shell with no trace of the overlap. Declared
  exemptions via `--exempt` for intentional fusions. Manual step, not wired
  into `validate_scad.sh` (solo sub-feature export is an extra step the part
  author adds). Needs `trimesh`; `manifold3d` for volume measurement.
- `../openscad-cad/references/confidence-tiers.md` — what may be claimed at each
  tier, the gates each requires, and the default table that keeps the spec a
  contract rather than an interrogation. State the tier reached in the final
  report (§8).
- `templates/part_template.scad` — starting point for a new part file, includes
  the `EXPECTED_BBOX` convention.
- `templates/layout.scad` — starting point for a new assembly's `layout.scad`.
