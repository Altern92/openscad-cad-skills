# 04 — Acceptance criteria (AC)

Every AC has a **command** and an **unambiguous result**. An AC that cannot be run is not an AC.

## P0 — Contract

| ID | Criterion | Check | PASS |
|---|---|---|---|
| AC-01 | Documentation read and approved | `NEXT.md` P0 checkboxes | all `[x]` |
| AC-02 | `requirements.json` schema frozen | `python3 gen/validate_schema.py tests/fixtures/*.json` | 8/8 `OK`, 0 errors |
| AC-03 | Error format frozen | `grep -c "KLAIDA:" docs/05_tests_and_errors.md` | ≥ 3 examples; format `KLAIDA: … → … → …` |
| AC-04 | Conventions written down | `grep -c "mm" docs/03_module_api.md` | > 0 |

## P1 — Kit v0

| ID | Criterion | Check | PASS |
|---|---|---|---|
| AC-05 | Hole table in one source | `grep -c "M4" kit/lib.scad` | ≥ 1 (table **only** in `kit/lib.scad`) |
| AC-06 | 8 modules exist | `ls kit/*.scad \| wc -l` | 9 (8 + `lib.scad`) |
| AC-07 | Every module has `kit_bbox_<name>` | `grep -c "function kit_bbox_" kit/*.scad` | 8 |
| AC-08 | Each module renders standalone | `for f in kit/*.scad; openscad -o /dev/null $f` | exit 0 for all |
| AC-09 | `plate` bbox correct | render + `stl_extent.py` | `[w,d,t]` ± 0.05 mm |
| AC-10 | `plate_with_holes` bbox + 4 holes | `check_topology.py` | bbox ± 0.05, genus 4 |
| AC-11 | `bracket_l` bbox + 2 holes | `check_topology.py` | bbox ± 0.05, genus 2 |
| AC-12 | `box` bbox, 0 holes | `check_topology.py` | bbox ± 0.05, genus 0 |
| AC-13 | `lid` bbox `[w,d,t+lip]` | `check_dimensions.py` | ± 0.05 |
| AC-14 | `boss` bbox + bore | `check_features.py` | Ø ± 0.05 |
| AC-15 | `hole_pattern` bbox + nx*ny | `check_topology.py` | genus = nx*ny |
| AC-16 | `snap_hook` bbox | `check_dimensions.py` | ± 0.05 |
| AC-17 | No "magic" coordinates | **MANUAL**: `grep -n "translate(" kit/*.scad` + review | every argument is 0/±1 (ε) or derived from parameters; self-assessed in §8 |
| AC-18 | Every `assert` carries a number and a suggestion | `grep -c "assert(" kit/*.scad` vs `grep -c "mm\|Ø"` | every assert message has a number |
| AC-19 | `examples/all_modules.scad` | `validate_scad.sh` | 0 failed, `dimensions=PASS`, `topology=PASS` |
| AC-20 | BOSL2 is the only dependency | `grep -rn "include <MCAD" kit/` | 0 |

## P2 — Tests

| ID | Criterion | Check | PASS |
|---|---|---|---|
| AC-21 | `tests/run_all.sh` runs | `bash tests/run_all.sh` | exit 0 |
| AC-22 | 11 golden fixtures pass | harness output | 11/11 `PASS` |
| AC-23 | 40 mutants fail with the exact message | `diff` against `tests/expected/*.txt` | 40/40 match |
| AC-24 | Mutants cover every `assert` | `tests/assert_coverage.tsv` | 40/40 asserts mapped |
| AC-25 | Tests write outside the project only to `/tmp` | `git status` / `find /tmp` | no stray files |
| AC-26 | Tests < 120 s | `time bash tests/run_all.sh` | real < 120 s (actual ~40 s) |

## P3 — Generator

| ID | Criterion | Check | PASS |
|---|---|---|---|
| AC-27 | JSON → `.scad` | `python3 gen/emit_part.py examples/bracket_80x50.json -o out/b.scad` | file created, exit 0 |
| AC-28 | Missing parameters → list, no file | `python3 gen/emit_part.py tests/missing.json -o out/x.scad` | exit **4**, no file, stderr list |
| AC-29 | Declarations match reality | generated file → `validate_scad.sh` | `dimensions=PASS`, `topology=PASS` |
| AC-30 | Determinism | generate twice, `diff` | byte-identical |
| AC-31 | All 11 fixtures generate and pass | loop over `tests/fixtures/*.json` | 11/11 exit 0 + gates PASS |
| AC-32 | `custom` → refusal | `tests/custom.json` | exit 4, `unsupported_kind` |
| AC-33 | `--check` mode | `python3 gen/emit_part.py --check tests/fixtures/x.json` | writes nothing, exit 0 |

## P4′ — Integration spec (not code)

> The skill must not be modified here (boundary: `AGENTS.md` §2). These ACs check the **document**
> `docs/09_skill_integration.md`, which the skill owner later implements.

| ID | Criterion | Check | PASS |
|---|---|---|---|
| AC-34 | `docs/09` covers S-1…S-6 | `grep -c "^### S-" docs/09_skill_integration.md` | 6 |
| AC-35 | Every S item has an AC | `grep -c "\*\*AC:\*\*" docs/09_skill_integration.md` | ≥ 6 |
| AC-36 | Integration steps documented | `grep -c "deploy_to_canon" docs/09_skill_integration.md` | ≥ 1 |
| AC-37 | "Do not do" section present | `grep -c "Do not" docs/09_skill_integration.md` | ≥ 1 |

## P5 — Measurement

| ID | Criterion | Check | PASS |
|---|---|---|---|
| AC-38 | 10 real briefs table | `docs/08_p5_measurement.md` | 10 rows, each with module and result |
| AC-39 | One-shot success | same table | ≥ 70 % without a second round; **0** false "done" |
| AC-40 | Decision recorded | `docs/02_architecture.md` §Decisions | ADR-006 present |

## General rules

- An AC is met only with the **command output** in the report (no paraphrase).
- If an AC cannot run because of the environment, mark `BLOCKED` with the reason — never `[x]`.
- Changing an AC requires user approval and a matching `NEXT.md` update.
