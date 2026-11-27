<!-- RAG-passport: file=NEXT.md | skill=all | applies_to=[future-work, roadmap, known-gaps] | version=2026-11-27 | source=P29 + competitor comparison 2026-11-27 -->
# NEXT — work queue (as of 2026-11-27)

This file is the only list of known, unfinished work. The full history (P1–P29, the 2026-09
analysis, cost measurements) is archived in
[`docs/archive/NEXT_2026-11-27.md`](docs/archive/NEXT_2026-11-27.md); item IDs cited in code,
specs and `INCIDENTS.json` refer to that file.

**State:** 120 tests (119 fixtures + GenKit) green in dev and in the installed copy, 26
`check_*.py` checkers + motion sweep, a 26-rule gate, ~145 incident entries. Last done: P29
(gear axes and BOSL2 `gear_dist()` centre distance, commit a672032).

**Workflow for every code item:** `feature-loop` — Acceptance Criteria → maintainer approval →
TDD → fresh-context review → `scad-modeler/tests/run_all.sh` green in dev and via
`~/.claude/skills` → commit/push only with the maintainer's explicit yes → deploy with
`scripts/deploy_to_canon.sh`. Every new gate needs a negative case (a mutant that must FAIL).
When an item is done, mark it `[x]` with the commit hash.

---

## 1. Roadmap (positioning, decided 2026-11-27)

The niche is **"an AI agent that models multi-part assemblies and proves they work"**. Paid tools
(Zoo Text-to-CAD, Backflip, Autodesk Fusion AI) win on surface quality, STEP output and GUI; as
far as known (not verified against primary sources), none of them automatically checks
collisions, motion, gear meshing or part retention. Strengthen the niche; do not compete on
pretty surfaces.

Priority order: P30 → P31 → P32. P33 only on user demand. P34 is deliberately not planned.

- [ ] **P30 Visible demo (highest impact, least code).** A short GIF or video at the top of
  `README.md`: prompt → model → checker FAIL → fix → OK (the gear-jam case from P29 is ready
  material). Optional later: a web page or hosted demo so people can see results without
  Claude Code. Goal: a visitor understands the value in 10 seconds (supports donations).
- [ ] **P31 Wider strength checks (formulas, not FEA).** Extend `check_strength.py` beyond
  heat-set insert holes and simple beams: bending and shear of brackets, thread strip-out,
  wall thickness vs load, press-fit hoop stress. Each formula with a cited source and an
  analytic reference case. Engineers miss this most; it is cheap.
- [ ] **P32 More assembly checks (the unique advantage).**
  - Worm and bevel gears (today a `gear_mesh` on non-parallel axes says NOT CHECKED; RC
    `steering_reduction_gearbox` declares worm/bevel pairs as `gear_mesh`).
  - Bearing and shaft tolerances (fit classes, seat depth).
  - Spring and screw lengths (thread engagement, bottoming out).
  - **One interface, two parts ("stamping", idea from the Constructive library,
    codeberg.org/solidboredom/constructive; GPL-2.0 OR CERN-OHL-W, so reimplement the idea, never
    copy code).** A single interface module adds the peg/shaft to one part and cuts the hole
    with clearance from the mating part, so the two cannot drift apart. Work: (a) a `mate()`
    pattern in `openscad-cad/references/patterns.scad` that both parts `include`, with a
    `removing` flag for cutter-only shape (screw-head clearance, insertion path); (b) the
    clearance comes from one approved place (`tolerances.md` / `limits.lock`), not a literal in
    each part; (c) a check that, for each `joints.json` pair, hole Ø = peg Ø + declared
    clearance (FAIL otherwise; mutant: hole 0.3 mm too small). Targets the class-B incidents
    (holes that do not match their pegs).
- [ ] **P33 STEP export (later, only if users ask).** Would need a second CAD kernel (CadQuery /
  build123d) beside OpenSCAD: large job and long-term maintenance. Today output is STL/DXF.
- **P34 Not planned:** organic/freeform surfaces at commercial quality and full FEA. Funded
  commercial tools own this; OpenSCAD (CSG + meshes) is the wrong base for it.

## 2. Open items carried over from the archive

- [ ] **Example `limits.lock` (R-26).** `scad-modeler/examples/gear_reduction` fails
  `check_rules.py` R-26 until the maintainer approves the limits with their own quote
  (`check_limits.py approve --quote`). Do not bypass.
- [ ] **P24 rest (kinematics/strength).** `front_axle_v4` joint `type`/`dof`/`angle` (likely
  FAIL: upper ball 22.8°); 3 g landing `loads.json` on the arms.
  Spec: `docs/superpowers/specs/2026-11-18-p24-kinematics-strength-ac.md`.
- [ ] **P28 candidates.**
  - `check_behavior.py` HOLDS accepts a body made of several separate shells as one (proven:
    4 balls, top one pulled 5 mm away, still PASS). Fix: FAIL when a joint body mesh has >1
    component without a declared `multi_shell`; negative test with 2 balls, one far away.
  - `check_behavior.py` `echo_values` reads angle `echo` only from the top-level `scad`, not
    from joint bodies' `scad` (loud FAIL, not a false PASS).
  - `bounded_depth` suspected: a thin plate deep inside a block is measured by its thickness.
  - `$fn/$fa/$fs` into `limits.lock`; HMAC receipts; hook installation from `install.sh`.
  - Second external audit: DOF/ground, joint_graph `bridge`, `hole_radius`, printability,
    attachment, bores, subfeature, `--all` end to end.
  - Mutant-coverage gate per checker; more metamorphic and analytic reference cases.
  - Purchased-parts library (MG996R, Z-S0398, INJORA).
  - Joint angle from geometry, not from `echo`.
- [ ] **P25 rest (protected laws).** `limits.lock` for the RC projects (needs the maintainer's
  quote); property-based tests (Hypothesis / CrossHair), TLA+ model, Sigstore receipts, mutmut
  trial — all optional, try only if a real false PASS shows the need.
- [ ] **P20b limit.** The host-hole inventory checks only one (the largest) contact plane of a
  mounted part; a part touching the host on two planes can still hide a covered hole.
- [ ] **PETG tolerances** — only after measuring: print `calibration_coupon()`
  (`openscad-cad/references/patterns.scad`, Pattern 5) in PETG, measure, record in
  `openscad-cad/references/tolerances.md` § PETG (printer, material, layer, sample, measured vs
  reported). Maintainer's job; never invent numbers.
- [ ] **Plugin icon** (`.claude-plugin/icon.png`, 512–2048 px) — only if submitting to the
  official plugin catalogue.
- [ ] **Donation button** — `.github/FUNDING.yml` + README link once GitHub Sponsors / Ko-fi
  accounts exist.
- [ ] **Exit-code unification** — deliberately not done: `validate_scad.sh` and fixtures rely on
  the current codes (6 checkers return 1, 6 return 3). Only together with a `check_*.py` v2 and
  a compatibility layer.
- [ ] **Cost re-measurement** — agent cost was not re-measured after the context-leak fix and
  P18/P19 slimming; measure together with coverage, not alone (needs approval if it uses paid
  runs).
