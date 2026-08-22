# Regression suite for this skill's own checker scripts

Added 2026-08-22. Until now, every new `check_*.py` was tested once
against a synthetic fixture built in a scratch directory, then the
fixture was deleted after the commit — real, but throwaway, verification.
An independent deep-research pass (asked specifically to find real
precedent for improving this skill, not to restate its own design)
flagged this directly: a "labeled regression corpus" and "deterministic
regression fixtures ... run automatically ... to instantly catch any
change that unexpectedly alters validation behavior" were named as
concrete, actionable gaps. This directory is that.

**This tests the SKILL's own scripts, not a user's project.** Not wired
into `validate_scad.sh` (which validates a *project*). Run it after
changing anything in `../scripts/`:

```bash
bash tests/run_all.sh
```

## Adding a fixture

1. Create `fixtures/<descriptive_name>/`.
2. Put whatever `.scad` (and `params.scad`, `parts/`, etc.) the checker
   under test needs in it. Prefer a **direct reproduction of a real
   `INCIDENTS.md` incident** where one exists — that's both a real test
   and a permanent record that the specific bug can't silently come back.
3. Write `run_test.sh`: a self-contained script that renders whatever it
   needs (via `$OPENSCAD`, defaulting to `openscad`), runs the checker
   under test via `$SCAD_MODELER_SCRIPTS/check_x.py` (exported by
   `run_all.sh`), compares the actual exit code (and, where useful, a
   specific string in the output — see `collisions_candidate_touch/` for
   an example) against what the fixture is supposed to prove, and exits
   0 if it matches, 1 with a clear message if it doesn't. Clean up any
   rendered `.stl` it created.
4. `chmod +x run_test.sh`, then `bash run_all.sh` to confirm it's picked
   up and passes.

Cover BOTH directions where practical — a fixture proving the checker
fails on the real bad case, and a second one proving it passes on the
fixed/good case (see the `_fail`/`_pass` pairs below). A suite that only
ever exercises the failing path can't tell "the check works" from "the
check always fails."

## Current fixtures

| Fixture | Proves |
|---|---|
| `margin_provenance_fail` / `_pass` | `check_margin_provenance.py` catches the real `jackshaft_bearing_wall_at_diff` incident shape (INCIDENTS.md, 2026-08-18) and passes once fixed |
| `param_context_fail` / `_pass` | `check_param_context.py` catches the real `axle_d` incident shape (INCIDENTS.md, 2026-08-18) and passes once fixed |
| `printability_overhang_fail` | `check_printability.py` flags a genuinely steep (77°) overhang |
| `printability_wall_fail` | `check_printability.py` flags a genuinely thin (0.3mm) wall |
| `collisions_candidate_touch` | `check_collisions.py` classifies an undeclared, exactly-touching pair as CANDIDATE INTENTIONAL TOUCH (Phase-2 Pattern 2), with a stub printed |
| `collisions_near_miss` | `check_collisions.py` surfaces a 0.15mm gap as a non-fatal NEAR MISS note, not a failure |

Not yet covered here (older checks, predating this suite — add a fixture
when touching one of these next): `check_connectivity.py`,
`check_dimensions.py`, `check_features.py`, `check_bore_reachability.py`,
`check_subfeature_overlap.py`, `check_dependencies.py`'s edit
classification, `motion_sweep.py`, `check_assumptions.py`,
`check_service_envelope.py`, `check_plan.py`, `check_intake.py`,
`check_rules.py`, `expected_bounds`/`forbidden_regions` in
`check_collisions.py`. Deliberately not backfilled all at once — add one
the next time you touch that script, per the same discipline this skill
already applies to `INCIDENTS.md` itself (don't build speculatively for
its own sake; let real need drive it).
