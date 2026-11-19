# P27: checker calculations (Fable calculation audit, 2026-11-19)

Source: independent Fable audit of `scad-modeler/scripts` at ad162cb, 15 reproduced defects + 2 suspected.
Every AC has a failing-first fixture under `scad-modeler/tests/fixtures/p27_*` and, where one line
carries the fix, a mutant in `tests/semantic_mutants.tsv`.

## check_strength.py
- **AC-1** Given a 50x20x2 bar loaded [0, 7.3, 7.3] N at 50 mm (oblique to the principal axes), when
  check_strength runs, then the bending stress is the unsymmetric-bending value (>= 27.3 MPa, the
  Z-only case) and the case FAILs at safety 2. Formula: solve the linear stress field a*x + b*y from
  Mx = int(y*sigma), My = -int(x*sigma) with the full second-moment tensor; max over the outline.
- **AC-2** Given an M3 insert (L 5.7, needs L+1 = 6.7) in a 6.55 mm blind hole, then it FAILs: the
  bottom is bisected to 0.01 mm, not rounded up to a 0.25 mm grid.

## motion_sweep.py
- **AC-3** Given `range_deg: [0, -90]`, then it is swept as [-90, 0] (same positions and verdict as the
  ascending form). `step_deg <= 0` is bad input (rc 2).
- **AC-4** Given a hinge contact declared with `expected_interference_mm` and `min_clearance_mm: 0.3`,
  then the declared pair is held to its interference range only and the motion PASSes when no
  other pair comes within 0.3 mm (the clearance applies to every undeclared pair).
- **AC-5** Given `teeth: 20` on a driven part that is NOT symmetric under a 18 deg turn, then the
  one-pitch shortcut is refused (full range swept, clash found); a symmetric part keeps it.

## check_fasteners.py
- **AC-6** Given `"instances"`, then the instance renders are ADDED to build/positioned/*.stl, not a
  replacement: a cover in build/positioned still blocks the head.
- **AC-7** Given a screw with `head_h: 0` 3 mm from another, then the crossing is reported (zero-length
  segments handled in the segment distance; no NaN).
- **AC-8** Given a fasteners entry without `start` (typo `strat`), then rc 2 naming it.
- **AC-9** Given a positioned mesh that is not watertight, then rc 2 naming it (containment tests on an
  open mesh are meaningless).
- **AC-10** Given an M4 into a 3.9 mm pilot, then "no thread material": the bite ring is at
  r = 0.44 d (pilot at most 0.88 d; ISO tap drills are 0.82-0.84 d, printed pilots run a little over).
- **AC-11** Given a 150 mm and a 300 mm lid covering an unused host hole, then "covers host hole":
  the contact face is sampled at a density set by its area, not a fixed 20000 points over the part.

## check_limits.py
- **AC-12** Given an approved lock, when after approval a clearance pair below the locked default, a
  `ground.tol` above the implicit 0.5, an `expected_interference_mm` hi above the implicit 0 on a
  contact that had none, a changed `force_N` direction, a bigger `step_deg` or a narrower `range_deg`
  is written, then each one FAILs as loosened. Implicit defaults are inventoried at approve.

## check_behavior.py
- **AC-13** Given a body that `import()`s an STL, when the STL changes, then the render cache misses
  (imported files are part of the cache key).
- **AC-14** Given an angle echo printed twice (right side 5, mirrored left 40, max 15), then the worst
  |value| over every match is used and the joint FAILs.
- **AC-15** The loose-piece cache cannot return another pose's result (weak references, not id()).

## check_fasteners.py render cache
- **AC-16** Given an instance or purchased body that imports an STL, when that STL is newer than the
  render, then it re-renders (newest of .scad and imported data files, not .scad only).

## check_features.py
- **AC-17** Given a SOLID Ø8 pin at a declared EXPECTED_HOLE with a Ø20 boss in the same slice, then
  FAIL: a hole is a contour that is an interior ring of a material polygon.

## check_dimensions.py
- **AC-18** Given cube([203, 100, 10]) declared [200, 100, 10] at $fn = 6, then FAIL: the tessellation
  bound only excuses a SHORTER extent (OpenSCAD polygons are inscribed); a longer one gets the floor.

## Not changed (with reason)
- check_collisions `bounded_depth`: suspected only (a thin fin deep in a block measures its thickness).
  Kept: the fixture of the audit failed correctly; recorded in NEXT.md for a measured follow-up.

## P27b (Fable review of P27, same day): 3 false PASS, 3 false FAIL, 1 slowdown in the P27 fixes
- **AC-4b** A declared contact keeps the motion's `min_clearance_mm` unless it states its own (the P27
  exemption covered the whole body pair and hid a 0.1 mm near-miss elsewhere on the lid and box).
- **AC-5b** `teeth` symmetry is tested on every vertex plus samples (a 1x1x2 mm nub on a 120 mm disc slipped).
- **AC-12b** limits.lock schema 2: whole driver set per motion, every contact as an opt-out flag, a contact's
  own clearance vs the approved motion clearance, -0.0 == 0.0 in the force direction; an old lock prints an
  OPEN QUESTION.
- **AC-9b** Open mesh = an edge with an odd face count (4-face edges from touching solids are valid).
- **AC-10b** Thread material from (d - P)/2 + 0.04 d (ISO coarse P, or `pitch`): M10x1 into 9.0 passes.
- **AC-11b** Covered-hole search clusters first and tests one centroid per cluster (344 s -> 12 s).
- **AC-13b** `import(convexity = 4, file = "x")` is followed for the behavior cache key.
- **AC-18b** `offset(delta=)` in the file allows the circumscribed overshoot on the longer side.
