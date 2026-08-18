# Planning before geometry

The failure this prevents: an agent handed a vague brief starts computing gear
ratios and centre distances before it has decided *what kind of mechanism this
is*. The numbers are then correct and worthless, because the architecture they
rest on was never chosen — it was assumed, silently, from whichever
interpretation came first.

Pahl & Beitz put the principle bluntly: *"no design can hope to correct a poor
solution concept in the embodiment design stage."* A wrong concept cannot be
computed out of later. This is the most durable claim in the whole planning
literature, and it is the only one this file treats as settled.

## The four gates

Adapted from Pahl & Beitz and VDI 2221, compressed to what one person building
a printed mechanism can actually sustain. Fill in `templates/plan.md`; each
section is a gate.

**1 — Task.** What the thing must do, what it must fit, what it must not do.
Separate *requirement* from *preference*. If the brief is contradictory, say so
here rather than picking a reading and moving on.

**2 — Architecture options.** At least two, genuinely different in principle —
not one idea plus a strawman. This is the whole point of the gate: a single
option is not a choice, it is an assumption wearing a table.

For mechanisms, vary the *principle*: spur vs planetary vs belt; bearing pressed
into housing vs into a printed carrier vs a bushing; one-piece housing vs split
shell. Two options that differ only in a dimension belong in §1's calculations,
not here.

**3 — Selection.** A minimal Pugh comparison: pick one option as the datum,
score the others `+` / `0` / `-` on 3–5 criteria. Weights are optional and
usually harmful when the brief is incomplete.

Two rules that matter more than the arithmetic:
- Include **one criterion for unknowns**, otherwise the matrix rewards whichever
  option is least specified — it looks clean because nobody has thought about it.
- Tag each criterion `known` / `assumed` / `blocked`, so a score based on a guess
  is visibly a guess.

The output is one line: which option, and why. The matrix is the reasoning, the
line is the decision.

**4 — Dependency order.** Which part's dimensions must be fixed before which.
A three-symbol matrix is enough: `X` = hard dependency, `?` = suspected but
unchecked, blank = independent. The `?` marks are the valuable part for a solo
workflow — they are where an assumption is about to be made without anyone
noticing.

Parts with many dependents get designed first. A cycle (`A` needs `B`, `B` needs
`A`) is not an error — it means those parts are one module and must be sized
together; say so rather than pretending an order exists.

## Assumptions and decisions log

One table, five kinds of row:

| Kind | Meaning |
|---|---|
| `fact` | confirmed against a datasheet, drawing, or measurement |
| `assumption` | used for now, not confirmed |
| `decision` | a choice made, with its reason |
| `risk` | something that would break the design if it went wrong |
| `question` | still needs an answer |

The one distinction that does the work: **fact vs assumption**. Any number that
came from inference rather than a source is an assumption, and if being wrong
about it would change a decision, mark it `blocking`. Blocking assumptions must
be resolved before detail work — that is what `scripts/check_plan.py` enforces,
so the rule is not merely advice.

This is the same discipline as the `PATIKRINTI` marker in SKILL.md §1, one stage
earlier: §1 catches unverified *numbers*, the log catches unverified
*premises*.

## Then, and only then

Architecture locked, dependency order known, blocking assumptions resolved →
SKILL.md §1's calculation table → `params.scad` → geometry.

Run the gate:

```bash
python3 scripts/check_plan.py --plan design/plan.md --layout layout.scad
```

It checks that the sections exist, that at least two architectures were
compared, that a decision was recorded, that no blocking assumption is
unresolved, and — the part worth having — that **every part in `layout.scad`
appears in the dependency order**. That last check catches a part that got
invented during detail work and never went through planning at all.

## What the evidence actually supports

Stated honestly, because parts of this literature are repeated far past what
the sources show.

**Strong.** Pahl & Beitz and VDI 2221 as staged design methodology, and the
concept-before-embodiment ordering. Decades of textbook standing.

**Strong.** DSM as a dependency-sequencing tool, and morphological charts plus
Pugh matrices as concept generation and selection tools. Standard engineering
design methodology with wide application.

**Weak, and commonly overstated.** The "1× / 10× / 100× / 1000×" cost-of-change
curve is **software** data — Barry Boehm's defect-fix costs from 1970s waterfall
projects at TRW, with corroboration from IBM, GTE and Bell Labs, published in
*Software Engineering Economics* (1981). It is not a measurement of mechanical
design, and the "IBM Systems Sciences Institute study" often cited alongside it
**does not exist as published research**. The directional claim — late changes
cost more — is well supported; the multipliers are not a mechanical constant and
should not be quoted as one.

**Reasonable transfer, not established practice.** Assumption and decision logs
(ADR, RAID) are mature in software architecture and project management. Applying
them to mechanical design is sensible and cheap, but it is a transfer, not
something with its own mechanical-engineering evidence base.

**Emerging, unverified here.** Recent work reports that LLM agents commit
prematurely to one interpretation and then defend it, and that CAD generators
recover coarse outer geometry while failing at faithful parametric structure.
Both match the failure this file exists to prevent, which is why the gate is
worth having — but the specific papers and their effect sizes were not verified
against primary sources, and no benchmark yet isolates "committed before the
architecture was settled" as a measured failure mode. Treat this as motivation,
not evidence.
