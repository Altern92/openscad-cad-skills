# Setup verification notes (2026-08-16)

Facts below were empirically verified against the actual installed OpenSCAD build
and libraries on this machine, not assumed from documentation or a prior model's
(DeepSeek's) claims. Re-verify if any of this changes (new machine, reinstalled
libraries, etc.) rather than trusting this file blindly forever — same principle
as the rest of this skill.

## OpenSCAD CLI flags (confirmed present via `openscad --help`)

`--hardwarnings`, `--check-parameters=true`, `--check-parameter-ranges=true` all
exist and both the space-separated (`--check-parameters true`) and `=`-joined
(`--check-parameters=true`) forms work.

## OpenSCAD language facts (confirmed by running test files)

- A bare, top-level `assert()` statement is valid OpenSCAD and halts the render
  with the given message on failure.
- Recursive user functions (a function calling itself, e.g. a linear-scan lookup
  over an array) work correctly.
- Trig functions (`sin`, `cos`, `tan`, ...) take **degrees**, always. Passing
  radians silently produces wrong-but-plausible-looking numbers rather than an
  error -- e.g. `tan(20)` = 0.364 (correct for 20°) but `tan(20*PI/180)` = 0.0061
  (wrong by ~60x, because 20*PI/180 in radians is being read as if it were degrees).
  This was the root cause of a bug in an earlier hand-written gear module.
- `module` is a reserved keyword and cannot be used as a variable/parameter name --
  doing so is a hard parse error (`Parser error: syntax error`), not a warning.

## BOSL2 / MCAD install status

As of 2026-08-16, a full, working BOSL2 is installed at
`~/Documents/OpenSCAD/libraries/BOSL2` (56 `.scad` files, cloned from
`https://github.com/BelfrySCAD/BOSL2.git`). `spur_gear(mod=1.0, teeth=11,
thickness=15, shaft_diam=3.175, pressure_angle=20, backlash=0.15)` was
test-rendered against it successfully (`--backend=Manifold --render`, no errors,
1384 triangles, correct-looking 11-tooth profile).

**Before that fix**, `~/Documents/OpenSCAD/libraries/BOSL2/` contained only a
single stray `gears.scad` file (not a real BOSL2 install) -- `include
<BOSL2/std.scad>` failed to resolve, and `gears.scad` itself then errored out
referencing undefined things (`CENTER`, `UP`, `first_defined()`, `is_finite()`)
that live in `std.scad`. The folder *existing* and *sharing BOSL2's name* was not
evidence it was a working install -- had to actually `include` it and render
something before trusting it. Renamed the old folder to
`BOSL2_incomplete_backup` rather than deleting it outright.

## Dimension check (`check_dimensions.py`) -- confirmed working (2026-08-16)

Built from a second DeepSeek DeepThinking pass (`05_deepseek_promptas_matmenu_patikra.md`
in the research folder), which this time correctly flagged its one uncertain
claim ("does `openscad --info` report a bounding box?") instead of asserting it.
Checked directly: `openscad --info` only dumps version/environment info, no
geometry bounding box -- confirms STL export + `trimesh` is the only real option,
as DeepSeek defaulted to.

Also verified directly (not just accepted from the DeepSeek response):
- The `EXPECTED_BBOX` regex still matches correctly even with trailing comment
  text after the closing bracket (as used in `part_template.scad`).
- `check_dimensions.py` needs only `trimesh` -- unlike `check_collisions.py`, it
  does NOT need `scipy`/`python-fcl` (tested in a venv with trimesh alone;
  `mesh.bounds`/`mesh.is_empty` don't hit the graph/connected-components code
  path that `is_convex`/`body_count` do).
- Default tolerance (`max(0.3mm, 1%)`) correctly: passes an exact match, fails a
  deliberate 1mm mismatch on a 10mm test part, and passes a 200mm part despite a
  1.5mm difference (within the wider 1%-based tolerance at that size).
- End-to-end: `validate_scad.sh --all` against two parts, one with a deliberately
  wrong `EXPECTED_BBOX` -- correctly failed and halted before validating the
  remaining part (`set -euo pipefail` doing its job).

`~/Documents/OpenSCAD/libraries/MCAD` is in the same incomplete state (only
`gears.scad` and `involute_gears.scad` present, not a full MCAD clone). Not fixed,
since BOSL2 alone already covers this skill's gear needs -- fix it the same way
(`git clone https://github.com/openscad/MCAD.git`) if MCAD is ever actually needed.

## BOSL2 requires `include`, not `use` -- confirmed by reproducing the failure

`use <BOSL2/std.scad>` followed by `cuboid([...]) { attach(TOP) cyl(...); }` fails:

```
WARNING: Ignoring unknown variable "$tags_shown" in .../BOSL2/attachments.scad
ERROR: Assertion '(is_list($tags_shown) || ($tags_shown == "ALL"))' failed
```

Root cause: `use` imports modules/functions only, not top-level variable
assignments -- BOSL2's default special variables (`$tags_shown`,
`$anchor_override`, `$attach_to`, `$transform`, ...) are declared as top-level
assignments in `std.scad`, so `use` silently drops them and `attach()` then
crashes trying to read one. Switching to `include <BOSL2/std.scad>` fixes it
immediately (verified: a `cuboid()` with an `attach(TOP) cyl(...)` boss rendered
correctly, no warnings, right after making that one change).

This is the exact same `use`-drops-top-level-variables behavior already
documented for this project's other OpenSCAD work (see the `openscad-cad` skill,
`nema23_fan_shroud` project) -- worth remembering as a general rule for *any*
OpenSCAD library, not just BOSL2: if a library defines default parameters as
top-level variables (not inside a function/module), it needs `include`, not `use`.
`use` is only safe for libraries whose public API is 100% modules/functions with
no top-level state.

## `use` also skips a file's top-level *statements*, not just variables (confirmed 2026-08-16)

Found while dogfooding this skill end-to-end (see below): `use <file.scad>` does not
execute `file.scad`'s own top-level module-call statements either (e.g. a part
file's trailing unconditional `part_geometry();`), the same way it doesn't import
top-level variable assignments. Confirmed with a minimal repro: a child file with a
top-level variable, a module using that variable, and a stray top-level
`translate(...) cube(...)` junk statement -- a parent that only `use`s the child and
calls its module rendered a mesh with the exact bounding box of the module's own
geometry, sized correctly from the child's internal variable, with no trace of the
junk statement's geometry.

Practical consequence for this skill: `assembly.scad` must `use` its part files, not
`include` them (see SKILL.md §6) -- `include` would also run each part file's own
trailing unconditional render call, silently duplicating that part's geometry on top
of the positioned copy placed via `at()`.

## Validation-script rework (2026-08-18) — what was verified, and how

Three changes, prompted by an external review of this skill set. Marked by how
each claim was established, because the two are not equally strong.

**Derived mathematically, then checked numerically in Python:**
- OpenSCAD's facet count is `$fn > 0 ? max(3,$fn) : ceil(max(min(360/$fa,
  2πr/$fs), 5))`. Mirrored in `scripts/scad_tessellation.py`.
- Inscribed-polygon deficit is `d·(1−cos(180/n))`. At `$fa=2, $fs=0.3` that is
  0.0031 mm at Ø20 and 0.0305 mm at Ø200 — versus the old flat
  `max(0.3 mm, 1%)` tolerance of 0.3 mm and 2.0 mm respectively. The old default
  was therefore 10–65× too loose to function as a mesh-error gate. An
  independent review derived the same figures.
- **Across-flats deficit and bounding-box deviation are numerically the same
  expression but describe different things**, and conflating them is the trap:
  OpenSCAD places a vertex at angle 0, so when `n` is divisible by 4 (and
  `$fa=2` gives exactly `n=180`) the bbox touches the ideal radius on every axis
  and the bbox error is ~0. `d·(1−cos(180/n))` is a safe *upper bound* for the
  bbox — appropriate for a tolerance — while it is the *realised* error
  flat-to-flat, which is what makes a hole too tight. A bbox check consequently
  cannot detect an undersized bore; only feature-level checking or the Pattern 0
  compensation addresses that.

**Verified by execution (Python 3, trimesh 5.0.0, python-fcl, manifold3d):**
- `check_dimensions.py`: passes an exact 40×20×15 match, fails a deliberate 1 mm
  X mismatch, skips cleanly when no `EXPECTED_BBOX` is declared, and honours
  `--abs-tol` as a documented escape hatch.
- The `$fa`/`$fs` parser resolves through `include <../params.scad>` and ignores
  commented-out assignments. **A line-anchored regex would have silently missed
  `$fs` in this skill's own template**, which writes `$fa = 2; $fs = 0.3;` on one
  line — the fallback to OpenSCAD's defaults would then have produced a
  tolerance ~35× too loose while looking like it worked. Caught by testing, not
  by reading.
- `check_collisions.py`: all four exit codes reproduced — 0 pass, 2 degraded
  (non-watertight mesh), 3 fail, 4 usage. Verified that an undeclared 0.1 mm
  overlap fails, that the same overlap declared as a press fit passes, that a
  0.2 mm gap fails against `--min-clearance 0.3`, that a declared press fit
  whose parts don't touch fails, and that `--strict` promotes a non-watertight
  mesh from degraded to fail.
- The old docstring/behaviour mismatch was real: it promised a non-zero exit for
  a non-watertight mesh and only printed a warning. Confirmed against the code
  before rewriting.

**Verified against OpenSCAD's upstream source (2026-08-18), closing questions
this rework had left open:**
- `src/core/primitives.cc` emits circle/cylinder vertex `i` at
  `phi = (360.0 * i) / num_fragments`, i.e. **there is always a vertex at angle
  0**. That settles the phase question the bbox derivation depends on: with `n`
  divisible by 4 (and `$fa=2` gives exactly `n=180`) vertices land on all four
  axes and the bbox error is zero, while the across-flats deficit is unchanged.
  The Pattern 0 compensation does not depend on phase at all, and the bbox
  tolerance uses the phase-independent upper bound, so both were already correct
  — but they are now correct *for a checked reason*.
- The fragment formula is `ceil(fmax(fmin(360/fa, r*2*PI/fs), 5))` with an
  `$fn > 0` short-circuit, plus a `r < GRID_FINE` short-circuit to 3.
  `src/geometry/Grid.h` gives `GRID_FINE = 0.00000095367431640625` (2^-20) —
  below a micron of radius, so dimensionally irrelevant; mirrored in
  `scad_tessellation.py` for fidelity, omitted from `patterns.scad`.

**Not verified — still open:**
- Whether `openscad --summary bounding-box` can replace the STL→trimesh
  round-trip entirely (no OpenSCAD binary in the environment where this rework
  was done). Settle it with `openscad --summary all --summary-file - model.scad`
  on a current build; if it reports the bbox directly, `check_dimensions.py`
  gains a much cheaper path.
- Whether the `0.005 mm` numeric floor is right. It is reasoned from float32 STL
  storage (~2.4e-5 mm ulp at 200 mm), not measured against real exports.

## End-to-end dogfood run (2026-08-16)

Ran the full workflow once, top to bottom, on a synthetic (not real-project) 2-part
gear assembly -- calculation table, `params.scad`, `layout.scad`, two part files
(one with a BOSL2 `attach()` boss, one with a BOSL2 `spur_gear()`), `assembly.scad`
with the MODE switch, `validate_scad.sh --all`, per-part positioned STL export via
`-D MODE="part"`, `check_collisions.py`, and a rendered preview. This was the one
thing the skill had never been run through before, only unit-tested piece by piece.

Findings:
- The `include`-vs-`use` bug above, and the vague `at(PART) children();` line in the
  old §6 (modules aren't values in OpenSCAD -- there's no way to look one up by
  string without an explicit if/else dispatch) -- both fixed in SKILL.md.
- The collision checker caught a real design mistake in the synthetic assembly (a
  gear housing footprint sized too generously for the actual center distance, which
  really did overlap the motor mount) -- fixed at the source per SKILL.md's own
  instruction (shrank the housing margin and mount footprint, recomputed from the
  same params.scad variables) rather than loosening the check, then re-ran clean.
- `gear_dist()` returned a different center distance than the naive
  `(t1+t2)*mod/2` formula would have for the first (12/36-tooth) attempt, a live
  example of why SKILL.md §5 says to use it instead of hand-deriving.
- Everything else (calculation table -> params.scad -> layout.scad -> part files ->
  assembly.scad -> validate_scad.sh -> check_collisions.py -> preview render) worked
  exactly as documented, no other deviations needed.
