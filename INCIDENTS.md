# Incidents log

Append-only. One entry per real bug found and fixed -- a validation check
catching something wrong, a failure found by actually running or measuring
something, or an inaccuracy found by cross-checking a claim against its
source. This is raw data for a future review pass (Phase 2: periodically read
this log and look for patterns worth promoting into a permanent SKILL.md/
references rule), not curated advice on its own. Don't edit past entries --
if a fix needs revising later, add a new entry that supersedes it and say so.

Not every skill file edit belongs here -- only things that were actually
*wrong* (a bug, a bad test, an inaccurate claim), not routine additions.

## Pattern analysis (Phase 2, 2026-08-19)

First real pass over the accumulated log (9 entries, 2026-08-16 to
2026-08-19) -- three recurring patterns, not just isolated incidents. For
each: the concrete mechanism Perplexity research turned up, honestly ranked
by precedent strength. **None of this is implemented yet** -- research and
write-up only, per explicit instruction; do not build from this section
without a separate go-ahead.

### Pattern 1 -- a declared/documented value drifts from what the live code
actually computes, after the live computation is upgraded

Instances: CD1/CD2 vs `gear_dist()` (below), `EXPECTED_BBOX` Z rounding
(below), `jackshaft_bearing_wall_at_diff` assert omitting real clearance
terms (below). Three of nine entries -- the strongest cluster in the log.

**Proposed mechanism** (moderate precedent -- fits "contract programming" /
dependency-integrity thinking, not a single named standard): stop writing
safety margins as separate handwritten numbers. Make the margin a function
that *calls the same helper function* the real geometry-cutting code calls
for its clearance terms, so there is no parallel arithmetic to drift apart
in the first place:

```scad
function shaft_clearance(d_nom, fit_class, printer_bias) =
    d_nom + fit_delta(fit_class) + printer_bias;
function shaft_safety_limit(...) =
    shaft_clearance(...) - safety_subtraction(...);
assert(shaft_safety_limit(...) > min_wall,
       str("shaft_safety_limit=", shaft_safety_limit(...)));
```

Solo-scale guard version (no full parser needed): a small script that scans
`.scad` files for `assert(`/`EXPECTED_*` and checks whether the formula it
references shares a helper-function name with the "live" formula used
elsewhere for the same quantity -- a lightweight dependency map, not full
static analysis.

### Pattern 2 -- a correctly-reasoned intentional contact (e.g. a clamshell
split line) never gets formalized into the declaration file meant to check
for exactly it

Instance: `check_collisions.py` failing on `gearbox_case_bottom`/`top`
(below) despite the touch being correctly identified as benign during the
original design session.

**Proposed mechanism** (most bespoke of the three -- no single standard
pattern, but aligned with BIM/CAD clash-tolerance practice): don't just
report "collision" -- classify the event (interference / contact / near
miss) and auto-suggest a declaration stub for human confirmation instead of
relying on someone remembering to write one by hand:
- overlap volume > 0 → real interference, flag as before.
- overlap volume == 0 and separation ≤ a touch tolerance (~0.02-0.05mm for
  printed parts) → candidate intentional touch, auto-generate a
  `joints.json` stub (part pair, `intentional_touch`, evidence, tolerance
  used) for the human/agent to confirm rather than hand-write from scratch.
- small positive gap below a separate, larger near-miss tolerance
  (~0.1-0.2mm) → flag as a near-miss, do NOT auto-declare (this is likely a
  real design sensitivity, not a benign touch).
- stability check: if a tiny parameter jitter flips the verdict between
  touch and overlap, treat it as a real problem, not benign -- don't
  auto-suggest in that case.

### Pattern 3 -- one shared params.scad variable is referenced by multiple
parts that each have a DIFFERENT real hard constraint, and only one
context's constraint gets checked

Instance: `axle_d=6mm` shared across the diff-side stub (photo-measured,
~6mm) and the wheel_hub end (MR105 bearing, fixed 5mm ID) (below) -- only
the diff-side context was ever actually verified against.

**Proposed mechanism** (strongest precedent of the three -- directly maps to
established CAD constraint-dependency-graph research and to dependency
tracking in systems like PostgreSQL, which won't let you break an object
with unresolved dependents): a parameter provenance/context manifest. Each
part file that consumes a shared parameter for a hardware-fit purpose
declares which context and which constraint it's satisfying:

```scad
use_param("axle_d", "diff_stub_end", "photo_measured_~6mm");
use_param("axle_d", "wheel_hub_bearing_end", "press_fit_MR105_bore5mm");
```

A small checker scans for every parameter referenced by ≥2 `use_param()`
contexts and fails if any context's declared constraint was never actually
exercised by a matching `assert()` nearby -- catching exactly the failure
mode where one end of a shared dimension was checked and the other was
silently assumed compatible. Doesn't require a full requirements-
traceability system -- "no shared parameter may fan out into multiple hard
constraints without a manifest entry (and a real assert) for each fan-out."

### If/when this gets built

Perplexity's own suggested build order, if these get implemented later:
(1) the shared-helper-function convention for Pattern 1 (cheapest, closes
the strongest cluster), (2) the clash classifier + auto-suggest for Pattern
2, (3) the parameter context manifest for Pattern 3 (most novel tooling,
build last). Not scheduled -- logged here for when there's a go-ahead.

## Entry format

```
### YYYY-MM-DD -- <one-line what broke>
- **Where:** <file/project>
- **Symptom:** <what was observed>
- **Root cause:** <why, once diagnosed>
- **Fix:** <what changed>
- **Already promoted to a rule?** <yes, in <file> / not yet>
```

## Entries

### 2026-08-19 -- validate_scad.sh's fail-fast (set -e) let one unrelated failure mask whether OTHER checks ran at all
- **Where:** `scad-modeler/scripts/validate_scad.sh`, `scad-modeler/scripts/check_rules.py`,
  `scad-modeler/rules_manifest.yaml` -- discovered when a different, parallel
  Claude Code session ran a full re-validation of
  `esp32_rc_modelis/mechanical/steering_reduction_gearbox/` (prompted by
  this session, after this skill's tooling matured well past that project's
  last validation round) and reported its final `check_rules.py` output.
- **Symptom:** R-04 (connectivity) and R-09 (motion sweep) were marked FAIL
  in the cited output, immediately followed by the model's own prose
  explaining "the gate stops early [at R-11's unresolved Critical
  assumption], but I manually, separately confirmed the geometry itself is
  clean." That is an unverified self-assessment standing in for a gate that
  never actually produced a result for those two rules -- the exact failure
  mode the whole L2-L4 rules-enforcement design exists to eliminate, now
  demonstrated happening in practice on real output, not hypothetically.
- **Root cause:** `validate_scad.sh` used `set -e`, so the FIRST failing
  command (in this case `check_assumptions.py`, gating R-11, completely
  unrelated to R-04/R-09) aborted the entire script before the parts loop,
  bore-reachability check, or mechanics auto-trigger ever ran. Separately,
  `rules_manifest.yaml`'s R-04 and R-09 both gated on the WHOLE script's
  exit code (`bash validate_scad.sh --all`) as a proxy for one specific
  check's result -- even after fixing the fail-fast issue, a shared exit
  code still can't distinguish "this specific check failed" from "some
  other independent check in the same run failed."
- **Fix:** two-part. (1) `validate_scad.sh` no longer uses `set -e`; every
  independent check runs regardless of earlier failures and prints its own
  `CHECK_RESULT <name>=PASS|FAIL|SKIP` line; the script's own exit code is
  still non-zero if anything failed, for a human running it directly.
  `validate_file()` returns instead of exiting on a render failure so other
  parts still get attempted. (2) `check_rules.py` gained an optional
  `success_pattern` field: when a rule's gate is a multi-purpose script,
  its verdict is decided by searching that gate's own output for the
  rule's specific `CHECK_RESULT` marker, not by the shared process exit
  code. R-04/R-09 now use `success_pattern: "CHECK_RESULT (connectivity|
  mechanics)=(PASS|SKIP)"`. Gate output is cached by literal command string
  so R-04 and R-09 sharing one `validate_scad.sh --all` invocation doesn't
  render twice. Tested directly against the reported scenario: a project
  with a real unresolved Critical assumption (R-11 correctly FAIL) and
  otherwise-clean geometry (a tangent gear pair with correct motion) now
  shows R-04=PASS, R-09=PASS, R-11=FAIL with no self-reported "I checked
  separately" needed -- and a genuinely broken gear mesh in the same setup
  correctly still shows R-09=FAIL. Full regression re-run (empty project,
  bash 3.2, gross overlap, clean tangent case) confirmed unaffected.
- **Already promoted to a rule?** Yes -- fixed directly in `validate_scad.sh`,
  `check_rules.py`, and `rules_manifest.yaml`.

### 2026-08-19 -- check_collisions.py's declared-contact check upgraded from a volume heuristic to exact penetration depth
- **Where:** `scad-modeler/scripts/check_collisions.py`, following up on the
  same-day volume-plausibility-bound fix (below) after asking Perplexity
  deep-research for an evidence-based critique of the whole validation
  workflow, specifically whether a better geometric quantity than
  boolean-intersection volume exists for verifying a declared
  `expected_interference_mm` spec.
- **Symptom (of the interim fix, not a bug in this fix):** the same-day
  volume-plausibility-bound fix (25% of the smaller part's own volume) could
  only catch GROSS overlap, not a real out-of-spec interference within
  plausible range -- confirmed directly: two 10mm cubes forced to overlap by
  0.1mm (correct, within a declared 0.05-0.15mm press-fit spec) and by
  0.3mm (wrong, outside that same spec, 2x the upper bound) produced overlap
  volumes of 10mm^3 and 30mm^3 respectively -- both comfortably under the
  25%-of-1000mm^3 threshold, so the plausibility bound would have silently
  passed BOTH as OK, unable to distinguish a correct fit from one 3x too
  deep.
- **Root cause:** a boolean-intersection volume is fundamentally the wrong
  unit to compare against a linear mm interference spec -- confirmed by
  research citing GJK/EPA-based penetration depth as the standard quantity
  for exactly this in contact mechanics and robotics, available via the
  same FCL backend `check_collisions.py` already depends on through
  `trimesh.collision` (previously only used for boolean overlap detection
  and minimum-distance queries, not its penetration-depth output).
- **Fix:** `manager.in_collision_internal(return_data=True)` now also
  returns FCL `ContactData` per contact point; the max `.depth` (mm) across
  a pair's contact points is compared directly against the declared
  `[lo, hi]` mm range. Not an exact whole-shape EPA minimum-translation-
  distance (would need convex decomposition first) but a correctly-unified,
  much more precise measure than volume. The old volume-plausibility bound
  is kept only as a defensive fallback for the rare case FCL returns no
  contact data for a pair trimesh otherwise reports as colliding. Tested:
  the 0.1mm/0.15mm-spec cube case now correctly passes with depth measured
  as exactly 0.100mm; the 0.3mm cube case now correctly fails with depth
  measured as exactly 0.300mm (previously silently passed); the full
  synthetic gear-assembly regression (tangent-touch pass, 10mm-forced-
  overlap fail, full `validate_scad.sh --all` integration) still passes
  with the new depth-based path, correctly reporting the failing case's
  measured depth as ~9.98mm.
- **Already promoted to a rule?** Yes -- fixed directly in the script.

### 2026-08-19 -- check_collisions.py accepted ANY overlap volume for a declared contact with a nonzero range
- **Where:** `scad-modeler/scripts/check_collisions.py`, discovered while
  building and testing the mechanics auto-trigger (below) against a
  deliberately-broken synthetic gear pair.
- **Symptom:** two cylinders forced to overlap by 10mm (1114.74mm³, ~44% of
  the smaller cylinder's own volume -- an obviously wrong, unbuildable
  position) reported `OK (intentional gear_mesh)` because they were declared
  as a contact pair with `expected_interference_mm: [0.0, 0.5]`. The check's
  own logic only ever compared the declared range's upper bound against zero
  (`if hi <= 0.0 and vol > 0.0: FAIL`); any declared range with `hi > 0`
  skipped volume validation entirely and always reported OK, regardless of
  how large the real overlap was.
- **Root cause:** a real measurement-type mismatch the code's own comment
  half-acknowledged ("volume is a severity signal, not a linear depth") but
  didn't actually act on for the common case (`hi > 0`) -- only the `hi <=
  0` edge case was enforced. A boolean-intersection volume can't be compared
  exactly to a linear interference-depth range without knowing contact area,
  but "can't compare exactly" was implemented as "don't compare at all,"
  silently disabling the check for every declared press-fit/gear-mesh
  contact with any nonzero tolerance -- which is most of them.
- **Fix:** added a plausibility bound: for `hi > 0`, overlap volume beyond
  25% of the smaller part's own volume now fails as `IMPLAUSIBLE DECLARED
  OVERLAP` regardless of the declaration. Not an exact fix (still can't
  derive true linear interference from volume alone), but catches gross,
  obviously-wrong overlap while still passing legitimate small interference
  fits. Tested: the 1114.74mm³ case now correctly fails; a small legitimate
  ~12mm³ overlap (0.5% of the smaller part's volume) still correctly passes;
  the original zero-overlap tangent case still passes clean.
- **Already promoted to a rule?** Yes -- fixed directly in the script.

### 2026-08-19 -- mechanics (motion) checks required someone to remember to run them
- **Where:** `scad-modeler/scripts/validate_scad.sh`.
- **Symptom:** `check_collisions.py` and `motion_sweep.py` both existed and
  worked, but neither was ever auto-triggered by `validate_scad.sh --all` --
  a moving assembly could pass full validation without either ever running,
  exactly the gap the user's own vision (point 4: "jei tai buna judancios
  detales, automatiskai tai ir planuoja, net patikrina mechanika") called
  out. `rules_manifest.yaml`'s R-09 could only mark this MANUAL.
- **Root cause:** two of this skill's own reference docs
  (`intake_and_analysis.md`, `mechanics_and_motion_planning.md`) each
  independently proposed a `design_manifest.json.motion` auto-trigger with
  mutually incompatible schemas (an object with `has_kinematics` vs. an
  array of driver/driven joint objects) -- and BOTH were different from
  `motion_sweep.py`'s own real, already-tested interface, which reads a
  `motion` array from `joints.json` (the same file `check_collisions.py`
  already uses for contacts). Neither doc's proposal matched the working
  script.
- **Fix:** wired the trigger to what `motion_sweep.py` actually reads:
  `validate_scad.sh --all` now detects a non-empty `joints.json#motion`
  array, renders each part positioned in assembly space via `assembly.scad`'s
  `MODE="part"`/`PART="<name>"` switch (SKILL.md §6 -- the per-part STLs the
  main loop produces are in local coordinates, not valid for cross-part
  interference checking), then runs `check_collisions.py` (static
  precondition) and `motion_sweep.py` (dynamic sweep) automatically, in that
  order. Tested end-to-end against a real two-part synthetic gear assembly:
  clean tangent case passes, a deliberately-broken deep-overlap case fails
  with a non-zero exit code that propagates through `set -e`, and a
  no-motion/no-joints.json project is unaffected (mechanics block correctly
  skipped). `rules_manifest.yaml` R-09 updated to `kind: auto` accordingly.
- **Already promoted to a rule?** Yes -- fixed directly in
  `validate_scad.sh` and `rules_manifest.yaml` R-09.

### 2026-08-19 -- validate_scad.sh crashed on an empty parts/ directory under macOS's default bash
- **Where:** `scad-modeler/scripts/validate_scad.sh`, and (root-caused from
  the same bug) `scad-modeler/scripts/check_rules.py`'s first version.
- **Symptom:** running the new `check_rules.py` (built this session to close
  the L4 rules-enforcement gap) against a bare project directory with no
  `parts/*.scad` files yet crashed with `parts[@]: unbound variable` instead
  of printing the intended `WARNING: no files found under parts/*.scad`.
  Never seen before this session because every prior test run this whole
  session happened to have at least one part file present, so the empty-array
  code path was never actually exercised.
- **Root cause:** two independent problems that happened to surface
  together. (1) macOS ships bash 3.2.57 as `/bin/bash` (frozen at the GPLv2
  license boundary, no 4.4+); bash <4.4 treats `"${array[@]}"` on a
  declared-but-empty array as an unbound variable under `set -u`, even
  though `${#array[@]}` correctly reports 0 -- confirmed directly: `arr=()`
  under `set -u` fails on `for x in "${arr[@]}"` but not on
  `${#arr[@]}`. `validate_scad.sh`'s `for scad in "${parts[@]}"; do` hit
  this exactly. (2) Separately, `check_rules.py`'s first version ran each
  gate command via `subprocess.run(cmd, shell=True, ...)` without passing
  `cwd=project_dir` -- `validate_scad.sh` and its relative-path globs assume
  the project directory IS the working directory, not an argument, so the
  gate was silently checking whatever directory `check_rules.py` itself was
  invoked from.
- **Fix:** `validate_scad.sh` now uses the `${parts[@]+"${parts[@]}"}` /
  `${built_stls[@]+"${built_stls[@]}"}` idiom (a standard bash
  version-portable empty-array guard) instead of bare `"${array[@]}"`.
  `check_rules.py` now passes `cwd=project_dir` to every gate subprocess.
  Both re-tested: an empty project directory now correctly prints the
  warning and passes; a populated one still passes; the fixes were verified
  against real bash 3.2 directly (`/bin/bash -c '...'`), not just assumed
  from documentation.
- **Already promoted to a rule?** Yes -- fixed directly in both scripts;
  no separate prose rule needed since this is a portability bug, not a
  process gap.

### 2026-08-19 -- belt-and-pulley stage passed every geometry check but could never physically be tensioned
- **Where:** `esp32_rc_modelis` (steering/reduction belt drive, exact part
  file not captured in the source transcript) -- a different, parallel
  Claude Code session's own work, self-diagnosed and written up in a
  blunt post-mortem shared with this session; not fixed directly here.
- **Symptom:** two pulleys modeled at fixed, non-adjustable centers,
  sized against a belt pitch length -- every declared geometry check
  (bbox, bore diameter, part-to-part collision in final position) passed.
  The design was still physically un-buildable: a non-stretch GT2 belt
  cannot be installed onto two pulleys whose centers are both fixed, with
  no tensioner, no idler, and no way to shorten the effective path during
  assembly.
- **Root cause:** category-B blind spot -- every check in this chain
  validates parts in their *final assembled position*; none of them
  simulate the *process* of getting a part into that position. A belt
  loop closing around two fixed centers with zero slack has no assembly
  path, and nothing in geometry-only validation asks "can this actually
  be installed," only "does it collide once installed."
- **Fix:** Not fixed by this session (source project, another session's
  work) -- motivated `scad-modeler/SKILL.md` §0.6 "Physical assembly
  narrative," which requires stating the installation path for any
  belt/bearing/fastener feature in writing before its geometry is coded.
- **Already promoted to a rule?** Yes -- `SKILL.md` §0.6 (this session,
  2026-08-19), though as prose/checklist only -- no automated check can
  catch "this belt architecture has no tensioner," that's a design-review
  judgment call, not a geometry predicate.

### 2026-08-19 -- three bearing bores measured correctly but were sealed behind unbored material with no path to the outside
- **Where:** a gearbox frame with three bearing towers, each modeled as a
  cylinder bored perpendicular through its own center axis -- a
  different, parallel Claude Code session's own work, self-diagnosed and
  written up in a blunt post-mortem shared with this session.
- **Symptom:** `check_features.py` correctly measured each bore's
  diameter *at the declared probe point* and passed; `check_connectivity.py`
  reported each tower as one clean, watertight body. Both were true and
  both missed the real problem: every one of the three bores was sealed
  behind ~8mm of solid, un-bored material, with no path connecting the
  bore to any exterior surface. The part was completely unassemblable --
  a bearing could never be inserted -- and nothing in the validation chain
  said so.
- **Root cause:** category-B/C blind spot -- a bore that measures the
  right diameter *at its seat* proves nothing about whether material in
  the way *between* the seat and the outside was ever actually removed. A
  fully enclosed internal cavity is still one connected, perfectly valid
  watertight shell; `body_count==1` and correct-diameter-at-one-point are
  both necessary but not sufficient for "this hole goes anywhere."
- **Fix:** The other session's §7 addition was prose + an inline code
  example only, not a runnable check -- itself a live instance of the
  "log is inert" mistake this whole post-mortem was about. This session
  turned it into `scad-modeler/scripts/check_bore_reachability.py`: a
  point-containment scan (`trimesh.contains()`, needs `rtree`) along a
  declared bore axis from a `bores.json` entry, wired into
  `validate_scad.sh --all` (opt-in via `bores.json`'s existence, runs
  once against every rendered part STL). Tested against synthetic
  fixtures matching this exact geometry -- a tower with a bore drilled
  only halfway through correctly failed (blocked at the first
  unreached point), the same tower with a full-depth bore correctly
  passed -- and confirmed end-to-end through a real `validate_scad.sh
  --all` run in both states.
- **Already promoted to a rule?** Yes -- `scad-modeler/scripts/check_bore_reachability.py`,
  wired into `validate_scad.sh`, referenced from SKILL.md §0.6/§7.

### 2026-08-19 -- a bearing tower overlapped a motor mount by 419mm³, invisible because both lived inside one part's `union()`
- **Where:** a gearbox frame part combining a bearing tower and a motor-
  mounting cradle in a single `union()` -- a different, parallel Claude
  Code session's own work, self-diagnosed and written up in a blunt
  post-mortem shared with this session.
- **Symptom:** the part rendered, exported as one watertight STL, and
  passed every check in the chain -- `check_collisions.py` never saw a
  problem because it only ever compares *separately exported* STL files
  against each other. Once the tower and the cradle were `union()`-ed
  together into one part, they stopped existing as distinguishable
  objects to any tool downstream, so a real 419mm³ overlap between them
  was structurally invisible, not just missed.
- **Root cause:** category-C blind spot -- `union()` of two overlapping
  solids is still one valid, single-body, watertight shell; nothing about
  that operation records or exposes that an overlap happened. The whole
  collision-checking approach in this skill is built on comparing
  distinct STL files, which by construction cannot see inside one.
- **Fix:** The other session's §7 addition was prose + an inline code
  example only, not a runnable check -- itself a live instance of the
  "log is inert" mistake this whole post-mortem was about. This session
  turned it into `scad-modeler/scripts/check_subfeature_overlap.py`:
  pairwise boolean-intersection volume between solo-exported sub-feature
  STLs, with `--exempt` for declared intentional fusions. Tested against
  synthetic fixtures -- two overlapping boxes correctly failed with the
  exact expected overlap volume (300mm³ for a known 10x10x3mm overlap
  region), two clear boxes correctly passed, and the overlapping pair
  correctly passed once declared via `--exempt`. NOT wired into
  `validate_scad.sh` -- unlike the bore check, this needs an extra export
  step (each sub-module rendered solo, pre-`union()`) that the normal
  per-part render doesn't produce, so it stays a manual command
  documented in SKILL.md §7, the same pattern as `check_collisions.py`.
- **Already promoted to a rule?** Yes -- `scad-modeler/scripts/check_subfeature_overlap.py`,
  documented as a manual step in SKILL.md §0.6/§7 (not auto-run, by design).

### 2026-08-19 -- short blind pilot holes near a curved tower wall left tiny negative-volume "ghost" bodies, not a real design error
- **Where:** `esp32_rc_modelis/mechanical/steering_reduction_gearbox/parts/
  gearbox_frame.scad` (`cap_pilot_holes_x`) and `bearing_cap.scad` -- a
  different, parallel Claude Code session's own work while fixing the
  incident below (jackshaft bearing axial retention); diagnosed from a
  shared transcript, not fixed directly by this session.
- **Symptom:** after adding M2 self-tap pilot holes for the new
  `bearing_cap`, `trimesh.body_count`/`.split()` reported extra
  disconnected bodies -- small, consistently NEGATIVE-volume shards
  (~-10mm³ to -16mm³, i.e. inverted normals) near the pilot hole location.
  Six debug variants were tried (removing a `-0.1mm` pre-offset, raising
  `$fn` 32→64, widening the hole 1.6mm→2.0mm) -- none of them cleared it.
  Only two configurations came out clean: a hole with a much larger
  diameter (5mm), and a hole deliberately cut with generous overlap past
  the tower's true outer surface instead of a precisely-sized blind depth.
- **Root cause:** the pilot hole's outer end landed almost exactly tangent
  to the tower's own curved outer cylindrical surface -- a near-tangent
  intersection between two curved CSG surfaces. At that near-tangency,
  floating-point/mesh-tessellation precision in the CGAL/Manifold boolean
  engine can leave a tiny inverted-normal shard behind instead of a clean
  cut, and the effect is insensitive to `$fn`/diameter tweaks that don't
  change the tangency condition itself -- only genuine geometric margin
  (bigger diameter, or a cut that clearly crosses the real surface with
  overlap) fixes it. This is a known category of CSG boolean fragility
  (grazing/near-tangent intersections), not a logic bug in the OpenSCAD
  code, and not a real disconnected-body design error either -- a false-
  positive-*adjacent* case for `check_connectivity.py`: the check correctly
  reports extra bodies, but the fix is a modeling-margin change, not
  evidence the part is actually two pieces.
- **Fix:** Not fixed/confirmed by this session -- diagnosed and relayed as
  a recommendation to the other session: replace the short blind pilot hole
  with either a full through-hole, or a blind cut that starts clearly
  outside the tower's outer surface with generous overlap margin, rather
  than a depth calculated to land precisely at the wall.
- **Already promoted to a rule?** not yet -- candidate for a part-file
  modeling note ("give a boolean cut genuine overlap margin past a curved
  surface it's not meant to just graze") and/or a `check_connectivity.py`
  docstring note ("a small negative-volume disconnected body is often a
  tangent-CSG-boolean artifact from a blind cut near a curved surface --
  try more overlap/diameter before assuming the part design itself is
  wrong").

### 2026-08-19 -- gearbox_frame.stl rendered as two physically disconnected bodies
- **Where:** `esp32_rc_modelis/mechanical/.../gearbox_frame.scad` (a different,
  parallel Claude Code session's own work; reported directly by that session)
- **Symptom:** a part meant to be printed as one solid piece was actually two
  unconnected bodies -- a floating disc (~1043mm³, bounds X:±9mm, Z:25-29mm)
  matching the upper bearing tower exactly, visible as a piece "hanging in
  air" in a render. `check_dimensions.py` passed (same overall bbox either
  way) and `check_collisions.py` passed (it only checks BETWEEN separate STL
  files, never within one file's own geometry).
- **Root cause:** fixing a collision between the tower's support legs and a
  worm gear's teeth widened the legs' radius from 7mm to 15mm. That solved
  the collision. Nobody re-checked whether the legs, at the new radius, still
  touched the disc they were supposed to hold up -- they didn't (disc radius
  9mm, legs' new inner edge 12mm, a permanent 3mm gap). The session had a
  working tool for exactly this (`trimesh` connected-body count) and used it
  manually, once, after the bug was already visible by eye -- it was never a
  standard, mandatory validation step.
- **Fix:** promoted directly to a rule this session -- `scripts/
  check_connectivity.py` (new; uses `trimesh.body_count`/`.split()`) is now
  wired into `validate_scad.sh` as a MANDATORY, default-on check for every
  part (opt out via `// EXPECTED_BODIES: N` for the rare genuinely-multi-body
  part). `SKILL.md` §7 also now says explicitly: after any geometry fix,
  re-run the whole validation cycle, not just the one check that was failing
  -- the reporting session named this as the second, broader root cause
  (stopped the moment `check_collisions.py` said OK).
- **Already promoted to a rule?** Yes -- `scad-modeler/SKILL.md` §7,
  `scripts/check_connectivity.py`, `scripts/validate_scad.sh`,
  `templates/part_template.scad` (all this session, 2026-08-19).

### 2026-08-18 -- rear_axle assembly had undocumented collisions across nearly every part pair
- **Where:** `esp32_rc_modelis/mechanical/rear_axle/` (built in a separate/
  parallel session, not this one)
- **Symptom:** the user spotted a visible overlap in a rendered screenshot;
  running `check_collisions.py` on it found far more than the single pair
  already flagged in a code comment — the axle tubes and motor mount also
  collided with both the diff carrier and the jackshaft housing.
- **Root cause:** the reduction-scheme architecture and a key gear module
  value were still unresolved/contradictory across prior documents when
  detailed calculations and part geometry were written. Work proceeded
  straight into the calculation table and geometry before the mechanical
  concept was actually settled, and a center distance (CD2=25mm) was locked
  in before checking whether it left room for two housings' full wall
  thickness.
- **Fix:** not fixed in that project itself (out of scope for this session)
  -- but directly motivated a new `scad-modeler` §0.5 "Planning" stage
  (decision log + lightweight architecture comparison + dependency ordering)
  required before the calculation table, so a design commits to numbers only
  after the concept is genuinely settled.
- **Already promoted to a rule?** Yes -- `scad-modeler/SKILL.md` §0.5 and
  `scad-modeler/references/planning.md` (this session, 2026-08-19).

### 2026-08-18 -- selftest.py's bad-bore check never actually failed
- **Where:** `scad-modeler/scripts/selftest.py`
- **Symptom:** the self-test's own headline claim ("UNcompensated bore fails,
  as it must") reported FAIL -- `check_features.py` returned OK on the
  deliberately-bad bore instead of catching it.
- **Root cause:** both the compensated and uncompensated test cylinders
  shared the test file's fine `$fa=2, $fs=0.3`, so the "bad" one was only
  ~0.006mm short of nominal -- inside `check_features.py`'s own 0.05mm
  default tolerance. The test's premise (a meaningful deficit) never held at
  those facet settings.
- **Fix:** forced the uncompensated cylinder to OpenSCAD's true defaults
  (`$fa=12, $fs=2`) via a local block override, producing a real ~0.23mm
  deficit that correctly fails.
- **Already promoted to a rule?** Yes -- fixed directly in `selftest.py`,
  documented in `scad-modeler/references/setup-notes.md`.

### 2026-08-18 -- selftest.py step 3 hung indefinitely
- **Where:** `scad-modeler/scripts/selftest.py`
- **Symptom:** `openscad --render --summary all --summary-file -` (no `-o`)
  hung for minutes at near-zero CPU, not just ran slowly.
- **Root cause:** NOT backend choice -- adding `--backend=Manifold` made no
  difference, and CSG evaluation itself finished in 13ms per the render log.
  OpenSCAD needs an explicit `-o` export target to take its proper
  non-interactive/batch code path; without one it stalls rather than erroring.
- **Fix:** added a throwaway `-o` output alongside `--summary`, which made the
  same call complete in under 5ms.
- **Already promoted to a rule?** Yes -- fixed in `selftest.py`, documented in
  `setup-notes.md`.

### 2026-08-16 -- assembly.scad silently doubled a part's geometry
- **Where:** `scad-modeler/SKILL.md` §6 (found while dogfooding the skill
  end-to-end on a synthetic assembly)
- **Symptom:** would have duplicated any part positioned away from the
  origin -- once unpositioned via the part file's own trailing render call,
  once positioned via `at()`.
- **Root cause:** `include`-ing a part file into `assembly.scad` also runs
  that file's own unconditional top-level render call (every part file ends
  with one, so it renders standalone). `include` doesn't skip that; `use` does.
- **Fix:** `SKILL.md` §6 now mandates `use`, not `include`, for part files in
  `assembly.scad`.
- **Already promoted to a rule?** Yes -- `SKILL.md` §6 and `setup-notes.md`.

### 2026-08-18 -- gearbox_case.scad EXPECTED_BBOX Z value fails validate_scad.sh's own tolerance
- **Where:** `esp32_rc_modelis/mechanical/rear_axle/parts/gearbox_case.scad` (read-only
  audit of a separate/parallel session's work)
- **Symptom:** running `validate_scad.sh --all` against the current files:
  `FAIL: gearbox_case.stl bbox mismatch ... Z: expected 70.900 mm, got
  70.927 mm (diff 0.0273 mm > tol 0.0108 mm)`. X (51.5mm) and Y (67.2mm)
  pass; only Z fails.
- **Root cause:** the header comment's `// EXPECTED_BBOX: [51.5, 67.2,
  70.9]` rounds the real rendered Z extent (70.927mm) to one decimal
  place, but `check_dimensions.py`'s tolerance is derived from the
  model's own facet resolution (~0.011mm here), far tighter than the
  0.027mm rounding gap -- exactly the "declared bbox is a rounded
  nominal" case SKILL.md §7 says needs `--abs-tol`/`--rel-tol`, which
  was never added.
- **Fix:** Not fixed -- read-only audit, scoped by user request
  (2026-08-19); flagged for the project owner to address (either write
  the full-precision 70.927 into the comment, or add an explicit
  tolerance override).
- **Already promoted to a rule?** not yet.

### 2026-08-18 -- check_collisions.py currently fails on gearbox_case_bottom/top; no joints.json declares the intended split-line touch
- **Where:** `esp32_rc_modelis/mechanical/rear_axle/` (positioned STLs
  exported per SKILL.md §6/§7, checked with `check_collisions.py
  --min-clearance 0.3`)
- **Symptom:** `check_collisions.py` returns exit 3, `FAIL: UNINTENDED
  INTERFERENCE: gearbox_case_bottom.stl <-> gearbox_case_top.stl` -- yet
  `README.md`/`calculations.md` both describe this exact pair as
  confirmed benign ("0.0mm³ ... patvirtinta esąs tikslus 0.0mm³ ...
  teisingas clamshell elgesys" / "Kolizijų patikra ... švari, išskyrus
  tikėtiną gearbox_case_bottom↔top prisilietimą"). Re-verified
  independently with a manual trimesh boolean intersection: the overlap
  is a genuine zero-volume degenerate surface at the Y=0 split plane
  (`is_volume: False`), confirming it IS benign -- but the project has
  no `joints.json` anywhere to declare it, so the check fails exactly as
  SKILL.md §7 warns an undeclared "intentional contact" will.
- **Root cause:** the clamshell split-line touch was identified and
  reasoned about correctly during the original session, but was never
  formalized as an `--expected-contacts` declaration
  (`templates/joints.json`), so the validation pipeline as it stands
  cannot actually be run to a clean pass -- the documented "švari"
  claim isn't reproducible from the command as given in README.md.
- **Fix:** Not fixed -- read-only audit, scoped by user request
  (2026-08-19); flagged for the project owner to address (add a
  `joints.json` declaring `gearbox_case_bottom`/`gearbox_case_top` as a
  `touching` contact with `expected_interference_mm: [0.0, 0.0]`).
- **Already promoted to a rule?** not yet.

### 2026-08-18 -- calculations.md's CD1/CD2 values (33.6mm/26.5mm) don't match what params.scad's own gear_dist() calls compute (33.83mm/26.62mm)
- **Where:** `esp32_rc_modelis/mechanical/rear_axle/calculations.md` +
  `params.scad`
- **Symptom:** every mention of the two center distances in
  `calculations.md`, `README.md`, and inline `params.scad`/
  `gearbox_case.scad` comments says CD1=33.6mm, CD2=26.5mm (the naive
  `(T1+T2)×mod/2` hand formula). Directly querying the live top-level
  variables from `params.scad` (`echo(CD1, CD2)`) gives 33.8326mm and
  26.6206mm -- a 0.23mm and 0.12mm drift.
- **Root cause:** `params.scad` correctly calls BOSL2's `gear_dist()`
  for both stages (matching SKILL.md §5's own guidance), but P1 (12T)
  and P2 (15T) are both below the ~17-tooth undercut threshold at 20°
  pressure angle, so `gear_dist()` silently applies its automatic
  profile-shift correction -- exactly the divergence SKILL.md §5
  already warns about ("stops being exact once BOSL2's
  profile_shift='auto' kicks in for small tooth counts").
  `calculations.md`'s calculation table was never re-verified against
  the actual `gear_dist()` output, so it still states the
  pre-profile-shift hand values as the final "OK" numbers.
- **Fix:** Not fixed -- read-only audit, scoped by user request
  (2026-08-19); flagged for the project owner to address (currently
  benign -- both real values are larger than documented, i.e. more
  clearance, not less -- but should be corrected in `calculations.md`
  so a future reader doesn't measure against the wrong nominal).
- **Already promoted to a rule?** not yet -- SKILL.md §5 already
  contains the general caution; this shows it wasn't actually applied
  to double-check this project's own calculation table after the fact.

### 2026-08-18 -- jackshaft_bearing_wall_at_diff assert in params.scad omits clearances the real geometry subtracts, understating the true minimum wall
- **Where:** `esp32_rc_modelis/mechanical/rear_axle/params.scad`
  (assert) vs. `parts/gearbox_case.scad` (`diff_cavity()`,
  `jackshaft_bearing_pockets()`)
- **Symptom:** `params.scad` computes
  `jackshaft_bearing_wall_at_diff = CD2 - diff_ring_outer_r -
  jackshaft_bearing_od/2` = 1.62mm (using the corrected CD2 from the
  previous entry) and asserts it's `> 1.0`, i.e. reports a "safe"
  ~1.6mm margin. But `gearbox_case.scad`'s own header comment
  independently flags the real wall as "~1.2mm ... ties FDM
  spausdinimo riba" (at the FDM printing limit) -- confirmed by hand:
  the actual cavities are cut with `gear_spin_clearance` (0.4mm, added
  to `diff_ring_outer_r` in `diff_cavity()`) and `bearing_press_fit`
  (0.05mm, added to the bearing pocket diameter in
  `jackshaft_bearing_pockets()`), neither of which the assert's formula
  includes. Recomputing with both terms gives 1.196mm, matching the
  code comment.
- **Root cause:** the assert was written against nominal pitch/OD
  dimensions only, not the actual clearance-inflated cavity radii the
  geometry modules use -- so it protects against a *gross* tooth-count
  regression but would not catch a smaller regression that pushes the
  real (clearance-inflated) wall toward zero while the assert's own
  optimistic formula still reports comfortable margin.
- **Fix:** Not fixed -- read-only audit, scoped by user request
  (2026-08-19); flagged for the project owner to address (add
  `gear_spin_clearance` and `bearing_press_fit` to the assert's formula
  so its "safe" verdict matches the geometry it's meant to guard).
- **Already promoted to a rule?** not yet.

### 2026-08-18 -- axle_d=6mm is incompatible with the MR105 bearings (fixed 5mm ID) at the wheel_hub end of the same half-shaft
- **Where:** `esp32_rc_modelis/mechanical/rear_axle/params.scad`
  (`axle_d`), `parts/wheel_hub.scad`, `BOM.md` #1/#7
- **Symptom:** `params.scad` sets `axle_d = 6` ("atnaujinta iš 5mm --
  nuotraukoje diff stebulė ~6mm; PATIKRINTI") and this single value is
  used uniformly as the half-shaft diameter in both `axle_tube.scad`'s
  bore and `wheel_hub.scad`'s central bore. But `wheel_hub.scad` also
  seats two MR105 bearings (BOM #1: fixed 10×5×4mm, ID=5mm) at its two
  ends, and the same half-shaft must pass through both. A uniform 6mm
  shaft cannot pass through a 5mm-ID bearing.
- **Root cause:** the 6mm figure comes from a photo measurement of the
  *diff-side* output stub diameter; nothing in `calculations.md`'s
  PATIKRINTI note ("gali reikėti keisti axle_d iš 5 į 6mm") considers
  that the same `axle_d` variable is also used for the wheel-hub/bearing
  end, where the bearing spec (MR105, ID fixed at 5mm) requires 5mm.
  The two ends of the half-shaft need different diameters (a stepped
  shaft) or a different bearing choice at the wheel end -- neither is
  modeled or called out anywhere in the CAD or BOM.
- **Fix:** Not fixed -- read-only audit, scoped by user request
  (2026-08-19); flagged for the project owner to address (decide:
  stepped half-shaft 6mm at diff / 5mm through the wheel_hub bearings,
  or a different bearing/stub diameter, and update
  `params.scad`/`BOM.md` accordingly).
- **Already promoted to a rule?** not yet.

### 2026-08-18 -- tolerances.md overstated milling's precision
- **Where:** `openscad-cad/references/tolerances.md`
- **Symptom:** none from an automated check -- found by cross-checking the
  file's claim against the actual cited paper's PDF (user-supplied).
- **Root cause:** the file claimed "milling and turning occupy IT7-IT10" --
  the paper's real Table 4 has milling at IT9-11; only turning reaches
  IT7-10. An earlier transcription pass conflated the two.
- **Fix:** corrected the claim in `tolerances.md` to cite the two ranges
  separately.
- **Already promoted to a rule?** Yes -- fixed directly in the reference file
  (the fix *is* the rule here, not a separate pattern to extract).
