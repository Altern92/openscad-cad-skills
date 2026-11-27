# Example: single-stage spur gear reduction

![Preview](preview.png)

An 11-tooth pinion driving a 66-tooth spur gear (6:1 reduction, module 1.0),
built with `scad-modeler` end to end: calculation table → centralized
params → per-part local coordinates → assembly layout → full validation
chain, including the part this skill is actually for — **verifying the
gears mesh correctly through a full rotation, not just in one static
pose**.

## Run it yourself

```bash
cd scad-modeler/examples/gear_reduction
bash ../../scripts/validate_scad.sh --all
```

Expected: every part renders as one connected body, both declared 5mm bores
measure correctly, each gear turns about its real axis, the centre distance
equals BOSL2 `gear_dist()` (38.845 mm, printed as `OK: centre distance ...`),
and `motion_sweep.py` sweeps the full 360° rotation and finds 0.139 mm of
backlash and no contact anywhere in the cycle. Both parts declare their size and
through-holes, so `dimensions`, `topology` and `declarations` PASS. Exit code 0, ending in
`All executed checks passed (...)`.

Then, before treating it as done:

```bash
python3 ../../scripts/check_rules.py --project-dir .
```

## What this demonstrates

- **`params.scad`** — every dimension in one place, with `assert()`
  invariants (the reduction ratio, the shaft bore vs. the pinion's own
  pitch diameter).
- **Real gear teeth, not placeholder cylinders** — `parts/pinion.scad` and
  `parts/spur.scad` use BOSL2's `spur_gear()`, not hand-rolled involute
  math (SKILL.md §5 explains why: a from-scratch implementation failed
  silently on a degrees/radians unit bug that looked plausible in a
  render but was wrong by ~60x).
- **`layout.scad`** — positions both parts in one shared assembly
  coordinate system via `at()`. Also documents a real, non-obvious BOSL2
  gotcha found while building this example: `layout.scad` must itself
  `include <BOSL2/std.scad>` and `include <BOSL2/gears.scad>` even though
  it never calls a gear function directly, because BOSL2 redefines
  `translate()`/`rotate()` to track internal special variables that a
  gear module positioned through a plain (non-BOSL2-aware) `at()` can't
  otherwise see — read the comment at the top of the file for the full
  explanation.
- **`joints.json`** — a declared `gear_mesh` contact with `"module": 1.0`,
  so the centre distance is checked against BOSL2 `gear_dist()`, and an
  interference window of 0-0.05 mm: correctly spaced and phased teeth do
  not touch. Until P29 (2026-11-27) this example used the textbook
  m·(z1+z2)/2 = 38.5 mm and a 0.5-2.0 mm window that hid the resulting jam;
  the 11T pinion gets an automatic profile shift in BOSL2, so the real
  distance is 38.845 mm. `params.scad` also sets each gear's `gear_spin` so
  a tooth faces a gap.
- **The full validation chain** — connectivity, bore measurement, gear
  axes and centre distance, declared-contact penetration depth, and a full
  motion sweep, all wired into one `validate_scad.sh --all` call. The
  example runs in the regression suite (fixture `example_gear_reduction`).

## What this deliberately skips

This is a 2-part, single-purpose gear pair with an obviously simple
architecture — exactly the case SKILL.md names as safe to skip §0.5
Planning and §0.6 Physical assembly narrative for. It also doesn't model
any purchased hardware (bearings, a real motor shaft) as NopSCADlib
vitamins — see `scad-modeler/references/hardware.md` for that, on a real
assembly where it matters.
