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

## Exit codes are NOT uniform across checkers — read this before writing a fixture

A trap worth stating plainly: **half the checkers use exit 1 for a failure, half
use exit 3.** This was found the hard way — two fixtures written in one session
both assumed 3 and both failed, for no reason other than the assumption.

| Exit code | Checkers |
|---|---|
| **1** on failure | `check_assumptions`, `check_connectivity`, `check_dimensions`, `check_features`, `check_plan`, `check_service_envelope` |
| **3** on failure | `check_attachment`, `check_bore_reachability`, `check_collisions`, `check_intake`, `check_rules`, `check_subfeature_overlap` |
| 4 on usage/runtime error | most checkers |
| 2 = degraded | `check_collisions` only — **treat as not checked, not as pass** |

`motion_sweep.py`, `check_margin_provenance.py`, `check_param_context.py`,
`check_printability.py` and `check_dependencies.py` compute their own codes —
read the docstring of the one you are testing rather than guessing.

**Do not "fix" this by changing the codes.** `validate_scad.sh` and any
user-side script branch on these values; a silent renumbering would break them.
The correct move when adding a checker is to document its code and add a fixture
that pins it.

When writing a fixture, do not assume — derive the expected code by running the
checker once and reading what it actually returns. That is what caught both
mistakes above.

## Adding a fixture

1. Create `fixtures/<descriptive_name>/`.
2. Put whatever `.scad` (and `params.scad`, `parts/`, etc.) the checker
   under test needs in it. Prefer a **direct reproduction of a real
   `INCIDENTS.json` incident** where one exists — that's both a real test
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
| `margin_provenance_fail` / `_pass` | `check_margin_provenance.py` catches the real `jackshaft_bearing_wall_at_diff` incident shape (INCIDENTS.json, 2026-08-18) and passes once fixed |
| `param_context_fail` / `_pass` | `check_param_context.py` catches the real `axle_d` incident shape (INCIDENTS.json, 2026-08-18) and passes once fixed |
| `scad_lint_computed_default_fail` / `scad_lint_rounded_standard_fail` / `scad_lint_clean_pass` | `check_scad_lint.py` (P2): beam `len = 211` computed by one call and omitted by another (INCIDENTS.json 2026-09-04), 1U 44.5 vs 44.45 (2026-08-23), and no false fire on comments, strings, exact values or fully-passed defaults |
| `topology_sealed_hole_fail` / `topology_cases` | `check_topology.py` (P12): a bore sealed by a 0.4 mm skin fails; matching count passes; no declaration SKIPs; an open mesh fails |
| `validate_lint_topology_wired` | both checks report `CHECK_RESULT` lines and set the verdict in single-file and `--all` mode |
| `libs_lock` | `env_gate.py` (P14): `--write-lock` pins BOSL2 by version and other libraries by tree hash; a different installed version or tree is env=FAIL; no lock, no check |
| `validate_libs_state_and_warning` | the state file records library versions; a preflight stopped by a WARNING is not reported as a failed assert() |
| `printability_overhang_fail` | `check_printability.py` flags a genuinely steep (77°) overhang |
| `printability_wall_fail` | `check_printability.py` flags a genuinely thin (0.3mm) wall |
| `assembly_sequence` | `check_assembly_sequence.py` (P35): open box + block + lid PASS with an order; a pin sealed in a closed housing FAILs "trapped" (exit 3); the same pin in `assembly.json` `inserted_before` PASSes and is named; no positioned STLs SKIP; two plates sharing a face slide apart (contact is not collision) |
| `fits` | `check_fits.py` (P32/P36): clearance 0.2 PASS; hole 0.3 mm too small FAIL; ISO H7/g6 in class PASS, hole outside H7 and peg outside g6 FAIL; undeclared 0.2 mm gap over 100 mm2 WARNs (exit 0), `--strict` FAILs, a declared pair and a 2 mm gap do not; no fits SKIP; unknown part name exit 4; `mate()` from patterns.scad renders to the declared clearance |
| `printability_bed_volume` | P38: part bbox vs `--bed` (default 256³); too big FAILs and says when a 90° turn fits |
| `printability_overhang_region` | P38: overhang reported per region (area, centre); a true-45° cone, a 45.5° wedge (inside the 1° facet tolerance) and a sub-1 mm² nub pass |
| `printability_bridge` | P38: flat ceiling carried both sides FAILs above 5 mm, passes at 4 mm; a one-sided shelf stays an UNSUPPORTED OVERHANG |
| `printability_bed_warp` | P38: sharp corners on the plate face print `WARN: BED CONTACT` (exit stays 0); a rounded footprint prints none |
| `strength_formulas` | `check_strength.py` wave 2 (AC-E1..E4): screw thread strip-out, Lamé press-fit hoop stress (X-Y vs Z by axis) and beam transverse shear each agree with the hand number in the fixture header, FAIL over the limit, and a derived (0.6 x tensile) shear limit only WARNs |
| `printability_knife_edge` | P38 (AC-I1): a 30° convex wedge edge prints `WARN: KNIFE EDGE` (exit stays 0); a cube with a sharp concave V groove prints none |
| `printability_stair_step` | P38 (AC-I2): a 10° up-facing ramp prints `INFO: STAIR STEPPING` with step width layer/tan(angle) (`--layer`); flat top + 45° chamfer prints none |
| `printability_support_volume` | P38 (AC-I3): `INFO: SUPPORT VOLUME` matches hand-computed mushroom columns (6283 mm³ to the plate, 5027 mm³ down to a pad below); a cube prints none |
| `collisions_candidate_touch` | `check_collisions.py` classifies an undeclared, exactly-touching pair as CANDIDATE INTENTIONAL TOUCH (Phase-2 Pattern 2), with a stub printed |
| `collisions_near_miss` | `check_collisions.py` surfaces a 0.15mm gap as a non-fatal NEAR MISS note, not a failure |
| `motion_sign_fail` | `motion_sweep.py` refuses to sweep a `gear_mesh` pair whose drivers share the same sign |
| `motion_sign_pass` | a correctly opposite-signed `gear_mesh` pair is not false-flagged |
| `motion_sign_internal_optout` | `"internal_gear_mesh"` opts a genuinely same-direction pair out of the sign check |
| `p32_gear_kinds` | P32 AC-G1/G2/G3: `gear_mesh` `"kind":"bevel"` (axes 0.3 mm apart, 88 vs 90 deg FAIL) and `"worm"` (+0.2 mm off `worm_dist()`, 88 deg FAIL); correct pairs OK; no `kind` stays NOT CHECKED |
| `margin_wrong_variable_fail` / `_pass` | `check_margin_provenance.py`'s wrong-variable-family mode catches the real `nas_deck_v3` incident shape (INCIDENTS.json, 2026-09-02) and passes once fixed |
| `fasteners_engage_pass` / `fasteners_engage_short_warn` / `fasteners_engage_short_alu_fail` | AC-H1: 16 mm M4 in plastic passes; 4.5 mm WARNs (◇ 1.5 d, exit 0); 4.5 mm in `"into_material": "aluminium"` FAILs (2 d). Builder: `fasteners_engage/make.py` |
| `fasteners_insert_short_fail` / `fasteners_insert_pass` | AC-H1: a screw reaching less than the heat-set insert's `L` (inserts.json) FAILs; a long one passes |
| `fasteners_bottom_out_fail` | AC-H1: blind pilot shallower than the screw: "screw bottoms out" |
| `fasteners_mount_two_plane_fail` | AC-H2: part on two planes covers a host hole under the smaller one; `covered_ok` clears it |
| `fail_hints` | P39: every FAIL block of a `check_*.py` / `motion_sweep.py` contains `Hint:` (what to change). Runs the FAIL-producing fixtures (the list in its `run_test.sh` plus every `*_fail*`) with the checkers behind `tools/hint_audit.py` shims, requires > 50 blocks seen and none hint-less; a new fixture that prints FAIL goes into that list. ~5 min; under the semantic-mutant runner only `fits` runs |

Not yet covered here (older checks, predating this suite — add a fixture
when touching one of these next): `check_connectivity.py`,
`check_dimensions.py`, `check_features.py`, `check_bore_reachability.py`,
`check_subfeature_overlap.py`, `check_dependencies.py`'s edit
classification, `check_assumptions.py`,
`check_service_envelope.py`, `check_plan.py`, `check_intake.py`,
`check_rules.py`, `expected_bounds`/`forbidden_regions` in
`check_collisions.py`. Deliberately not backfilled all at once — add one
the next time you touch that script, per the same discipline this skill
already applies to `INCIDENTS.json` itself (don't build speculatively for
its own sake; let real need drive it).
