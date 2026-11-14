# NEXT.md — work queue

The single list. An agent takes **only** the top unchecked item. Every item references an AC in
`docs/04_acceptance_criteria.md`.

| # | Work | AC | Estimate | Status |
|---|---|---|---|---|
| **P0** | Contract: conventions, error format, `requirements.json` schema | AC-01…AC-04 | 0.5 d | ✅ (AC-01 approved 2026-11-01) |
| **P0b** | Re-baseline after the gate rewrite (2026-11-01 13:16–13:38): align `docs/04/05/09/10`, `README`, `HANDOFF` | AC-34…AC-37 + P0/P2 corrections | 0.5 d | ✅ 2026-11-01 |
| **P1** | Kit v0: 8 modules + `kit_bbox_<name>()` + `assert()`; thin slice first (pwh + box + lid + generator → e2e PASS) | AC-05…AC-20 | 2–3 d | ✅ 2026-11-01 (8/8 PASS) |
| **P2** | Tests: 11 golden + **40 mutants** (one per `assert`) + assembly, `run_all.sh` (≤ 120 s) | AC-21…AC-26 | 1–2 d | ✅ 2026-11-01 (53 passed, ~40 s) |
| **P3** | Generator `gen/emit_part.py` (JSON → .scad + declarations) | AC-27…AC-33 | 2–3 d | ✅ 2026-11-01 (7/7 AC) |
| **P4′** | Integration spec for the skill (NOT code) → `docs/09` | AC-34…AC-37 | 0.5 d | ✅ 2026-11-01 |
| **P5** | Measurement: 10 real briefs, one-shot rate | AC-38…AC-40 | 2–3 d | ✅ 2026-11-01 (7/10 = 70 %, 0 false) |
| **P6** | F1: `bracket_l` → `EXPECTED_HOLE` for both legs + regression test | `docs/13` F1 | 0.5 d | ✅ 53 passed |
| **P7** | Docs sync: AC-17 wording, `docs/09/12` migration pointer, numbers, English | `docs/13` F2/F4/F5 | 0.5 d | ✅ |
| **P8** | Audit §5 #1/#2/#3/#5/#6/#7: deploy to `scad-modeler` + `deploy_genkit.sh` + `EXPECTED_BBOX_TOL` + `geom_mutation.py` + `box` screw holes + composite `box_with_lid` (P5 8/10) | Audit §5 | 1 d | ✅ 2026-11-02 (59/59 GenKit, 136 geom mutants 0 new survivors, P5 8/10) |

## P0 — Contract

- [x] `docs/01…13` read and approved (AC-01) — user approved 2026-11-01
- [x] `gen/schema.json` + `gen/validate_schema.py` (AC-02) — 9/9 OK; negative tests 4/4 FAIL
- [x] `requirements.json` schema frozen (`docs/03_module_api.md` §Schema)
- [x] Error format frozen (`docs/05_tests_and_errors.md` §Format) (AC-03)
- [x] Conventions: mm, +Z, local origin, module name `kit_<name>` (AC-04)

### P0 result (2026-11-01)

```bash
python3 gen/validate_schema.py --self-check          # OK schema, exit 0
python3 gen/validate_schema.py tests/fixtures/*.json examples/*.json
# 9/9 OK, 0 failed
python3 gen/validate_schema.py /tmp/badreq/*.json    # 4/4 FAIL, exit 4
#   missing.json  -> params: 't' is a required property
#   typo.json     -> Additional properties are not allowed ('thickness')
#   baddate.json  -> source/date: 'lapkritis' is not a 'date'
#   badkind.json  -> kind: 'gearbox' is not one of [...]
```

Created: `gen/schema.json`, `gen/validate_schema.py`, `tests/fixtures/*.json` (8 at the time),
`examples/bracket_80x50.json`.

**Deliberate decision:** the schema contains **no geometric limits** (e.g. `t >= 1.2`). Those belong
in OpenSCAD `assert()` — otherwise the P2 mutants would be rejected at the schema level and the
assert would never be exercised.

## P1 — Kit v0

- [x] `kit/lib.scad` (hole table, tolerances, helpers)
- [x] 8 modules: `plate`, `plate_with_holes`, `bracket_l`, `box`, `lid`, `boss`, `hole_pattern`, `snap_hook`
- [x] every module: `assert()` with a number and a suggestion
- [x] `examples/all_modules.scad`

## P2 — Tests

- [x] 11 fixtures, 40 mutants, 40 expected messages
- [x] `tests/assert_coverage.tsv` (40 rows)
- [x] `tests/run_all.sh` — 4 sections (golden, mutants, assembly, gate-mutant)

## P3 — Generator

- [x] `gen/emit_part.py` with `--check`
- [x] `jsonschema` validation + re-exec into the venv
- [x] declarations: `EXPECTED_BBOX`, `EXPECTED_THROUGH_HOLES`, `EXPECTED_HOLE` (boss, bracket_l)
- [x] missing parameters → list on stderr, exit 4, **no file**

## P4′ — Integration spec (not code)

> The skill may not be modified here — it is maintained by another agent. This item is a
> **document**, not an implementation.

- [x] `docs/09_skill_integration.md`: S-1…S-6 with ACs
- [x] S-1 verdict semantics, S-2 declaration coverage, S-3 missing artefact ≠ PASS
- [x] S-4 intake, S-5 `resolve_python.sh`, S-6 coplanar — all done in the skill (dev `984c8a5`)

## P5 — Measurement

- [x] 10 briefs from `docs/11_p5_briefs.md` (verbatim)
- [x] table: brief → module → PASS/FAIL → second round?
- [x] decision gates per `docs/06_risks_and_gates.md` (V3 passed: 7/10, 0 false)

### P5 result (2026-11-01)

```bash
python3 tests/p5/run_p5.py --briefs tests/p5/briefs_real.json
# First-pass success: 7/10; honestly refused: 3
```

The real run found one bug the gates missed: `bracket_l` put both holes in the horizontal leg
(`THROUGH_HOLES=2` matched, so the gates passed). Fixed; now covered by `gm_br_orientation`
(docs/13 F1).

## P6 — F1: hole orientation (after audit `docs/13`)

- [x] `emit_part.py`: `bracket_l` → `// EXPECTED_HOLE` for the horizontal leg (`"Z"`) and vertical leg (`"Y"`)
- [x] gate-mutant in `run_all.sh`: a mutated `kit/` with both holes horizontal must fail `features`
- [x] result: `PASS gm_br_orientation features=FAIL (Y axis hole not found)`

**Why:** the P5 bug passed the gates because the only declaration was `THROUGH_HOLES: 2`. This was the
only finding that could silently return.

## P7 — Docs sync

- [x] AC-17 rewritten as MANUAL (grep cannot distinguish `d / 2` from a literal)
- [x] `docs/09`/`docs/12`: pointer to the skill's `references/validation.md` §"Migrating an older project"
- [x] numbers: `README` 40 s, `NEXT` 40 mutants, `docs/08` single table
- [x] all docs translated to English; `README.md` now contains the deployment guide
