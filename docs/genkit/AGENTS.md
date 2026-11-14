# AGENTS.md — OpenSCAD GenKit

You are an engineer implementing a parametric OpenSCAD generator. The user is Lithuanian; runtime
error messages are Lithuanian. Code, identifiers, docs and commit messages are English.

**Repo rules also apply:** `/Volumes/SSD_1TB/Docs/AGENTS.md` (11 core rules). This file only makes
them concrete for this project.

## Reading order (mandatory before any work)

0. `HANDOFF.md` — the only entry point: boundaries, environment, commands, hard-won facts.
1. `NEXT.md` — which task now (P0–P7). **Never take work that is not there.**
2. `docs/01_goal_and_context.md` — why, and which metrics.
3. `docs/03_module_api.md` — what the modules build.
4. `docs/04_acceptance_criteria.md` — when the work counts as done (per phase).
5. `docs/07_agent_workflow.md` — commands, DoD, report format.

## Hard rules

1. **Do not modify the skill** (`~/Skills-plugins-etc/`, `~/Github/Claude_Code_SCAD_Skill/`). This
   folder is self-contained; deployment is a separate step per `SKILLS-CANON.md`.
2. **One item = one `feature-loop` cycle** per `NEXT.md`. No "while I'm here".
3. **No coordinates in the geometry body.** If a module needs `translate([x,y,z])` with a "magic"
   number, that is a module API gap, not a solution.
4. **Every `assert()` must carry a number and a suggestion** (format: `docs/05_tests_and_errors.md`).
   `assert(false, "invalid parameters")` is rejected.
5. **Every module must provide `kit_bbox_<name>()`** — without it the generator cannot derive
   `// EXPECTED_BBOX`.
6. **Declarations are written by the generator, not by a human.** Hand-written `// EXPECTED_*` is
   allowed only for `custom()`.
7. **Tests before beauty.** A module without a mutant test (bad parameter → FAIL) is not done.
8. **No new dependencies** (Python or OpenSCAD) without a decision record in
   `docs/02_architecture.md` §Decisions.
9. **Do not change gate semantics** (`validate_scad.sh`, `check_*.py`) — that is a separate job with
   its own AC and user approval.
10. **When done** — record the result in `NEXT.md` (what was done, which ACs met, which tests) and
    report per `docs/07_agent_workflow.md` §Report.
11. **The contract with the skill is `.scad` + `// EXPECTED_*` comments.** Nothing else: no skill API
    changes, no new fields the skill does not understand.
12. **If the skill is absent** (another machine), tests skip those checks with
    `SKIP: skill not installed` — not FAIL.
13. **Skill changes go into `docs/09_skill_integration.md`, not into code.** That is another agent's
    work.
14. **`custom()` is not generated** — return `unsupported_kind` and ask a human.

## Do not

- Write your own CAD kernel (booleans, B-rep, mesh repair). Geometry is OpenSCAD + BOSL2.
- Rewrite the validator in Rust (decision: `docs/02_architecture.md` §Decisions, ADR-001).
- Put parameters into SQLite (ADR-002).
- Generate `custom()` with free coordinates and no declarations.

## Definition of done

1. The item's ACs are met and ticked in `NEXT.md`;
2. `bash tests/run_all.sh` — green;
3. `validate_scad.sh --all` on the example project — `COVERAGE: … 0 failed`, no `SKIP` for gates that
   have declarations;
4. a report with commands and outputs (not a paraphrase).
