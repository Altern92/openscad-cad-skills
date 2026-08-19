# Intake & Analysis Stage

> **When to apply**: the very start of any new design — before §0.5 Planning.
> Turns the user's (often messy) brief — plus whatever information they
> gathered from other AIs — into a machine-checkable requirement spec, classifies
> every component as **printed vs purchased**, and proposes **2–3 similar past
> variants** to adapt instead of designing from zero.

## 1. Requirements spec (JSON) — extracted from the brief

The skill writes `design_manifest.json` (or `requirements.json` for non-moving
designs) during intake. This is the single structured output of the intake
stage; everything downstream (planning §0.5, params.scad §2, checks §7) reads
from it. Schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OpenSCADDesignSpec",
  "type": "object",
  "required": ["goal", "envelope", "interfaces", "motion", "parameters", "dependencies"],
  "properties": {
    "goal": { "type": "string", "description": "Primary functional objective" },
    "envelope": {
      "type": "object",
      "properties": {
        "max_bounds_xyz_mm": { "type": "array", "items": { "type": "number" }, "minItems": 3, "maxItems": 3 },
        "is_strict": { "type": "boolean" }
      },
      "required": ["max_bounds_xyz_mm", "is_strict"]
    },
    "parameters": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "value", "unit", "status"],
        "properties": {
          "name": { "type": "string" },
          "value": { "type": "number" },
          "unit": { "type": "string", "enum": ["mm", "deg", "rpm", "N"] },
          "status": { "type": "string", "enum": ["confirmed", "estimated", "unknown"] },
          "tolerance_mm": { "type": "number" }
        }
      }
    },
    "interfaces": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["mate_type", "mating_part", "clearance_mm"],
        "properties": {
          "mate_type": { "type": "string", "enum": ["bore", "boss", "slot", "fastener_clearance", "thread_insert"] },
          "mating_part": { "type": "string" },
          "clearance_mm": { "type": "number" }
        }
      }
    },
    "motion": {
      "type": "object",
      "properties": {
        "has_kinematics": { "type": "boolean" },
        "dof_type": { "type": "string", "enum": ["none", "rotational", "linear", "planar", "gear_mesh"] },
        "range": { "type": "array", "items": { "type": "number" } },
        "continuous": { "type": "boolean" }
      },
      "required": ["has_kinematics"]
    },
    "dependencies": {
      "type": "object",
      "description": "DAG map: parameter -> list of dependent submodules/calculators to recompute",
      "additionalProperties": { "type": "array", "items": { "type": "string" } }
    }
  }
}
```

**Status discipline** (this is a rule the skill must enforce — it is the
single biggest source of wrong designs): every number from the user's brief or
from another AI is tagged `confirmed` | `estimated` | `unknown`. `unknown`
values must be asked back or measured — never invented. `estimated` values go
into `params.scad` as named variables and into the §8 final report as "still
estimated". Do not silently promote an estimate to a fact during modeling.

**Always ask back** (before modeling, if any of these are missing):
1. Goal in one sentence + what it must NOT do.
2. Which dimensions are hard (must fit an existing part/space) vs soft.
3. Does anything move? How (motor, hand, spring)? Speed/load if known.
4. Which parts already exist / are purchased (bearings, shafts, fasteners…)?
5. Print constraints: printer size, material, orientation preference.

## 2. Printed vs purchased classification

Philosophy: standard high-precision hardware is a **vitamin** (NopSCADlib term)
— an off-the-shelf part modelled with its real catalogue dimensions (envelope
+ cutouts), never printed. The skill positions the vitamin, not a fake
cylinder ([NopSCADlib vitamins](https://github.com/nophead/NopSCADlib),
[DeepWiki](https://deepwiki.com/nophead/NopSCADlib/4-component-library-(vitamins))).

| Kriterijus | Spausdinti (`.scad` modulis) | Pirkti / vitaminas (NopSCADlib) | Sprendimo riba |
|---|---|---|---|
| **Apkrova** | Statiniai korpusai, žemo sukimo momento laikikliai | Ašys, velenai, konstrukcinės tvirtinimo detalės | Jei šlytis/tempimas rizikuoja sluoksnių atsisluoksniavimu → plienas |
| **Tikslumas** | ISO ≥ IT11 (tarpas ≥ 0.2mm) | Guolių kakliukai, velenai (ISO h6/h7/g6) | Jei tolerancija < 0.1mm → vitaminas + spausdinta kišenė |
| **Trintis / greitis** | Įvorės žemais sūkiais (<60 rpm), slankikliai | Rutuliniai guoliai (608, 625), žalvario įvorės | Nuolatinis sukimasis arba μ < 0.15 → rutulinis guolis |
| **Kaina / įsigijimas** | Individuali geometrija, vienetiniai | M3/M4 varžtai, šiluminiai įdėklai, GT2 skriemuliai/diržai | Jei standartinė detalė kainuoja < ~1€ → vitaminas |
| **Įgyvendinamumas** | Savaiminės atramos ≤45°, tiltai <15mm | Lygūs strypai, sraigtai, spyruoklės | Vidiniai spiraliniai keliai / nespaudinami iškyšos → pirkta |

**Output of this stage**: a `purchased_components` array in
`design_manifest.json` (name, qty, key dims — see
`mechanics_and_motion_planning.md` §3.1), and one `@purchased` marker on every
parameter that describes a purchased part's dimension (so the change-propagation
tree knows a purchased-dimension change triggers fit checks, not geometry
re-renders).

## 3. Similar-variant retrieval (find 2–3 past designs to adapt)

Goal: never start from zero when a past design (or parametric template) covers
half the problem. Two mechanisms:

**A. Direct read-through, not an embedding index.** An earlier version of this
section specified a DashScope embedding index (vector search over past
projects). Reconsidered 2026-08-19: the actual archive is a personal collection
of a dozen or so past `.scad` projects, not a corpus at a scale where vector
search earns its cost. At this size, reading every past project's `README.md`
(plus the entry-point `.scad` file's top variable block if the README alone
doesn't answer it) directly and judging similarity is both simpler — no
external API, no vector store, no embedding pipeline to build and maintain —
and likely *better*, since judging "is this gearbox similar" benefits from
understanding module/tooth-count/motion-type context, not just text
similarity. Do this:

1. List past project directories (e.g. everywhere else under
   `3D_Spausdinimas/`, excluding the skill's own repo).
2. Read each candidate's `README.md`; for a closer look at the ones that seem
   plausible, read the entry-point `.scad` file's parameter block too.
3. Judge similarity on the same axes an embedding rerank would have used
   anyway — vitamins/hardware used, motion type, envelope size, category —
   and surface 2–3 candidates worth adapting from.

Revisit this if the archive grows into the hundreds of projects, where
reading every candidate stops being practical — until then, an embedding
index is infrastructure without a problem to solve. (DashScope access itself
is still real and working, see `04_Kita/DashScope_Qwen_kreditu_naudojimas/`
— just not needed for this.)

**B. Parametric templates**: the Gridfinity tables
(`openscad-cad/references/gridfinity-params.md`) and the reusable patterns
(`openscad-cad/references/patterns.scad`) are themselves a variant source —
when the brief matches a known pattern (bin, bracket, sleeve, pocket), the
template IS the "similar variant" and the skill adapts its parameters instead
of writing fresh geometry.

**When retrieval must be skipped**: a brief that explicitly demands a novel
mechanism or unproven geometry — then say so in the plan (§0.5) and do not
pretend a variant exists.

---

## Šaltinių žurnalas

| ID | Teiginys | Šaltinis (URL) | Tipas | Data | Būsena |
|---|---|---|---|---|---|
| I-001 | Vitaminų filosofija: standartinės detalės modeliuojamos realiais matmenimis, BOM generuojama | https://github.com/nophead/NopSCADlib ; https://deepwiki.com/nophead/NopSCADlib/4-component-library-(vitamins) | pirminis | 2026-08-19 | su šaltiniu |
| I-002 | FDM tarpų klasės (press/slip/transition) — sprendimo kriterijai | https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/ | pirminis | 2026-08-19 | su šaltiniu |
| I-003 | Judančių spausdintų dalių apribojimai (trintis, nusidėvėjimas) | https://thevirtualfoundry.com/3d-print-moving-parts/ | pirminis | 2026-08-19 | su šaltiniu |
| I-004 | ~~Embedding modelio naudojimas paieškai — DashScope qwen3.7-text-embedding~~ NEBENAUDOJAMA 2026-08-19: §3 pakeista tiesioginiu README skaitymu, žr. aukščiau kodėl | https://help.aliyun.com/zh/model-studio/model-pricing.md | pirminis | 2026-08-19 | pakeista |
