<!-- RAG-passport: file=templates/plan.md | skill=scad-modeler | applies_to=[plan, architecture-options, decision, gate-check_plan] | version=2026-09-11 | source=06_RAG_taisykles (T2) | kind=TEMPLATE (copy into project, do not edit here) -->
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
gate explicitly by filling in the line below -- delete the whole block
otherwise, don't leave it as an inactive example.

**Keep the comment markers.** `check_plan.py` reads the form
`<!-- PLAN_EXEMPT: reason -->` and does not accept a bare `PLAN_EXEMPT: ...` line. An
earlier version of this template said "uncomment", which produces a plan the
gate rejects with "fewer than 2 architecture options listed (found 1), and no
PLAN_EXEMPT declared" -- measured 2026-09-12, found by an adversarial review:

<!-- Fill in only if truly exempt. Keep the comment markers.
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
