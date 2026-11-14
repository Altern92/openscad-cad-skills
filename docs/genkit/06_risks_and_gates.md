# 06 — Risks and decision gates

## Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | 8 modules do not cover real briefs | medium | one-shot rate drops | `custom()` escape hatch + P5 measurement; expand only on data |
| R2 | `assert` limits too strict → false FAIL | medium | user gets an error on a good part | limits from the printer profile (ADR), not a constant; review against 3 real cases |
| R3 | Model picks the wrong module | medium | wrong geometry | 3 few-shot examples in the system prompt; `kind` is a required field |
| R4 | Python bbox formula disagrees with SCAD | medium | false `dimensions=FAIL` | `check_dimensions.py` is the oracle; AC-29 checks it for every module |
| R5 | Over-engineering (new modules before data) | high | time wasted | P5 gate; a new module only from a real brief |
| R6 | OpenSCAD version drift (Manifold) | low | bbox/topology differ | pin the version; AC-19 runs every time |
| R7 | Gate-semantics change (P4′) breaks existing tests | medium | skill regression | only with its own AC and after `scad-modeler/tests/run_all.sh` (82 tests) |

## Decision gates

### V1 — after P1 (kit v0)

**Question:** do the 8 modules cover 3 real briefs written by hand?

- **3/3** → continue to P2.
- **2/3** → review the module list before P2 (cheap now, expensive later).
- **≤ 1/3** → stop; the problem is module selection, not implementation.

### V2 — after P3 (generator)

**Question:** does the generated `.scad` pass the gates without manual edits?

- **11/11** → P4′.
- **< 11/11** → fix the generator; **never** weaken an `assert`.

### V3 — after P5 (measurement)

**Question:** what is the one-shot rate?

| Result | Decision |
|---|---|
| ≥ 70 %, 0 false "done" | continue: expand the module list from the failures |
| 50–70 % | fix intake (questions), not modules |
| < 50 % | stop and redesign: host builder (ADR-006) or a narrower scope |
| > 0 false "done" | **block release** — fix verdict semantics first, then re-measure |

### V4 — after P5, if the rate is good

**Question:** is the remaining pain execution (speed/distribution)?

- Yes → consider a Rust CLI (not a rewrite): `manifold-csg` + `parry3d`, 2–3 weeks, separate ADR.
- No → Rust is irrelevant; invest in modules.

## When blocked

1. Write `BLOCKED: <reason>` next to the item in `NEXT.md`.
2. Do not take another item (the queue is the queue).
3. If the blocker is environmental (OpenSCAD, BOSL2), give the exact command that restores it.
4. If the blocker is an unclear AC, ask the user **one** question with a proposal.
