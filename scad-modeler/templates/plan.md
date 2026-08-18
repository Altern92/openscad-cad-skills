# Design plan: <project name>

Fill this in before any geometry. `scripts/check_plan.py` reads it, so keep the
section headings and table shapes. See `references/planning.md` for why each
gate exists.

## 1. Task

What it must do, in one paragraph. Then:

- **Must:** <hard requirements — dimensions it has to fit, loads it has to carry>
- **Must not:** <exclusions that are easy to violate by accident>
- **Preference:** <things that are nice, and may be traded away>
- **Contradictions in the brief:** <state them here rather than silently picking
  a reading; "none" if there are none>

## 2. Architecture options

At least two, differing in *principle* — not in a dimension. One option plus a
strawman is not a comparison.

| # | Option | Working principle | Known risk |
|---|---|---|---|
| A | <e.g. single-stage spur> | <how it works> | <what could go wrong> |
| B | <e.g. two-stage planetary> | | |

## 3. Selection

Datum: **A**

Score each alternative against the datum: `+` better, `0` same, `-` worse.
Tag each criterion `known` / `assumed` / `blocked` so a guess reads as a guess.
Keep the unknowns row — without it the least-specified option wins by default.

| Criterion | Status | A | B |
|---|---|---|---|
| Packaging / envelope | known | 0 | + |
| Part count | known | 0 | - |
| Printability | assumed | 0 | 0 |
| Backlash risk | assumed | 0 | - |
| Unknowns remaining | known | 0 | - |

**Decision:** <A or B> — <one line: the reason, not a restatement of the score>

## 4. Dependency order

`X` = this part cannot be finalised until that one is; `?` = suspected, not
checked; blank = independent. A cycle means those parts are one module and get
sized together — say so rather than inventing an order.

| Part | Depends on | Mark |
|---|---|---|
| gear_pair | — | |
| shaft | gear_pair | X |
| housing | gear_pair, shaft | ? |

**Design order:** gear_pair, shaft, housing

**Modules (parts that must be sized together):** <list, or "none">

## 5. Assumptions and decisions

Every number that came from inference rather than a source is an `assumption`.
If being wrong about it would change a decision, put `blocking` in Status —
`check_plan.py` refuses to pass the gate while one is unresolved.

| ID | Kind | Statement | Status | Source |
|---|---|---|---|---|
| F1 | fact | Bearing 608 OD is 22.0 mm | confirmed | datasheet |
| A1 | assumption | Motor shaft is 5 mm | blocking | measure before proceeding |
| A2 | assumption | Housing wall 3 mm is stiff enough | open | no load case defined |
| D1 | decision | Two-stage, per §3 | confirmed | §3 |
| R1 | risk | If shaft differs, pinion bore changes | open | depends on A1 |
| Q1 | question | Is the output direction fixed? | open | ask |
