# 02 — Architecture

## Layers

```
┌──────────────────────────────────────────────────────────┐
│ 1. Intake (agent)                                        │
│    brief → 3–5 questions → requirements.json             │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 2. Generator  gen/emit_part.py  (Python 3)               │
│    requirements.json → parts/<name>.scad                 │
│    + // EXPECTED_* derived from the same numbers         │
│    + missing parameters → exit 4, no file written        │
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 3. Kit  kit/*.scad  (OpenSCAD + BOSL2)                   │
│    modules compute the geometry, assert() impossible input│
└───────────────────────────┬──────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Gates  validate_scad.sh --all  (already in the skill) │
│    ~20 checks; declarations are now generator-written    │
└──────────────────────────────────────────────────────────┘
```

## Why three layers, not one

| Decision | Alternative | Why |
|---|---|---|
| Kit in **OpenSCAD** | A Python/Rust library that emits SCAD | OpenSCAD only compiles `.scad`; BOSL2 is already there; the model already writes this language |
| Generator in **Python** | Rust | `jsonschema` is already in the venv; one process (no interpreter drift); the agent writes Python more reliably |
| Declarations from the generator | Model writes the comments | Otherwise they become "discipline" again (audit F1) |
| Gates unchanged | New validator | 20 gates already work; changing their semantics is a separate job (P4′) |

## File layout

```
OpenSCAD_GenKit/
├── AGENTS.md
├── HANDOFF.md
├── NEXT.md
├── README.md              ← what it is + deployment
├── docs/                  ← this documentation
├── kit/                   ← OpenSCAD modules
│   ├── lib.scad           ← hole table, tolerances, helpers
│   ├── plate.scad
│   ├── plate_with_holes.scad
│   ├── bracket_l.scad
│   ├── box.scad
│   ├── lid.scad
│   ├── boss.scad
│   ├── hole_pattern.scad
│   └── snap_hook.scad
├── gen/
│   ├── emit_part.py
│   ├── validate_schema.py
│   └── schema.json
├── examples/
│   └── bracket_80x50.json
└── tests/
    ├── fixtures/          ← 11 good JSON files
    ├── mutants/           ← 40 bad JSON files (one per assert)
    ├── expected/          ← expected error text per mutant
    ├── p5/                ← P5 runner + brief sets
    └── run_all.sh
```

## Data flow

1. `requirements.json` (schema: `03_module_api.md` §Schema) carries `kind` (module name) and `params`.
2. The generator validates the schema; missing parameters come back as a list (exit 4), never guessed.
3. The generator computes the bbox with the same formula as the module and writes `// EXPECTED_BBOX`.
4. The `.scad` contains `include <kit/lib.scad>` + the module include + one `kit_<name>(...)` call.
5. Gates: `validate_scad.sh --all` → `CHECK_RESULT` + `COVERAGE`.

## Decisions (ADR)

### ADR-001: Python generator, not Rust

**Context:** Rust would buy ~30 % wall time and a single binary; the audit showed Python startup is
1.2–1.5 s out of 5.8 s.
**Decision:** Python.
**Reasons:** (a) the generator is one process, not 20 — startup cost is irrelevant; (b) `jsonschema`
is already present; (c) the agent writes Python more reliably; (d) Rust can be added later as a CLI
without changing the API.
**Consequences:** a venv dependency — handled by `resolve_python.sh` at every entry point.

### ADR-002: JSON parameters, not SQLite

**Decision:** `requirements.json` is the only parameter source.
**Reasons:** git diff, model readability, folder = state, schema validation already exists.
**Consequences:** history stays in JSONL; SQLite is only acceptable as a derived read-model.

### ADR-003: Kit before a host builder

**Decision:** v0 is SCAD modules with `assert`, not a typed Python/Rust builder.
**Reasons:** cheapest (2–3 days), plugs into the existing pipeline, the model already writes SCAD.
**Consequences:** if P5 shows the model picks the wrong modules, then a host builder (separate ADR).

### ADR-004: No home-grown CAD kernel

**Decision:** geometry is OpenSCAD + Manifold; no boolean/B-rep implementation.
**Reasons:** years of work, and it already exists and works.

### ADR-005: Gate semantics are a separate job

**Decision:** `validate_scad.sh` and `check_*.py` are not modified during P1–P3. P4′ may only change
verdict semantics and declaration coverage, with its own AC and tests.

### ADR-006: P5 result — continue with 8 modules (2026-11-01)

**Context:** 10 real briefs, first round: 7/10 generated and passed the gates correctly; 3 honest
refusals (composite request, gear, hinge); 0 cases of "PASS but wrong geometry" **after** the
`bracket_l` fix (before it there was 1 — both holes horizontal instead of one per leg).

**Decision:** **continue** with the current 8 modules + `lid` hole parameter; **do not** expand into
free-form geometry (`custom()` stays an honest refusal with a BOSL2 pointer); **host builder** — not
needed for now (the errors were in module geometry, not in module selection); **Rust** — not ruled
out, but not now (ADR-001).

**Consequences:** P6 candidates — `lid` hole variant (done), box screw holes (open), composite
request decomposition (intake work, S-4).

## Independence

The project must work without the `scad-modeler` skill (OpenSCAD + BOSL2 only), so it can be tested
in isolation. Gates are part of *integration*, not a precondition.
