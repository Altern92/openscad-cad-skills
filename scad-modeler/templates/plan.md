# Plan — <project name>

Fill in every section for real before touching the calculation table (§1).
An unfilled template is supposed to fail `check_plan.py` — that's the point,
see the script's own docstring.

## Task

<one paragraph: what is this assembly, what does it need to do>

## Architecture options

At least two meaningfully different options, even if one is obviously
better — comparing one option against itself isn't a comparison, it's an
assumption wearing a table. If there is genuinely only one sane architecture
(a single bracket, an obvious layout with no real alternative), skip this
gate explicitly by uncommenting and filling in the line below -- delete it
entirely otherwise, don't leave it as an inactive example:

<!-- Uncomment and fill in only if truly exempt:
PLAN_EXEMPT: single obvious architecture -- <state why in one clause>
-->

| Option | Description |
|---|---|
| Datum | <the most plausible option> |
| Alt A | <a genuinely different approach, not a minor variation> |

## Comparison

Score each alternative against the datum, `+`/`0`/`-`. Always include the
uncertainty/risk row (`references/planning.md` §2 explains why).

| Criterion | Datum | Alt A |
|---|---:|---:|
| <criterion 1> | 0 | |
| **Uncertainty/risk** | 0 | |

## Decision

The decisions/assumptions log (`references/planning.md` §1 format) — must
contain at least one `Decision` row with `Status: Confirmed`, recording which
architecture option was actually chosen and why.

| ID | Type | Criticality | Statement | Status | Evidence |
|---|---|---|---|---|---|
| D1 | Decision | Ordinary | <which option, and why> | TBD | |

## Parts and dependency order

Every part that will appear in `layout.scad` must be listed here first —
`check_plan.py` fails if `layout.scad` names a part this table doesn't.

| Part | Depends on | Notes |
|---|---|---|
| <part_name> | <another part_name, or "-"> | |
