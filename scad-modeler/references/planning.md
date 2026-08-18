# Planning — before the calculation table

## Why this exists

Real incident (`../INCIDENTS.md`, 2026-08-18): a rear-axle gearbox project had
detailed gear-ratio and center-distance numbers calculated and locked into
`params.scad` before the actual mechanical architecture (which reduction
scheme, which parts mesh with which) was genuinely settled — prior documents
disagreed on the architecture and on a key gear module value. The calculation
work proceeded anyway. Later, `check_collisions.py` found real, undocumented
interference across nearly every part pair, traceable back to a center
distance that had been fixed before checking whether it left room for two
housings' full wall thickness. The fix cost more than it would have if the
architecture question had been forced closed first.

## The rule: architecture before numbers

Don't write a single formula in the calculation table (§1) until the
mechanical concept is settled and every part's rough role and dependency
order is sketched. This is directionally supported across engineering design
literature (Pahl & Beitz's four-phase model puts conceptual design before
embodiment/detail design; VDI 2221/2223 the same) — late architecture changes
cost more than early ones, consistently, across sources.

**One citation to get right, not wrong**: the specific "1x / 10x / 100x /
1000x by phase" cost-of-change curve people often quote is **Barry Boehm's
1981 software-engineering data** (TRW/IBM/GTE/Bell Labs projects), not a
mechanical-design measurement. Cite it, if at all, as "the same directional
effect shows up in software cost data too" — not as if it were derived from
CAD or mechanical assemblies. Mechanical/hardware change-cost literature
supports the direction (late changes cost more) but not a clean universal
multiplier. Getting this citation wrong is exactly the kind of thing
`INCIDENTS.md` exists to catch — don't repeat the error by copying the neat
1/10/100 chart into mechanical design contexts as if it were proven there.

There's also direct AI-agent-specific support: gating an agent's editing
until it has collected enough evidence before committing — i.e. exactly
"don't detail before the concept is settled" — measurably improved coding-
agent Pass@1 by 4.8–11.8 points in one 2026 study. CAD-specific benchmarks
(BenchCAD, Text2CAD-Bench) don't yet have a dedicated metric for "committed
to architecture too early," but they do document a related pattern: LLM CAD
generators often lock onto an oversimplified construction path (plain
sketch-extrude) instead of the operation the geometry actually needs
(sweep/loft/twist-extrude) — a same-shape failure of settling too fast on
the first workable-looking approach.

## Workflow

Four steps, in order. Each produces a small artifact that later steps (and
§1's calculation table) can reference — none of this is thrown away.

### 1. Decisions/assumptions log — start this first, before anything else

Six fields, one row per fact/assumption/decision/risk/question that the
design depends on:

| ID | Type | Criticality | Statement | Status | Evidence |
|---|---|---|---|---|---|
| F1 | Fact | Ordinary | Motor shaft is 3.175mm | Confirmed | Datasheet |
| A1 | Assumption | Critical | Diff ring gear module is 1.0mm | Unverified | Estimated from a product photo, OD/tooth-count formula |
| D1 | Decision | Ordinary | Two-stage jackshaft reduction, not single-stage | Confirmed | User chose this over direct-mesh option (see §2 below) |
| R1 | Risk | Critical | CD2 may be too small for both housings' full wall thickness | Open | Needs check once both housings are sized |
| Q1 | Question | Ordinary | Which side do motor leads exit? | Open | Ask user or guess + flag |

Types: **Fact** (confirmed, cite the source), **Assumption** (used for now,
not confirmed — this is what becomes a `PATIKRINTI` marker once it reaches
the calculation table in §1), **Decision** (a choice made, with why),
**Risk** (something that can break the design if unaddressed), **Question**
(needs resolving, from the user or by looking something up).

**Criticality** — mark **Critical** anything that feeds a load-bearing,
strength, or fit-critical calculation (a gear module, a stress-relevant
dimension, a bearing rating) — not just anything uncertain. Everything else
is **Ordinary**. This distinction exists because "wrong or unverified initial
design assumptions" is, by a wide margin, the most evidence-backed root
cause of real mechanical failures across multiple large failure-analysis
studies (2026-08-19 Perplexity research: ~79% of a 284-case chemical-process
accident study involved a design error; design error outranked component
failure as a root cause, 35% vs 18%, in a nuclear-industry dataset) — an
*Ordinary* unresolved assumption is a normal, acceptable work-in-progress
state; a *Critical* one left unresolved is exactly the failure mode those
studies describe. `scripts/check_assumptions.py` enforces this: a `Critical`
row whose `Status` isn't `Confirmed`/`Verified`/`Resolved` fails validation
(§7) once this table exists — it's the same idea as DFMEA "critical/special
characteristics" and a project assumptions register, adapted to a solo
agent's calculation table rather than a full quality-management template.

This log is the *source* for the calculation table's `PATIKRINTI` markers —
not a separate parallel system. An `Assumption` row that's still
`Unverified` when you reach §1 becomes a `PATIKRINTI` row there.

### 2. If more than one architecture is viable, or prior docs disagree: a lightweight Pugh comparison

Don't silently pick one, and don't calculate numbers for more than one. Pick
the most plausible option as the **datum**, score 1-3 alternatives against
it on 3-5 criteria as `+` / `0` / `-`:

| Criterion | Datum (e.g. direct mesh) | Alt A (e.g. jackshaft 2-stage) |
|---|---:|---:|
| Ground clearance | 0 | + |
| Parts count | 0 | - |
| Backlash risk | 0 | + |
| Manufacturability | 0 | 0 |
| **Uncertainty/risk** | 0 | - |

Always include the **uncertainty/risk row** — otherwise a vague,
under-specified concept can look artificially good just because it hasn't
been thought through enough to reveal its problems yet. If the result is
close or genuinely unclear, this is a `Question` for the user (§0/log above),
not something to resolve by guessing or by calculating both.

### 3. Parts list + minimal dependency order

List every part with one line each, then a tiny dependency matrix — for
3-6 parts this takes under 10 minutes and catches real ordering mistakes:

| Part | A | B | C | Notes |
|---|---:|---:|---:|---|
| A (motor mount) | – | X | | A needs B's shaft diameter |
| B (jackshaft housing) | | – | ? | maybe depends on C's bearing seat |
| C (diff carrier) | | | – | independent — design this first |

`X` = hard dependency (this part's geometry needs that part's number first).
`?` = uncertain — that uncertainty is itself worth a `Question` row in the
log above, not a silent guess. A part with many incoming `X`s (i.e. many
`?`s wanting to be `X`s) should be designed *later*; an independent part with
no dependencies should usually go first. For 2-3 parts, skip the matrix and
just write two lists: **must know first** / **can wait**.

### 4. Now do §1's calculation table

Every `Assumption` still unresolved becomes a `PATIKRINTI` row. Every
`Decision` from step 2 becomes the fixed premise the formulas are built on —
don't let a formula quietly re-open an architecture question that step 2
already closed.

## What this is not

Not a full industrial DSM (no clustering algorithms), not a weighted Pugh
matrix, not an enterprise RAID log. Each artifact above is the smallest
version that still catches the failure mode it's aimed at, for a solo agent
working a small assembly (3-6 parts) — not a design team's process. If a
project genuinely has more parts/complexity than that, treat this as a
starting template, not a ceiling.
