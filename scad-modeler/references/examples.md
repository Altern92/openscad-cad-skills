<!-- RAG-passport: file=references/examples.md | skill=scad-modeler | applies_to=[examples, retrieval, copy-from] | version=2026-09-12 | source=agent-reach research on example retrieval + measured gap -->
# Examples — what to copy, and from where

> **Why this file exists.** A working end-to-end project shipped for months and no
> agent ever used it. It was linked from `README.md` (which people read) and
> mentioned in `SKILL.md` exactly once, as the source of an incident — while
> `templates/` had **eight** links from the same file. Agents copied the templates
> and never opened the example. A working reference nobody can find is not a
> reference.

---

## The working project (always available, validates clean)

**`scad-modeler/examples/gear_reduction/`** — 11-tooth pinion driving a 66-tooth spur
(6:1, module 1.0). 102 lines total, and **all 18 checks pass** on it right now.

```bash
cd scad-modeler/examples/gear_reduction
bash ../../scripts/validate_scad.sh --all      # COVERAGE: 11 passed, 0 failed
```

| Copy this | When |
|---|---|
| `layout.scad` — the recursive `at()` lookup | you need positioned parts without assembly-level `translate()` in part files |
| `assembly.scad` — the MODE/PART switch | any assembly; copy it rather than writing it from memory (§6) |
| `calculations.md` — the table shape | before writing geometry; §1 requires this shape |
| `joints.json` — a declared motion array | anything that moves; this is what auto-triggers the sweep |

**Read it as a whole once** when starting a new assembly. It is 102 lines — cheaper
than reconstructing the file layout from the prose in SKILL.md.

---

## Fragments, not projects

**`openscad-cad/references/patterns.scad`** — 302 lines, 6 patterns plus 4 session
lessons. Copy a pattern, not the file.

| Pattern | Use when |
|---|---|
| 0 · circular-hole tessellation (`true_hole_d()`) | **any hole that must measure true** — the single most-reused function in the library |
| 1 · rectangular locating pocket | Gridfinity bin with a rectangular item |
| 2 · irregular-contour pocket | the item has a non-rectangular outline |
| 3 · friction-fit sleeve with cable exit | a cable or wire passes through |
| 4 · bent duct via segmented `hull()` | a tube changes direction |
| 5 · hole calibration coupon | a press fit matters and no calibration profile exists |

---

## Your own past projects

The strongest signal is a **structurally similar** earlier project, not a generic
example. Before designing, check whether the current project has siblings:

```bash
ls ..                       # sibling projects
find .. -name params.scad -not -path '*/build/*' | head
```

Read their `params.scad` and `README.md` first — the naming, units, and fit
conventions there are the ones the user already accepted.

**Caveat:** an old project may predate the current workflow. It can be missing
`design_manifest.json`, `bores.json`, or `plan.md`, and its validation verdicts will be
mostly `not-applicable` as a result. Copy its geometry conventions, not its process.

---

## What the evidence says, and what it does not

| Finding | Source |
|---|---|
| Examples help **when task-relevant**; relevance beats volume | CodeRAG-Bench (NAACL 2025) |
| Lexical similarity is a **weak proxy** for useful context | RepoBench / DevEval literature |
| Gains **saturate around 6** examples, and bad examples **hurt** | in-context selection studies |
| Context files show a **correctness null at +20% cost** | arXiv 2602.11988; REALM@EMNLP 2026 |

**So: this file is a hand-built retriever, not a corpus.** It exists because the
evidence supports *having the right example at hand* and does not support *mining
idioms into the skill*. Keep it small. If an entry is never the answer to "copy
this for that", delete it.

**Not evidence:** that this improves results. That would need roughly **120 tasks
per arm** to detect a 10pp effect — see `_wiki/scad/05_agentu_testai.md`.