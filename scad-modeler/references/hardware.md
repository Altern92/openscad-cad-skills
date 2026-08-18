# Purchased hardware ("vitamins") — the blind spot this closes

## Why this exists

Every check in this skill's validation chain (`check_collisions.py`,
`check_connectivity.py`, `motion_sweep.py`) only ever sees `parts/*.scad` --
things this skill designs and prints. A real assembly also contains
purchased components with their own real physical envelope: bearings,
motors, screws, off-the-shelf gears. Cavities sized for them get checked
(`EXPECTED_HOLE`, `check_features.py`), but the purchased part's own BODY
has never been positioned as a real, checkable solid anywhere in this
pipeline -- so a motor body colliding with a nearby printed bracket, or a
bearing's actual OD interfering with something, is invisible to every check
here unless someone happens to hand-model a placeholder for it.

## The fix: NopSCADlib "vitamins," not placeholders you draw yourself

[NopSCADlib](https://github.com/nophead/NopSCADlib) (nophead -- the same
person behind the `polyhole` technique `patterns.scad` Pattern 0 already
credits) ships real, dimensionally-accurate solid models for exactly this
purchased-hardware category, not just reference data. Confirmed by actually
rendering one (2026-08-19): `ball_bearing(BBMR105)` (a custom MR105 constant
-- MR105 isn't predefined, see below) renders a watertight, manifold solid
whose bounding box is exactly `[10, 10, 4]` mm, matching the real MR105
spec (OD10 × W4mm), centered on the bearing axis at the origin. Then
round-tripped through the actual pipeline: positioned it against a printed
housing's bearing pocket and ran `check_collisions.py` on both STLs --
correctly OK when the pocket was sized/centered right, correctly FAILED
(overlap ~166mm³) on a deliberately wrong pocket. The whole existing
toolchain works on a vitamin with zero modification; it's just another STL.

```bash
git clone https://github.com/nophead/NopSCADlib.git \
    ~/Documents/OpenSCAD/libraries/NopSCADlib
```

Common vitamins (confirmed present in the repo, 2026-08-19):

| Category | Data file (constants) | Module file | Module |
|---|---|---|---|
| Ball bearings | `vitamins/ball_bearings.scad` | `vitamins/ball_bearing.scad` | `ball_bearing(type)` |
| Screws | `vitamins/screws.scad` | `vitamins/screw.scad` | `screw(type, length)` |
| Stepper motors | `vitamins/stepper_motors.scad` | `vitamins/stepper_motor.scad` | `NEMA(type)` |
| Brushless motors | `vitamins/blDC.scad` | `vitamins/bldc_motor.scad` | `BLDC(type)` |
| Linear bearings | `vitamins/linear_bearings.scad` | `vitamins/linear_bearing.scad` | `linear_bearing(type)` |

**Not every part size is predefined** -- e.g. MR105 (5×10×4mm) isn't one of
the built-in `BBMR*` constants (closest are `BBMR85`/`BBMR95`). Add your own
in the same tuple format rather than skipping the vitamin because the exact
size isn't there:

```openscad
include <NopSCADlib/vitamins/ball_bearings.scad>
BBMR105 = ["MR105", 5, 10, 4, "silver", 0.5, 0.5, 0, 0]; // name id od w colour or ir fd fw
ball_bearing(BBMR105);
```

If NopSCADlib genuinely has nothing close (an unusual off-the-shelf part),
fall back to a simple bounding-envelope placeholder (a cylinder/box at the
component's real OD/length) rather than skipping collision-checking for it
entirely -- an approximate envelope check beats no check.

## Using vitamins in the workflow

Position purchased hardware in `layout.scad`'s `LAYOUT` array exactly like a
printed part -- `check_plan.py`'s "every layout part must be in the plan"
check already works on any `LAYOUT` entry regardless of whether it maps to
a printed part or a vitamin, no changes needed there. In `assembly.scad`,
`use` the vitamin's file instead of a `parts/*.scad` file for that entry.

For collision-checking (§7): export the vitamin positioned the same way a
printed part is (`-D 'MODE="part"' -D 'PART="bearing_1"'` if you route it
through the same dispatch, or export it directly at its `at()` position) and
include it in the `check_collisions.py` file list alongside the printed
parts' STLs.

`check_connectivity.py` does **not** apply to vitamins (`validate_scad.sh`
only runs it for `parts/*.scad`) -- a purchased part isn't something this
skill is printing, single-body-ness isn't a meaningful question for it.

## BOM (§8) — split Printed from Purchased

The final report's BOM should distinguish, not assume everything was
printed:

| Part | Source | Material/Spec | Quantity | Notes |
|---|---|---|---|---|
| jackshaft_housing | Printed | PETG | 1 | flat, no supports |
| MR105 bearing | Purchased | NopSCADlib `BBMR105` (custom const), 5×10×4mm | 2 | verify seal type when ordering |
| M3×20 cap screw | Purchased | NopSCADlib `M3_cs_cap_screw` | 4 | |

"Print orientation" only makes sense for the Printed rows -- don't ask for
one on a bearing.
