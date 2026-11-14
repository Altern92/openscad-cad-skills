# 12 — Handoff to the `scad-modeler` owner (Claude)

**To:** whoever maintains `scad-modeler` (`~/Github/Claude_Code_SCAD_Skill/`, canon
`~/Skills-plugins-etc/skills/scad-modeler/`).
**From:** the OpenSCAD GenKit project. **Date:** 2026-11-01.
**Status:** GenKit P0–P5 complete; 53 tests green; 8 modules + generator work.
**Gate version this document was written against:** `validate_scad.sh` ~1185 lines, 2026-11-01
(after P15–P17). If the file grew significantly, line numbers shifted, but the semantics
(S-1/S-2/S-3/S-6 ✓, S-4/S-5 ✓) were checked against that version.

**One sentence:** GenKit produces `.scad` files whose declarations (`// EXPECTED_*`) are **always
present**, so the skill only needs **deployment** — the semantic fixes are already in.

---

## 1. What GenKit gives the skill

| Artefact | Where | What it means for the skill |
|---|---|---|
| `kit/*.scad` (9 files) | `OpenSCAD_GenKit/kit/` | 8 parametric modules with `assert` + `kit_bbox_<name>()`; each `.scad` can be validated as a normal part |
| `gen/emit_part.py` | `OpenSCAD_GenKit/gen/` | `requirements.json` → `.scad` **with `// EXPECTED_BBOX` and `// EXPECTED_THROUGH_HOLES`** |
| `tests/run_all.sh` | `OpenSCAD_GenKit/tests/` | 11 golden + 40 mutants + assembly + gate-mutant; ~40 s |
| Contract | — | `.scad` + `// EXPECTED_*` — **nothing else**. No skill API changes needed |

**Why it matters:** until now `dimensions`/`topology`/`features` were **opt-in** — `SKIP` without a
hand-written declaration. GenKit files never lack one, so those gates become mandatory for real.

---

## 2. What the skill ALREADY has (verified 2026-11-01, not my work)

| S | Status | Evidence |
|---|---|---|
| S-1 verdict semantics | ✓ | `INCONCLUSIVE` → final line `NOT VERIFIED: 1 check(s) could not determine an answer`, **exit 2** (`validate_scad.sh:1179-1181`); demo: 2 parts with `// NO_JOINT:` + `joints.json` `motion` without `assembly.scad` → `8 passed, 0 failed, 1 inconclusive`, exit 2 |
| S-2 declaration coverage | ✓ | `declarations=FAIL` without `// EXPECTED_BBOX` **or** `// NO_BBOX: <reason>` (`:237-239`, PASS `:1097`); `NO_BBOX` without a reason → FAIL |
| S-3 missing artefact ≠ PASS | ✓ | `plan=FAIL` for 3+ parts without `plan.md`, `SKIP` for 2 parts; `service_envelope` without a file → `SKIP` |
| S-6 coplanar FCL | ✓ | `box`+`lid` contact (`touching`, `[0,0]`) → `collisions=PASS`, no 40 mm phantom |

If any of these changed in the skill — **first read `docs/10` §7** (gate state after the rewrite) and
run its reproductions; the exact current semantics live there.

## 3. Status 2026-11-01: S-4 and S-5 are done in the skill

> Updated after the audit (`docs/13`). The previous version of this section predates the skill fixes.

### S-4 — ✅ done (dev `2812edd`)

With `design_manifest.json` → `intake=PASS|FAIL` (verified: an invalid manifest → `intake=FAIL`, not
SKIP).

### S-5 — ✅ done (dev `984c8a5`)

All mesh checkers re-exec into the venv. Verified:
`/usr/bin/python3 check_connectivity.py --stl x.stl --scad pwh.scad` → `OK: 1 connected body`.
`check_rules.py` with system `python3` on a clean project → exit 0.

**Audit correction:** the earlier claim "`check_rules.py` → exit 3 (false FAIL)" was true **before**
S-5; it no longer reproduces. Correct wording: *it was an environment error masked as a rule failure;
fixed.*

### What remains

1. **Deployment** (below) — moving `kit/` and `gen/` into the skill.
2. **Migration:** the skill already has `references/validation.md` §"Migrating an older project" —
   `docs/09` must point there instead of its own script.

### Deployment

1. Decide whether `kit/` and `gen/` are copied into `scad-modeler/` as a package or kept as a side
   project (both work — see `docs/09` §Integration steps).
2. Includes: the generator writes **absolute** `include <$KIT/...>`; `--kit-root` overrides the
   location. Module files include each other relatively (`include <lib.scad>`).
3. `SKILL.md`: add a "Generator" section with `make part JSON=...` and a pointer to the
   `requirements.json` schema (`gen/schema.json`).
4. Add the GenKit tests to `scad-modeler/tests/run_all.sh` (or a separate entry) — **run both**:
   skill 82 and GenKit 53.
5. `deploy_to_canon.sh` → canon → `~/.claude/skills` symlink.

---

## 4. Contract and hard prohibitions

- **Do not change the `// EXPECTED_*` format.** That is the GenKit contract. Format:
  `// EXPECTED_BBOX: [w, d, h]`, `// EXPECTED_THROUGH_HOLES: N`,
  `// EXPECTED_HOLE: [x, y, z, "Z", d]`, `// NO_BBOX: <reason>` (≥ 10 characters).
- **Do not put geometric limits into the JSON schema** — they belong in OpenSCAD `assert()`
  (otherwise mutants are rejected at the schema level and the assert is never exercised).
- **`custom()` is not generated** — it returns `unsupported_kind` (exit 4) with BOSL2 / "split it"
  pointers. A deliberate boundary, not a bug.
- **Do not change the GenKit hole table** (`kit/lib.scad`, ISO 273: M3 3.4, M4 4.5, M5 5.5, M6 6.6)
  without a decision record — the generator **reads** it from there
  (`grep -c "3.4" gen/emit_part.py` → 0).

---

## 5. How to check you broke nothing

```bash
cd /Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit
bash tests/run_all.sh          # 53 passed, 0 failed (~40 s)
```

If you changed the gates — **read `docs/10` §7** and re-run the commands there.
Gate output format: `CHECK_RESULT <gate>=<VERDICT>` (**no colon**) and
`COVERAGE: X passed, Y failed, Z not-applicable, W inconclusive, V advisory (N checks reported…)`.

If you rewrote the gates substantially — GenKit has a **P0b re-baseline** protocol (`NEXT.md` P0b,
`docs/10` §7): bring `docs/04/05/09/10`, `README`, `HANDOFF` back in line.

---

## 6. What GenKit does NOT do (so you do not read it as a gap)

| Boundary | Reason |
|---|---|
| Composite request decomposition | "box with a lid and 4 screws" → 1 brief ≠ 1 part; must be split at **intake** (S-4) |
| `box` screw holes | needed by one P5 brief only; honestly refused for now |
| Free-form geometry (gears, hinges) | `custom()` + BOSL2; deliberately not built |
| Assembly generation | GenKit generates **parts**; `assembly.scad` is written by hand (see `tests/run_all.sh` step 3 for an example) |

---

## 7. Risks you should know

1. **Shared file:** if you change `validate_scad.sh` semantics, GenKit `docs/04` AC-22/AC-23 may no
   longer match. Tell the GenKit agent or update `docs/10` §7.
2. **Silent regression:** the 53 GenKit tests fail if the `COVERAGE` format, `CHECK_RESULT` lines or
   the `build/` location change (the gates create `build/` in the **current** directory).
3. **False "done" rule** (`docs/06` V3): one PASS with wrong geometry blocks release. One was found
   during P5 (`bracket_l` — both holes in one leg) and fixed; if it reappears — **block**, do not fix
   "later".
4. **Do not weaken `assert`s** to make tests pass. If a GenKit file fails, the error is on the GenKit
   side (`kit/`), not in the gates.

---

## 8. Where to find details

| Question | Document |
|---|---|
| What GenKit does and why | `docs/01`, `docs/02` (ADR-001…ADR-006) |
| Module API, `assert`, declarations | `docs/03` |
| Acceptance criteria (AC-01…AC-40) | `docs/04` |
| Error format, mutants | `docs/05` |
| Risks, V1–V4 gates, P5 result | `docs/06` |
| P5 measurement (7/10 = 70 %) | `docs/08`, `docs/11` |
| The S-1…S-6 changes | `docs/09` |
| Gate semantics after the rewrite + reproductions | `docs/10` §7 |

**Test status at handoff (verbatim):**

```text
$ bash tests/run_all.sh
...
53 passed, 0 failed
real    0m40s
```
