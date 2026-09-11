<!-- RAG-passport: file=references/retrieval.md | skill=all (openscad-cad+scad-modeler+openscad-organic) | applies_to=[which-skill, routing, passport-format, abstention] | version=2026-09-11 | source=06_RAG_taisykles (T2/T3/T4) -->
# Retrieval — which skill and which reference, before anything else

Pointer file, not a copy. Every rule below lives in its own file; this file only routes. (RAG T3 — thin entry, details behind triggers.)

## Which skill to load

| You have | Load | Why |
|---|---|---|
| Single part (insert, bracket, cover, Gridfinity bin) | `openscad-cad` | Core workflow: write → render → look → fix → export |
| 2+ interacting parts (gears, bearings, fits) | `scad-modeler` + `openscad-cad` | Gated planning, calculations before geometry, validation cycle |
| Figurine / organic shape | `openscad-organic` + `openscad-cad` (+ `scad-modeler` if articulated) | hull/skin/sweep + FDM detail minimums |
| Unsure / vague brief | `scad-modeler` intake (`references/intake_and_analysis.md`) | Brief → requirements before geometry |

## Passport format (every reference chunk carries one)

```
file=<path> | section=<section> | skill=<skill> | applies_to=[a, b] | units=<units> | version=<date> | source=<origin>
```

`.scad` chunks additionally: `pattern=<name> | depends_on=<pattern|none>`. See `../openscad-cad/references/patterns.scad` P0–P5 for the example.

## Abstention (precision over recall)

Top match weak, units/printer differ, or fit intent unstated → ask once, don't guess. Full rule: `../openscad-cad/references/confidence-tiers.md` (Abstention rule + Tier 1–5).

## Small-archive policy

Past-project archive (~12) is read directly (README + top variable block), not embedded — vector search doesn't earn its cost at this size. See `../scad-modeler/references/intake_and_analysis.md` §3.
