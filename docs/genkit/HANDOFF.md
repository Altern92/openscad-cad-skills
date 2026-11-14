# HANDOFF — start here

This is the **only entry point**. Read it fully (10 min), then go to `NEXT.md`. Everything else is
detail for what is described here.

---

## 1. What you are building

**OpenSCAD GenKit** — a parametric generator that turns `requirements.json` into a `.scad` file
**together with declarations** (`// EXPECTED_BBOX`, `// EXPECTED_THROUGH_HOLES`), so that LLM-generated
models can be verified deterministically instead of "looks fine".

Goal: **the user says once what they want → a correct model, no second round.** Success is measured
as ≥ 70 % one-shot and **0** cases of PASS with wrong geometry (`docs/08_p5_measurement.md`).

## 2. Your boundaries (hard)

| Allowed | Forbidden |
|---|---|
| Write **only** inside this folder (`OpenSCAD_GenKit/`) | Modify `~/Skills-plugins-etc/` or `~/Github/Claude_Code_SCAD_Skill/` |
| **Call** skill scripts for reading (`validate_scad.sh`, `check_*.py`) | Change their code, semantics, thresholds |
| Change `kit/`, `gen/`, `tests/`, `docs/` | Change the `// EXPECTED_*` format (it is the contract) |
| Write integration specs (`docs/09`) | Implement skill changes (that is the other agent's work) |

**Why:** the skill is maintained by a different agent (Claude) and has its own test suite (82 tests).
If you touch its files you break a regression you cannot verify. Your product will be **copied** into
the skill later.

**The contract with the skill is only:** a `.scad` file + `// EXPECTED_*` comments. Nothing else. If it
seems the skill must change — write it into `docs/09_skill_integration.md`, not into code.

## 3. Environment (verified 2026-11-01)

| What | Where |
|---|---|
| OpenSCAD | `~/.local/bin/openscad` (2026.10.11, Manifold) |
| BOSL2 | `~/Documents/OpenSCAD/libraries/BOSL2/` |
| Python venv (has trimesh etc.) | `~/.local/share/scad-modeler/venv/bin/python` |
| Gates (canon) | `~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh` |
| Gates (dev) | `~/Github/Claude_Code_SCAD_Skill/claude_skills/scad-modeler/scripts/validate_scad.sh` |
| Skill tests | `bash <dev>/claude_skills/scad-modeler/tests/run_all.sh` (82 tests) |

**The system `python3` has no `jsonschema` / `trimesh` — that is an environment fact, not a bug.** Use
the venv or re-exec (example: `gen/validate_schema.py`).

## 4. Commands that work today

```bash
cd /Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit

# schema check
python3 gen/validate_schema.py tests/fixtures/*.json        # → 8/8 OK

# one module
openscad -o /tmp/m.stl kit/plate_with_holes.scad

# gates on one file
bash ~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh /tmp/part.scad

# full project (parts/ + assembly.scad)
bash ~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh --all

# all GenKit tests
bash tests/run_all.sh                                       # 53 passed
```

## 5. What to do now

1. Read `NEXT.md` — the work queue. **Take only the first unchecked item.**
2. Read `docs/03_module_api.md` (module spec) and `docs/05_tests_and_errors.md` (error format).
3. **Recommended order:** thin vertical slice first — `plate_with_holes` + `box` + `lid` + generator —
   and prove end-to-end that declarations turn `SKIP` into `PASS`. Only then the remaining 5 modules.
   (Already done; kept here for re-runs.)
4. **Stop rule:** if within 2 days the generator cannot produce a PASS with declarations — stop and
   report; the architecture is wrong.

## 6. Ten facts I learned the hard way (do not re-learn them)

1. **`validate_scad.sh` printed "All validations passed" with SKIPs** (before 2026-11-01). Never trust
   the last line — read `CHECK_RESULT` and `COVERAGE`.
2. **`check_plan.py` without `plan.md` returned exit 0 → PASS** (now SKIP/FAIL). The same for
   `check_service_envelope.py`.
3. **`intake` was hard-coded `SKIP`** in `validate_scad.sh` — it never fired (now fixed).
4. **`INCONCLUSIVE` did not change the exit code** (now exit 2, `NOT VERIFIED`).
5. **The canonical example had no `EXPECTED_BBOX`** — so `dimensions=SKIP` even there (now the
   `declarations` gate forces it).
6. **FCL wrongly reports a 40 mm overlap** between exactly coincident faces (0 volume). Not
   reproducible with plain cubes; reproducible with a box + thin lid.
7. **`part_template.scad` module `part_geometry()`** does not match §6 dispatch by part name — the
   first render fails.
8. **`bores.json` says "assembly coordinates", `check_attachment.py` says "local"**; both read the
   local STL.
9. **`check_rules.py` with the system `python3` gave a false FAIL** (`trimesh not installed`) — fixed
   in the skill (S-5, dev `984c8a5`).
10. **`plan` and `service_envelope` never moved out of PASS in 436 runs** — dead gates
    (`~/.claude/scad_modeler/validation_log/`).

Full list with reproduction commands: `docs/10_audit_findings.md`.

## 7. Decisions you should not revisit

| Decision | Document |
|---|---|
| Generator in Python, not Rust | `docs/02` ADR-001 |
| Parameters in JSON, not SQLite | ADR-002 |
| SCAD kit before a host builder | ADR-003 |
| No home-grown CAD kernel | ADR-004 |
| Gate semantics are not your job | ADR-005 + `docs/09` |

## 8. Definition of done

- ACs met and **command output pasted** (no paraphrase);
- `bash tests/run_all.sh` → `0 failed`;
- `NEXT.md` updated (`[x]` + result);
- no changes outside this folder.

## 9. When you are stuck

1. Write `BLOCKED: <reason>` next to the item in `NEXT.md`.
2. If the environment is missing (OpenSCAD, BOSL2) — give the command that restores it.
3. If an AC is unclear — **one** question to the user with a proposal.
4. Do not take the next item. The queue is the queue.

## 10. Document map

| File | When to read |
|---|---|
| `AGENTS.md` | always first (rules) |
| `NEXT.md` | always (work queue) |
| `docs/01_goal_and_context.md` | context and metrics |
| `docs/02_architecture.md` | layers and ADRs |
| `docs/03_module_api.md` | **while working on a module** |
| `docs/04_acceptance_criteria.md` | before saying "done" |
| `docs/05_tests_and_errors.md` | error format and tests |
| `docs/06_risks_and_gates.md` | risks and decision gates |
| `docs/07_agent_workflow.md` | working procedure and report format |
| `docs/08_p5_measurement.md` | measurement (P5) |
| `docs/09_skill_integration.md` | integration into the skill (not your code) |
| `docs/10_audit_findings.md` | audit knowledge and reproductions |
| `docs/11_p5_briefs.md` | the 10 P5 briefs |
| `docs/12_handoff_claude.md` | handoff to the skill owner |
| `docs/13_audit_2026-11-01.md` | post-implementation audit |
