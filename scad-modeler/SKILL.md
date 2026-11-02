---
name: scad-modeler
description: 'Use for complex, multi-part parametric OpenSCAD mechanical assemblies — things with gears, bearings, reductions, multiple interacting printed parts, or where getting a dimension wrong means two parts collide or don''t mesh. Triggers on "gear ratio", "reduction", "bearing", "shaft", "assembly", "BOM", "center distance", "mechanical design", "RC car", "gearbox", "multi-part", "design a mechanism", "which architecture", "gearbox layout", or a brief vague enough that more than one mechanism would satisfy it — or requests to design several parts that must fit together and be validated. For a single simple part, use openscad-cad instead. Adds: gated planning before numbers, calculations before geometry, centralized positions, and dimensional/collision/motion validation. ALWAYS load openscad-cad alongside. ALWAYS read ../INCIDENTS.md before writing geometry.'
---

# SCAD Modeler — Multi-Part Mechanical Assemblies

For assemblies where parts must fit together (gear meshes, bearing fits, shaft
alignment). A single self-contained part: use `openscad-cad`. Which skill or file
holds a fact: `../references/retrieval.md`.

This file is the rules and commands. The reasons, incident history and longer
examples are in `references/workflow_details.md` under the same section numbers;
open a section there when a rule here is unclear or a gate fails.

## You are not done until these two commands have run

```
S=~/.claude/skills/scad-modeler/scripts       # the skill's scripts, not the project's
bash $S/validate_scad.sh --all                # from the project root
$(bash $S/resolve_python.sh --print) $S/check_rules.py --project-dir .
```

Exit 0 = every executed check passed (the last line counts the not-applicable ones);
1 = a check failed; 2 = `NOT VERIFIED`, a check could not determine its answer, which
is never a pass; 5 = environment.

`CHECK_RESULT env=FAIL` (exit 5): a Python module, OpenSCAD, an included library, or
the library version in `libs.lock` is wrong, so nothing reported is about the
geometry. Stop, show the user the `ENV_FAIL:` lines and their fix (usually
`bash scripts/setup_env.sh`), report no PASS/FAIL. Once a project validates, pin its
libraries: `python3 scripts/env_gate.py --project-dir . --write-lock`.

Paste BOTH outputs into the final report. A part is finished when the pipeline has
run and you have quoted it, not when you believe it is right (an agent that ran one
checker by hand shipped 3 disconnected bodies; references/workflow_details.md, first section).

## 0. Before anything else

1. Read the project's own facts first (`CLAUDE.md`, `AGENTS.md`, README,
   `design_decisions.md`). Ask once for a missing fact; never guess a bearing bore or
   shaft diameter.
2. Read `../INCIDENTS.md` — **its `## Index` only**, then the entries matching what you
   build (`grep -n <term>` works). Not after something breaks.
3. New designs: write `design_manifest.json` (Stage 0; `validate_scad.sh` runs
   `check_intake.py` on it), classify each component **printed vs purchased**
   (bearings, shafts, fasteners are never printed), and look at 2–3 similar past
   projects. How: `references/intake_and_analysis.md`.

## 0.5. Planning (3+ parts, or an uncertain architecture)

Settle the concept before any formula. Copy `templates/plan.md` to `plan.md`: at
least 2 architecture options (or `<!-- PLAN_EXEMPT: reason -->`), a `Decision` row
with `Status: Confirmed`, and every part that `layout.scad` names. `plan=FAIL` for 3+
parts without it. Method: `references/planning.md`.

## 0.6. Physical assembly narrative (per feature touching a bearing, shaft, fastener, purchased part, or sharing a `union()`)

Before writing that feature's geometry, answer in a few sentences (in
`calculations.md` or the plan): **insertion path** (the whole path from outside to
the seat, not just the seat), **shared-part neighbours** (real envelopes of every
sub-feature in the same `union()`), **retention** (what stops motion in the
directions it must not move), **purchased-part fit** (the install step the real
object needs). For a load-bearing fit with no calibration profile, propose a
`calibration_coupon()` (R-14) yourself.

Every answer becomes a declaration; prose is checked by nothing:

| Answer | Declaration | Checked by |
|---|---|---|
| Insertion path | `bores.json` — `bore_candidates.py --scad parts/X.scad` writes it from the CSG tree; delete what is not a bore | `check_bore_reachability.py` |
| Shared-part neighbours | `fusions.json`; `// EXPECTED_BODIES: N` | `check_subfeature_overlap.py`, `check_connectivity.py` |
| Retention | `attachments.json` (`"to": "<part>"`). Every part needs a joint: contact, attachment, or `// NO_JOINT: <reason>` | `check_attachment.py`, `check_joint_graph.py` |
| Purchased-part fit | `joints.json` contact with `expected_interference_mm` and `derivation` | `check_collisions.py`, `motion_sweep.py` |

Templates for all four are in `templates/`. Why this step exists (three "done"
designs nobody could assemble): details §0.6.

## 1. Calculation table (before any geometry)

| Part | Formula | Value | Status |
|------|---------|-------|--------|
| Stage 1 ratio | driven_teeth / driver_teeth | 66/11 = 6.00 | OK |
| Bearing bore | per datasheet | 10mm | PATIKRINTI |

Anything not from a datasheet, spec or prior decision is `PATIKRINTI`; resolve every
one before §2. The table goes into the final report.

## 2. `params.scad` — every dimension, one place

Every dimension used anywhere lives here; a bare number in a part is only for a local
cosmetic detail. `assert()` every relationship the design depends on (ratio near
target, wall still positive after clearance, bore bigger than shaft):

```openscad
gear_module = 1.0;            // NOT `module` -- reserved word
pinion_teeth = 11; spur_teeth = 66;
ratio_1 = spur_teeth / pinion_teeth;
assert(ratio_1 > 5.5 && ratio_1 < 6.5, "Stage 1 ratio drifted from target ~6:1");
```

- A margin assert includes **every clearance term the geometry applies**
  (`_clearance`/`_fit`/`_bias`/`_offset`/`_backlash`), and checks the variable actually
  cut, not a same-family sibling. `check_margin_provenance.py` (R-15) flags both; a
  deliberate exception is `// MARGIN_EXCLUDES_OK: <var>`.
- One value used for hardware fit in 2+ places: `use_param("axle_d", "<context>",
  "<constraint>")` in each part plus an `assert()` there (`check_param_context.py`,
  R-16). Examples: details §2.

## 3. `layout.scad` — where each part sits

State origin and axes in a comment, then a `LAYOUT` table and `at(name)` module that
translates/rotates a part into place. Copy `templates/layout.scad`.

## 4. Part files — local coordinates

**Before your first part, open `references/examples.md` and `examples/gear_reduction/`**
(102 lines, validates clean); copying beats reconstructing. One file per part, around
its own sensible origin, with origin and print orientation in a top comment; never
transform the whole part inside its file (`at()` does that). For features within a
part prefer BOSL2 attachments (always the `{ }` block form when attaching more than
one). `python3 scripts/doctor.py` confirms BOSL2 is really installed.

**Every number that came from outside becomes a declaration**, not just code:

```openscad
// EXPECTED_BBOX: [33.595, 33.595, 46]        // required (or // NO_BBOX: <why>)
// EXPECTED_THROUGH_HOLES: 4                   // required (or // NO_THROUGH_HOLES_CHECK: <why>)
// EXPECTED_HOLE: [0, 0, 5.5, "Z", 5.2]       // x, y, z, axis, across-flats Ø, per specified bore
// EXPECTED_BODIES: 2                          // only if genuinely multi-shell
// SENSITIVE_TO: wall                          // re-render with wall x1.5; unchanged = hard-coded
// PREVIEW_FILE: <why>                         // a file showing variants side by side, not one part
```

`declarations=FAIL` when the first two are missing or their reason is empty. Never use
`PREVIEW_FILE` to silence a file that renders two real parts.

## 4.5. Purchased hardware — position its body, not just its cavity

Model bearings, motors, screws as positioned NopSCADlib vitamins (`ball_bearing()`,
`screw()`, `NEMA()`) so the checks see them; BOM splits Printed vs Purchased. How:
`references/hardware.md`.

## 5. Gears: BOSL2, never hand-written involute math

```openscad
include <BOSL2/std.scad>
include <BOSL2/gears.scad>
spur_gear(mod=gear_module, teeth=pinion_teeth, thickness=15,
          shaft_diam=motor_shaft_d, pressure_angle=20, backlash=0.15);
```

- Center distance with profile shift: `gear_dist(mod=, teeth1=, teeth2=)`.
- `layout.scad` needs **both BOSL2 includes too**, or positioned gears fail through
  `at()` while the part renders fine alone.
- OpenSCAD trig takes degrees. Helical/herringbone/bevel: PolyGear, render-tested.
  Why and what failed: details §5.

## 6. `assembly.scad` — MODE switch

**Copy `templates/assembly.scad`.** Parts come in with `use`, never `include` (include
runs the part's top-level call again: a stray copy at the origin). The two guarded
lines are mandatory; a plain `MODE = 1;` defeats `-D` and every positioned part
becomes the whole assembly:

```openscad
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
module part_by_name(name) {
    if (name == "rear_jackshaft") rear_jackshaft();
    else assert(false, str("Unknown part in layout: ", name));
}
if (MODE == "assembly") { at("rear_jackshaft") rear_jackshaft(); }
else if (MODE == "part") { at(PART) part_by_name(PART); }
```

End assembly mode with a BOM `echo()`. NopSCADlib projects can use its BOM tooling
instead (details §6).

Anything that moves (hinge, gear, slider) is declared in `joints.json`; the validator
sweeps it (`mechanics`). Every motion entry needs a `drivers` list:

```json
{"contacts": [{"pair": ["box", "lid"], "joint_type": "hinge", "expected_interference_mm": [0, 0.05]}],
 "motion": [{"id": "lid_open", "range_deg": [0, 110], "step_deg": 2.0,
   "drivers": [{"part": "lid", "type": "revolute", "axis": [-1, 0, 0], "origin": [0, 60, 20], "ratio": 1.0}]}]}
```

`axis`/`origin` are assembly coordinates and +angle turns right-handed about `axis`: a lid
hinged on its back edge (y = 60) opens upward with axis −X; +X swings it into the box.
Meshing external gears need opposite-sign `ratio` (1.0 and −0.5); `prismatic` takes mm per
degree. Undriven parts are static; contact pairs may overlap only within their range.
`min_clearance_mm` (default 0) applies to every pair, the hinge contact too — set it only
when no driven part may ever touch anything.

## 7. Validation cycle (every part and the assembly)

`bash scripts/validate_scad.sh --all` renders every `parts/*.scad` and the assembly
and prints one `CHECK_RESULT <gate>=PASS|FAIL|SKIP|INCONCLUSIVE|ADVISORY` line per gate
and a `COVERAGE:` line. Read those lines, not just the exit code. What each gate
catches, tolerances, field semantics: `references/validation.md`.

- **FAIL** — fix the model at the source. Never loosen an `assert()`, tolerance,
  threshold or declaration to make it pass.
- **SKIP / not-applicable** — the declaration or file it needs is absent; add it if
  it should apply. A SKIP is not a pass.
- **INCONCLUSIVE** — the check ran and could not answer. Never read it as success.
- **After any geometry fix, re-run the whole cycle**, not only the check you were
  fixing; one fix silently breaking another is how the connectivity bug was born.

Then render a preview and look at it:
`openscad --backend=Manifold --render -o build/preview.png --imgsize=1200,900 --autocenter --viewall assembly.scad`

**Approved numbers (P5).** Multi-part project: put the size and through-hole count the
user agreed to in `acceptance.json` (`{"parts": {"plate": {"bbox": [40, 20, 5],
"through_holes": 2}}}`), show it, and after their yes run
`$S/acceptance.py approve --quote "<their exact words>"`; `$S/acceptance.py emit`
prints the declaration lines. A failing part is fixed in the geometry, never in its
comment. You cannot approve your own numbers.

Not gated: `check_printability.py` (advisory, run by hand with `--stl`) and load /
strength (needs material data).

## 8. Final report

Run `check_rules.py` (the second command above) and cite its **full** output,
including your done / skipped / not-applicable verdict for every MANUAL rule. Then:
files created or changed; BOM split Printed / Purchased; critical dimensions from the
calculation table; open `PATIKRINTI` items; print orientation per part; the
confidence tier reached (`../openscad-cad/references/confidence-tiers.md`).

A real bug found and fixed this session (wrong test, false pass, hang, wrong claim):
append it to `../INCIDENTS.md` in its entry format before finishing.

## Generator (parametric parts)

If the request fits one of the 8 shapes (plate, plate_with_holes, bracket_l, box, lid,
boss, hole_pattern, snap_hook) or the composite `box_with_lid` (2-part enclosure with
optional corner screws), do not hand-write the `.scad`. Write `requirements.json` and
run:

    python3 gen/emit_part.py requirements.json -o parts/<part>.scad

For `kind: "box_with_lid"`, pass `-o assembly.scad` — it emits `parts/box.scad`,
`parts/lid.scad`, `assembly.scad` and `joints.json`. The generator writes `// EXPECTED_*`
declarations from the same parameters. Schema: `gen/schema.json`. If `kind` does not fit,
use `custom` (hand-written, declarations required).

Working example of each kind: `tests/genkit/fixtures/`.

## Reference files

| Need | File |
|---|---|
| Reasons, incident history, longer examples for each section | `references/workflow_details.md` |
| What each gate catches, declaration fields, exit codes | `references/validation.md` |
| Which check applies now | `references/validation_decision_tree.md` |
| Working example to copy | `references/examples.md`, `examples/gear_reduction/` |
| Stage 0 spec schema, printed vs purchased | `references/intake_and_analysis.md` |
| Planning method | `references/planning.md` |
| Motion, fit clearances | `references/mechanics_and_motion_planning.md` |
| What to re-check after an edit (`check_dependencies.py --change VAR`) | `references/change_propagation.md` |
| Vitamins and BOM | `references/hardware.md` |
| Why rules drift, rules manifest | `references/rules_enforcement.md`, `rules_manifest.yaml` |
| Templates | `templates/` (plan, part, layout, assembly, joints, bores, attachments, fusions, service_envelope) |
| Every script and what it needs | `references/workflow_details.md` § Reference files |
