# 09 — Integration into the `scad-modeler` skill

This document is **not implemented** by the GenKit agent. It is the spec for whoever owns
`scad-modeler`. Status as of 2026-11-01: **S-1…S-6 are implemented in the skill** (dev `984c8a5`);
what remains is deployment (see `README.md` §Deployment).

## What GenKit gives the skill

1. `.scad` files whose **declarations are always present** (`// EXPECTED_*` derived from
   `requirements.json`).
2. A `requirements.json` → `.scad` path that intake can call.
3. `tests/run_all.sh`, which checks the modules *and* the presence of declarations.

What GenKit cannot do itself (it may not touch the skill): make `SKIP` and `INCONCLUSIVE` fail the
run, and make declaration coverage a gate.

## Changes (S-1 … S-6)

### S-1 — Verdict semantics ✅ done (2026-11-01)

**Was:** `validate_scad.sh` printed "All validations passed." even with 7 SKIP and 1 INCONCLUSIVE;
`INCONCLUSIVE` only incremented a counter.
**Now:** `INCONCLUSIVE` → `VERDICT=INCONCLUSIVE`, exit 2, final line `NOT VERIFIED: N check(s) could
not determine an answer`; the success line is `All executed checks passed (N passed, N n/a, N advisory)`.
**AC:** a project with `mechanics=INCONCLUSIVE` → exit ≠ 0.

### S-2 — Declaration coverage gate ✅ done (2026-11-01)

**Was:** `dimensions`, `features`, `topology` ran only if the `.scad` carried a declaration comment.
**Now:** a `declarations` gate (`CHECK_RESULT declarations=PASS|FAIL`) requires `EXPECTED_BBOX` or
`// NO_BBOX: <reason>` on every printed part.
**AC:** a part without a declaration → `declarations=FAIL`, run exit ≠ 0.

### S-3 — A missing mandatory artefact is not PASS ✅ done (2026-11-01)

**Was:** `check_plan.py` without `plan.md` → exit 0 → `plan=PASS`; `check_service_envelope.py` the
same.
**Now:** both return exit 2 → `plan=SKIP`, `service_envelope=SKIP`.
**AC:** a new project without `plan.md` → `plan=SKIP`.

### S-4 — Un-hardcode `intake` ✅ done (dev `2812edd`)

**Was:** `intake=SKIP` unconditionally.
**Now:** with `design_manifest.json` it runs `check_intake.py` → `intake=PASS|FAIL`.
**AC:** a project with a manifest → `intake=PASS|FAIL`.

### S-5 — `resolve_python.sh` at every entry point ✅ done (dev `984c8a5`)

**Was:** mesh checkers called directly with `python3` reported "trimesh not installed" although the
venv existed (false FAIL).
**Now:** all mesh checkers re-exec into the venv; if the venv is missing, the message points to
`bash scripts/setup_env.sh`. Covered by the test `mesh_scripts_reexec_venv`.
**AC:** `/usr/bin/python3 check_connectivity.py …` → `OK`, never an ENV error when the venv exists.

### S-6 — Coplanar FCL guard ✅ done (P19)

**Was:** two parts with exactly coincident faces → `penetration depth 40.000 mm` for a 0-volume
intersection.
**Now:** the collision check reads two-face contact as 0 depth.
**AC:** a generated lid at `z = box_h` → `collisions=PASS`.

## Migration of older projects

The skill has the procedure: `scad-modeler/references/validation.md` §**"Migrating an older
project"**. Declarations are taken from **intent** (plan, `params.scad`, specification), never from a
render — otherwise existing errors would be recorded as the "correct" size.

## Deployment steps

1. Copy `kit/` and `gen/` into the skill (decide: inside `scad-modeler/` or a separate skill).
2. Adjust `include` paths — the generator writes **absolute** `include <$KIT/...>`; `--kit-root`
   allows another location. Module files include each other relatively (`include <lib.scad>`).
3. `SKILL.md`: add a "Generator" section (text in `README.md` §Step 3).
4. Add the GenKit suite to `scad-modeler/tests/run_all.sh` — run **both**: 82 skill + 53 GenKit.
5. `deploy_to_canon.sh` → canon → `~/.claude/skills` symlink.

## Do not

- Do not change the `// EXPECTED_*` format — it is the GenKit contract.
- Do not put geometric limits into the JSON schema (they belong in `assert`).
- Do not add `custom()` support to the generator — it deliberately returns `unsupported_kind`.

## Knowledge from the skill worth reusing

- `check_rules.py` already has a `COVER` line ("N rules exercised, M whose antecedent never fired") —
  a good precedent for the S-2 gate.
- `validation_log.jsonl` (8 685 rows) holds the full history; before changing semantics, check how
  many runs had SKIP.
- `templates/joints.json` ships a `"touching" 0–0` example that triggered the S-6 bug — fix the
  template too.
