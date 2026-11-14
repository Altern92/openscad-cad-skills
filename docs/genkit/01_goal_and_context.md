# 01 — Goal and context

## Problem

An LLM writes OpenSCAD code that almost always **compiles**, but is often **geometrically wrong**:
a hole in mid-air, a blind bore, a 40 mm overlap between parts, a part 62 % thinner than asked.
OpenSCAD has no topology, so none of these produce an error message.

`scad-modeler` has ~20 gates (21 after the 2026-11-01 13:16–13:38 rewrite) that would catch them —
but the 2026-11-01 audit showed they **did not run** when needed:

| Fact | Number |
|---|---|
| Gates that ran only with a hand-written declaration (`EXPECTED_BBOX`, `EXPECTED_THROUGH_HOLES`) | the 2 most expensive (after 2026-11-01: **mandatory** via the `declarations` gate) |
| A gear 62 % too thin | passed 20 gates, `check_rules.py` exit 0 |
| `INCONCLUSIVE` runs | ended exit 0, "All validations passed" (after 2026-11-01: **exit 2**) |
| Python process startup share | 1.2–1.5 s out of 5.8 s |
| Canonical example without `EXPECTED_BBOX` | `dimensions=SKIP` |

The cause is not missing libraries: `trimesh`, `python-fcl`, `manifold3d` work. The cause is that
**the model has too many degrees of freedom** (it writes coordinates) and **the declarations are
its responsibility**, not the system's.

## Goal

> The user says once what they want. The system collects the missing parameters, generates the
> model, and **proves** it is correct — with no second round and no human looking at a picture.

Success is not "the code compiled", it is:

| Metric | Target | How it is measured |
|---|---|---|
| One-shot success | ≥ 70 % | 10 real briefs (P5), no second round |
| Silent false "done" | **0** | no FAIL may end as PASS |
| Declaration coverage | 100 % | every printed part has `EXPECTED_BBOX` or `// NO_BBOX:` |
| Time to verdict | ≤ 6 s for a small model | `validate_scad.sh --all` |

## Scope

**In:** plates, brackets, boxes, lids, bosses, hole patterns, snap hooks. That is ~80 % of real
briefs.

**Out:** new mechanisms (gear trains, hinges, multi-part assemblies with motion). One-shot success
is not reachable there — published data shows 5-operation tasks dropping to 3–30 %.

**Deliberately out:** a Rust rewrite, SQLite for parameters, a home-grown CAD kernel (see
`02_architecture.md` §Decisions).

## Context

- Audit note: `~/Desktop/Obsidian/Personal/Research/Runs/2026/2026-11-01-openscad-skill-auditas.md`
- Skill: `~/Github/Claude_Code_SCAD_Skill/claude_skills/scad-modeler/`
- Gates: `scripts/validate_scad.sh` (20 gates, 4.8 s), `tests/run_all.sh` (65 tests at audit time)
- Environment: OpenSCAD 2026.10.11 (`~/.local/bin/openscad`), venv `~/.local/share/scad-modeler/venv`,
  BOSL2 `~/Documents/OpenSCAD/libraries/BOSL2`

## What counts as "a correct model"

1. All gates PASS (not SKIP, not INCONCLUSIVE).
2. Declarations match `requirements.json` (bbox, through-hole count).
3. Generation is deterministic: the same JSON → the same `.scad`, byte for byte.
4. No hand-written coordinates outside a module (`grep`-checked, manual review).
