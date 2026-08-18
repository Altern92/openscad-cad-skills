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
