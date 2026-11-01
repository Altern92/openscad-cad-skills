# P15: honest verdict -- declarations required, no empty PASS, INCONCLUSIVE is not success (AC)

Date: 2026-11-01. Tier: bounded (validate_scad.sh, check_rules.py, templates, docs). Approved in advance
("darome viska pagal tavo rekomendacijas"; audit follow-up "jei yra kas naudingo pridek ir test vystyma").
Origin: an external audit (MBP, 2026-11-01), every claim re-checked on the mini before use.

## Evidence (re-measured on the mini, examples/gear_reduction)
- 20 CHECK_RESULT lines, `dimensions=SKIP`, `topology=SKIP`: the reference example declares no
  `EXPECTED_BBOX` / `EXPECTED_THROUGH_HOLES`, so a 62 % thinner gear (audit M4) passes everything.
- `plan=PASS` and `service_envelope=PASS` without plan.md / service_envelope.md (checkers return 0 on a
  missing file); the example has 2 parts, but a 3-part project without a plan also passes.
- `INCONCLUSIVE` only bumps a counter (validate_scad.sh:71): exit 0 and "All validations passed.".
- The NEXT line says `python3 .../check_rules.py`; run that way, the gates inside it use the system
  python3 without trimesh (audit: false FAIL R-06). check_rules.py runs gates with `shell=True`.
- templates/part_template.scad defines `part_geometry()`, assembly.scad dispatches by part name.
- templates/bores.json says "IN ASSEMBLY COORDINATES"; validate_scad.sh passes `build/*.stl`, the
  local-frame part renders (check_attachment.py says local too).

## AC
- AC-1 (declarations): Given `--all` and a `parts/X.scad` with neither `// EXPECTED_BBOX:` nor
  `// NO_BBOX: <reason>`, then `CHECK_RESULT declarations=FAIL` naming X and the missing line, exit 1.
- AC-2: Same for `// EXPECTED_THROUGH_HOLES: N` vs `// NO_THROUGH_HOLES_CHECK: <reason>`.
- AC-3: Given every part declares both (or an escape with a non-empty reason), then `declarations=PASS`.
  An escape with an empty reason (`// NO_BBOX:`) counts as missing.
- AC-4: Single-file mode applies AC-1..3 to that one file.
- AC-5 (plan antecedent): Given no plan.md and >= 3 `parts/*.scad`, then `plan=FAIL` ("§0.5 plan.md is
  required for 3+ parts"); with < 3 parts, `plan=SKIP`, never PASS.
- AC-6: Given no service_envelope.md, then `service_envelope=SKIP`, not PASS.
- AC-7 (INCONCLUSIVE): Given no FAIL and >= 1 INCONCLUSIVE, then exit 2, last line starts
  `NOT VERIFIED:`, state file verdict `INCONCLUSIVE`. FAIL still wins (exit 1).
- AC-8: Given a clean run with SKIPs, then the last line is
  `All executed checks passed (P passed, S not-applicable, A advisory).`, exit 0.
- AC-9 (interpreter): check_rules.py runs every gate with resolve_python.sh sourced, so a `python3`
  gate gets the mesh interpreter even when check_rules.py itself was started by the system python3.
  The NEXT line prints the resolved interpreter, not bare `python3`.
- AC-10 (docs): SKILL.md commands use `$S=~/.claude/skills/scad-modeler/scripts`, not project-relative
  `scripts/`; part_template.scad says to rename `part_geometry` to the part's name; bores.json says
  part-local coordinates; examples/gear_reduction declares EXPECTED_BBOX + EXPECTED_THROUGH_HOLES.
- AC-11: Suite green in dev and via ~/.claude/skills; mutants.tsv unchanged in shape; new fixture(s)
  fail when the feature is reverted.

## Decisions
- Required, not opt-in: a missing declaration is a true finding ("this dimension was never checked"),
  so it is FAIL, not a false positive. The escape needs a written reason, which the report shows.
- `intake` stays SKIP (P5 will put requirements in front of geometry); rule R-01 already runs it.
- Out of this round: coplanar-contact collision false FAIL (audit E1, conditional, needs a repro),
  DSH lifecycle hook (F4), auto-declarations from requirements.json (P5).
