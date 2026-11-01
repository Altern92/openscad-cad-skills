# P2 + P12: static SCAD lint and through-hole topology (AC)

Date: 2026-11-01. Tier: feature (two new checkers wired into validate_scad.sh).
Origin: NEXT.md P2 ("not yet" incidents) and P12 (EvoCAD 2510.11631, Euler characteristic).

## Baseline (measured 2026-11-01)
- Suite 57/57 green; `tests/mutants.tsv` lists 16 checkers, `mutant_coverage` requires every
  `check_*.py` to have a row.
- P2(c) is already covered: every script reads STL via trimesh or `stl_extent.py` (ASCII + binary,
  fixture `stl_extent_both_formats`). No `struct.unpack("<I")` outside `stl_extent.py`.
- Euler test on real Manifold renders: two through-holes χ=−2 g=2; one blind χ=0 g=1; both blind χ=2 g=0.

## P2 – `scripts/check_scad_lint.py --project-dir .` (stdlib, static)
Scans `params.scad`, `layout.scad`, `assembly.scad`, `parts/*.scad` and, in single-file mode, the
given `.scad`. Exit 0 pass, 3 fail, 4 usage – same as the other checkers.
- AC-1 (computed default): Given `beam.scad` with `module beam(len = 211)`, `assembly.scad`
  calling `beam(len = span - 2*node_r)` and `beam.scad` calling `beam()`, then FAIL naming `beam`,
  `len`, `211`, the computing call and the omitting call, exit 3.
- AC-2: Given the same module where every call passes a numeric literal (`beam(len = 211)`), or the
  default is `undef`, or every call passes the argument (computed or not), then PASS, exit 0.
  *Revised during GREEN (2026-11-01):* the first rule ("any computed caller") fired on ordinary API
  defaults in BOSL2 (bottlecaps), NopSCADlib (pcb, radial, psu) and MCAD; the incident itself needs
  a caller that omits the argument.
- AC-3 (rounded standard): Given `unit_1U = 44.5;` (or `rack_u = 44.4`), then FAIL naming the line and
  the exact value `44.45` (EIA-310), exit 3. Table (name-gated, value within 2 % but not equal):
  1U 44.45, inch 25.4, 19" panel 482.6, EIA hole pitch 15.875.
- AC-4: Given `unit_1U = 44.45;`, or `wall = 44.5;` (name not in the table), then PASS.
- AC-5: Comments and strings are ignored (`// was 44.5` does not fire).
- AC-6: `validate_scad.sh` prints `CHECK_RESULT scad_lint=PASS|FAIL` in project and single-file
  mode; a FAIL makes the verdict FAIL and exit 1.

## P12 – `scripts/check_topology.py --stl X.stl --scad X.scad` (trimesh)
- AC-7: Given a plate with 2 through-holes declaring `// EXPECTED_THROUGH_HOLES: 2`, then PASS, exit 0.
- AC-8: Given the same plate with one hole sealed by a 0.4 mm skin (still declaring 2), then FAIL
  saying expected 2, found 1 (χ, bodies printed), exit 3.
- AC-9: Given no `EXPECTED_THROUGH_HOLES` line, then SKIP with reason, exit 0 – never a guess.
- AC-10: Given a non-watertight mesh, then FAIL "genus undefined: mesh not watertight", exit 3
  (not a silent PASS).
- AC-11: `validate_scad.sh` prints `CHECK_RESULT topology=PASS|FAIL|SKIP` per part, counted in
  `COVERAGE`.

## Shared
- AC-12: `tests/mutants.tsv` has rows for both checkers; `mutant_coverage` stays green, and each
  checker stubbed to `exit 0` makes its fail fixture FAIL.
- AC-13: Docs: scad-modeler SKILL.md (validation table) documents both declarations;
  openscad-cad SKILL.md says ad-hoc STL measuring goes through `stl_extent.py` (P2c);
  `skill_docs_match_code` and `env_gate_documented` stay green.
- AC-14: Full suite green in dev and via `~/.claude/skills`; `examples/gear_reduction` CHECK_RESULT
  lines unchanged except the two new lines (scad_lint, topology=SKIP).

## Provisional assumptions
- AC-1 only reads keyword arguments; positional calls (`beam(216.5)`) are not seen. shortcut, documented.
- Genus counts handles, not holes: a through-slot or ring counts 1, two intersecting bores can count
  more. The declaration is "topological through-holes"; SKILL.md says so.
- P13 (variable-change test) is not in this round.
