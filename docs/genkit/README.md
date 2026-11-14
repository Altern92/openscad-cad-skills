> **Moved 2026-11-14.** GenKit is now a permanent part of this repo: `scad-modeler/kit/`, `scad-modeler/gen/` (examples in `gen/examples/`), `scad-modeler/tests/genkit/`, and these docs. The former standalone copy on the owner's SSD is no longer a source and nothing syncs from it (INC-2026-11-13-09). Paths like `/Volumes/.../OpenSCAD_GenKit` and `make deploy` in these docs are history; run `bash scad-modeler/tests/run_all.sh` (includes the GenKit suite).

# OpenSCAD GenKit

Parametric "one-shot" part generator: the user says once what they want → the system collects
parameters → it emits a `.scad` **with declarations** → deterministic gates prove the model is
correct.

**Status: P0–P8 complete (2026-11-02).** Contract approved (AC-01); `gen/schema.json` +
`gen/validate_schema.py` + 13 JSON examples work; the gates were re-baselined after the
2026-11-01 13:16–13:38 rewrite (P0b). 8 kit modules + composite `box_with_lid` + `gen/emit_part.py`
work: 12 fixtures → gates `0 failed, 0 inconclusive`. `bash tests/run_all.sh` → **59 passed, 0 failed** (~45 s).
P5 (10 real briefs): **8/10 (80 %)** one-shot, 0 false "done", 2 honest refusals
(`docs/08`, ADR-006 in `docs/02`).

Runtime error messages are in **English** (since 2026-11-14; Lithuanian before); docs and code comments are
in English.

## Why

The 2026-11-01 audit found that `scad-modeler` has ~20 working gates (21 after the same-day
rewrite; `docs/10` §7), but:

- the most expensive gates (`dimensions`, `topology`) ran only if the `.scad` carried a
  declaration comment → otherwise `SKIP` and "All validations passed" (after 2026-11-01:
  declarations are **mandatory**, `declarations=FAIL` without them);
- a gear 62 % too thin passed the whole chain (`check_rules.py` exit 0);
- `INCONCLUSIVE` did not fail the run (after 2026-11-01: **exit 2**, `NOT VERIFIED`);
- ~19 separate Python processes cost 1.2–1.5 s out of 5.8 s.

The goal is not "more gates". It is **fewer degrees of freedom for the model to get wrong** and
**declarations derived from the same parameters**, instead of asking the model to remember them.

## How it works (3 layers)

```
requirements.json  →  generator (Python)  →  parts/part.scad (+ // EXPECTED_*)
                             ↓
                   validate_scad.sh --all  →  PASS / FAIL / SKIP (with declaration coverage)
```

1. **Kit** (`kit/*.scad`) — 8 OpenSCAD modules that compute the geometry themselves and
   `assert()` impossible parameters.
2. **Generator** (`gen/emit_part.py`) — reads `requirements.json`, writes the `.scad` **and the
   declarations** from the same numbers.
3. **Gates** (already in the skill) — check the result; declarations are no longer opt-in because
   the generator writes them.

---

# Deployment into `scad-modeler`

The kit is designed to live **inside** the `scad-modeler` skill: the `// EXPECTED_*` contract is
defined there, and one skill keeps one test suite.

## Step 0 — Preconditions

```bash
openscad --version                      # 2026.x
ls ~/Documents/OpenSCAD/libraries/BOSL2/std.scad
ls ~/Github/Claude_Code_SCAD_Skill/claude_skills/scad-modeler/scripts/validate_scad.sh
```

If any is missing, stop — the kit cannot be verified.

## Step 1 — Copy the payload

| From (this repo) | To (skill dev repo) |
|---|---|
| `kit/*.scad` | `claude_skills/scad-modeler/kit/` |
| `gen/emit_part.py`, `gen/schema.json`, `gen/validate_schema.py` | `claude_skills/scad-modeler/gen/` |
| `tests/` (fixtures, mutants, expected, run_all.sh, p5) | `claude_skills/scad-modeler/tests/genkit/` |

```bash
SKILL=~/Github/Claude_Code_SCAD_Skill/claude_skills/scad-modeler
mkdir -p "$SKILL/kit" "$SKILL/gen" "$SKILL/tests/genkit"
cp kit/*.scad "$SKILL/kit/"
cp gen/*.py gen/schema.json "$SKILL/gen/"
cp -R tests/. "$SKILL/tests/genkit/"
```

**Do not** copy `docs/`, `examples/`, `NEXT.md`, `HANDOFF.md` — they stay in this project.

## Step 2 — Fix include paths

`gen/emit_part.py` writes `include <$KIT/...>` where `$KIT` defaults to `<script_dir>/../kit`.
After the copy that resolves to `scad-modeler/kit/` — correct. Verify:

```bash
python3 "$SKILL/gen/emit_part.py" "$SKILL/tests/genkit/fixtures/box.json" -o /tmp/box.scad
grep '^include' /tmp/box.scad
# include </.../scad-modeler/kit/lib.scad>
```

If the paths still point at the old project location, pass `--kit-root "$SKILL/kit"` or change
`DEFAULT_KIT`.

## Step 3 — Add the `SKILL.md` section

Append to `scad-modeler/SKILL.md` (before the reference-files list):

```markdown
## Generator (parametric parts)

If the request fits one of the 8 shapes (plate, plate_with_holes, bracket_l, box, lid,
boss, hole_pattern, snap_hook), do not hand-write the `.scad`. Write `requirements.json`
and run:

    python3 gen/emit_part.py requirements.json -o parts/<part>.scad

The generator writes `// EXPECTED_*` declarations from the same parameters. Schema:
`gen/schema.json`. If `kind` does not fit, use `custom` (hand-written, declarations
required).

Working example of each kind: `tests/genkit/fixtures/`.
```

## Step 4 — Wire the tests

Append to `scad-modeler/tests/run_all.sh`, before the summary block:

```bash
# GenKit suite (53 tests)
if [ -x "$SKILL_DIR/tests/genkit/run_all.sh" ]; then
    bash "$SKILL_DIR/tests/genkit/run_all.sh" || fail=$((fail+1))
fi
```

Use the `$SKILL_DIR` variable the script already defines.

## Step 5 — Verify

```bash
# 1. schema
python3 "$SKILL/gen/validate_schema.py" "$SKILL/tests/genkit/fixtures/"*.json | tail -1
# expect: 8/8 OK

# 2. GenKit suite
bash "$SKILL/tests/genkit/run_all.sh" | tail -3
# expect: 53 passed, 0 failed

# 3. skill regression (must stay green)
bash "$SKILL/tests/run_all.sh" | tail -2
# expect: 82 passed, 0 failed

# 4. end-to-end on a generated part
python3 "$SKILL/gen/emit_part.py" examples/bracket_80x50.json -o /tmp/b.scad
bash "$SKILL/scripts/validate_scad.sh" /tmp/b.scad | grep -E 'dimensions|features|declarations'
# expect: dimensions=PASS, features=PASS, declarations=PASS
```

## Step 6 — Deploy to canon

```bash
cd ~/Skills-plugins-etc
bash scripts/deploy_to_canon.sh        # or the rsync flow documented in SKILLS-CANON.md
```

Then confirm from the installed symlink:

```bash
ls ~/.claude/skills/scad-modeler/kit/  # 9 .scad files
```

## Rollback

```bash
SKILL=~/Github/Claude_Code_SCAD_Skill/claude_skills/scad-modeler
rm -rf "$SKILL/kit" "$SKILL/gen" "$SKILL/tests/genkit"
```

Remove the `## Generator` section from `SKILL.md` and the GenKit block from
`tests/run_all.sh`. Nothing else was modified.

## Deployment checklist

- [x] Step 1 files copied (`scripts/deploy_genkit.sh`)
- [x] Step 2 includes resolve to the skill's `kit/`
- [x] Step 3 `SKILL.md` section added
- [x] Step 4 test block wired
- [x] Step 5 all four verifications pass (12/12 schema, 59 GenKit, 84 skill + 1 GenKit suite, PASS×3)
- [x] Step 6 canon deployed and symlink verified (`scripts/deploy_to_canon.sh`)

---

## Layout

| Path | Contents |
|---|---|
| `kit/` | 8 parametric modules + `lib.scad` (hole table, helpers, tolerances) |
| `gen/emit_part.py` | `requirements.json` → `.scad` + `// EXPECTED_*` (incl. `EXPECTED_BBOX_TOL` & `box_with_lid`) |
| `gen/schema.json` | JSON Schema for `requirements.json` (types/structure only) |
| `gen/validate_schema.py` | standalone schema validator (re-execs into the venv if needed) |
| `tests/fixtures/` | 12 good inputs |
| `tests/mutants/` | 43 bad inputs — one per `assert` |
| `tests/expected/` | expected error text per mutant |
| `tests/run_all.sh` | 59 tests: 12 golden, 43 mutants, 2 assemblies (`box+lid`, `box_with_lid`), 2 gate-mutants |
| `tests/geom_mutation.py` | periodic geometric mutation test (136 mutants; baseline in `geom_mutation_baseline.tsv`) |
| `tests/p5/` | P5 runner + brief sets |

## Documentation

| File | Contents |
|---|---|
| `HANDOFF.md` | **Start here** — boundaries, environment, commands, hard-won facts |
| `AGENTS.md` | mandatory rules for any agent working here |
| `NEXT.md` | work queue P0–P7 |
| `docs/01_goal_and_context.md` | problem, goal, metrics, scope |
| `docs/02_architecture.md` | layers, data flow, ADR-001…006 |
| `docs/03_module_api.md` | module signatures, asserts, declarations, JSON schema |
| `docs/04_acceptance_criteria.md` | AC-01…AC-40 with commands |
| `docs/05_tests_and_errors.md` | error format, fixtures, mutants, harness |
| `docs/06_risks_and_gates.md` | risks R1–R7, decision gates V1–V4 |
| `docs/07_agent_workflow.md` | how an agent works here (DoD, report format) |
| `docs/08_p5_measurement.md` | P5 protocol and results |
| `docs/09_skill_integration.md` | what the skill must change (S-1…S-6) |
| `docs/10_audit_findings.md` | measured gate behaviour, repro commands |
| `docs/11_p5_briefs.md` | the 10 briefs used for P5 |
| `docs/12_handoff_claude.md` | handoff to the `scad-modeler` owner |
| `docs/13_audit_2026-11-01.md` | post-implementation audit (F1–F6) |

## Quick start

```bash
cd OpenSCAD_GenKit
make part JSON=examples/bracket_80x50.json OUT=out/bracket.scad
python3 gen/validate_schema.py tests/fixtures/*.json      # 8/8 OK
bash tests/run_all.sh                                     # 53 passed
```

## Related

- Audit note (vault): `~/Desktop/Obsidian/Personal/Research/Runs/2026/2026-11-01-openscad-skill-auditas.md`
- Skill (dev): `~/Github/Claude_Code_SCAD_Skill/claude_skills/scad-modeler/`
- Skill (canon): `~/Skills-plugins-etc/skills/scad-modeler/`
- Deploy procedure: `~/Skills-plugins-etc/SKILLS-CANON.md`
