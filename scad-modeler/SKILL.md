---
name: scad-modeler
description: Use for complex, multi-part parametric OpenSCAD mechanical assemblies — things with gears, bearings, reductions, multiple interacting printed parts, or where getting a dimension wrong means two parts collide or don't mesh. Triggers on "gear ratio", "reduction", "bearing", "shaft", "assembly", "BOM", "center distance", "mechanical design", "RC car", "gearbox", "multi-part", or requests to design several parts that must fit together and be validated, not just a single organizer/bracket. For a single simple part (an insert, a bracket, a cover, a shroud), use the openscad-cad skill instead — this skill's calculation-table + validation overhead is not worth it for those. This skill builds on openscad-cad (§2 render/export commands still apply) and adds: mandatory engineering calculations before geometry, centralized part positions, per-part local coordinates, and automated dimensional/collision validation.
---

# SCAD Modeler — Multi-Part Mechanical Assemblies

For a single self-contained part, use `openscad-cad` directly — this skill is for
assemblies where multiple parts must fit together correctly (gear meshes, bearing
press-fits, shaft alignments), where a wrong number means two parts collide or a
gear pair doesn't mesh, not just "the pocket is 2mm too small."

## 0. Before anything else: read project facts

Check `CLAUDE.md` (project-level, or the specific project folder) for already-decided
facts: motor/component specs, gear ratios, tolerances, design decisions. Don't ask the
user to repeat facts that are already written down. If a needed fact is missing, ask
once rather than guessing — a wrong bearing bore or shaft diameter is not something a
render will catch; it only shows up when the part doesn't fit.

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
BOSL2's attachment system over hand-computed `translate()` offsets. A full, real
BOSL2 clone is installed at `~/Documents/OpenSCAD/libraries/BOSL2` (verified: 56
`.scad` files including `std.scad`, and `spur_gear()` below was test-rendered
successfully against this install with the project's actual 11-tooth pinion
parameters — see `references/setup-notes.md` for why this needed re-doing: an
earlier, incomplete drop-in of just `gears.scad` alone was there before and
silently failed on missing dependencies):

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

If BOSL2 truly isn't available for some reason, MCAD's `involute_gears.scad` is
another tested option -- but verify it's a complete MCAD install before relying on
it (`~/Documents/OpenSCAD/libraries/MCAD` on this machine currently has only 2 of
MCAD's files present, not a full clone -- check before use, don't assume). Either
way: a tested library beats a fresh implementation, every time, for gear math.

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
  instead of flagged; an undeclared overlap still fails, and a declared press
  fit whose parts don't touch fails too.

Exit codes: `0` pass, `2` degraded (a mesh wasn't watertight, or a declared
interference couldn't be measured — treat as *not checked*, not as pass), `3`
fail, `4` usage error. The non-watertight case previously printed a warning and
carried on while claiming otherwise in its own docstring; FCL results on a
non-watertight mesh aren't trustworthy, so it now changes the verdict. Use
`--strict` to make it a hard fail.

This is **one static pose**. A gearbox, hinge, latch or slider can be clear at
0° and interfere at 37°; nothing here sweeps motion or checks that an assembly
sequence exists. Don't read a pass as "the mechanism works."

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

## 8. Final report

After every check passes, report:
- Files created/changed.
- BOM: part name, material, quantity, key dimensions.
- Critical dimensions carried over from the calculation table (ratios, center
  distances, bearing fits) — these are what the user needs to double check against
  their own understanding of the mechanism.
- Any remaining `PATIKRINTI` items that couldn't be resolved.
- Suggested print orientation per part.

## Reference files

- `scripts/validate_scad.sh` — render/validate every part + assembly, auto-discovers
  files under `parts/` (no manual list to keep in sync); also runs the bounding-box
  check below for any part that opts in.
- `scripts/check_dimensions.py` — compares a rendered STL's bounding box against
  a part's declared `// EXPECTED_BBOX: [x, y, z]`, with the tolerance derived
  from `$fn`/`$fa`/`$fs`. Needs only `trimesh` (confirmed lighter than
  check_collisions.py — no scipy/python-fcl needed for this one).
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
- `templates/joints.json` — starting point for declaring intentional contact
  pairs.
- `templates/part_template.scad` — starting point for a new part file, includes
  the `EXPECTED_BBOX` convention.
- `templates/layout.scad` — starting point for a new assembly's `layout.scad`.
