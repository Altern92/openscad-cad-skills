# Agent eval 2026-11-01 (P7 agent QA v2 + P8 + NEXT §6 ablation)

Tasks: `bench/agent_eval.py` (5 tasks, each from a real failure record in
`04_Kita/openscad_skill_training_data*` or the SSD sweep). Agent: Claude Sonnet
subagent (Claude Code Agent tool), one run per cell. Grading: deterministic
(mesh measurements + `validate_scad.sh --all`), no judge. Tokens: the
subagent's own usage report (`bench/agent_eval_usage_2026-11-01.tsv`).

Arms:
- **full** — agent reads `openscad-cad/SKILL.md` + `scad-modeler/SKILL.md`
- **lean** — agent reads `openscad-cad/SKILL.md` only (scad-modeler's validator still used)

Both arms ran against the installed validator of that moment (before the two
fixes below). Grades below are on the geometry and on the report against
what the agent saw.

| Task (source) | full | lean |
|---|---|---|
| clear_span_tenons (fc-006) | PASS, crossbar 140 mm | PASS |
| standoffs_on_holes (SSD board_shelf) | PASS, 4 through-holes | PASS |
| flip_keeps_hole (fc-001) | geometry PASS; validator false FAIL (fixed) | geometry PASS; same false FAIL |
| lightening_cutout (chain-20) | PASS | PASS |
| honest_report (uc-005) | PASS: honest; hinge opens upward | report honest, but **hinge axis swings the lid INTO the box** — invisible to the old validator, `mechanics=FAIL` after the fix |
| **substantive** | **5/5** | **4/5** |
| mean tokens / run | 79 091 | 68 961 (−12.8 %) |
| mean tool calls / run | 9.6 | 8.8 |
| mean wall time | 65 s | 51 s |

## What the transcripts show (cost, NEXT §6)

Parsed from the subagent transcripts (tool calls only): the agents read the
two SKILL.md files and the templates; **none opened `references/validation.md`,
`INCIDENTS.md` or `NEXT.md`**. `scad-modeler/SKILL.md` is 56 691 B (~14 k tokens),
`openscad-cad/SKILL.md` 25 468 B (~6 k); one `validate_scad.sh --all` output is
~6.3 kB (~1.6 k tokens). So in this setting the skill text is ~20 k of ~70–80 k
tokens per run, and the scad-modeler SKILL.md accounts for about the full−lean
difference (~10 k). The §6 suspects validation.md / NEXT.md / INCIDENTS were not
the cost driver here.

## Validator bugs found by the agents (fixed, with fixtures)

1. One-part assembly failed as "MODE/PART switch did not take effect" →
   `positioned_tripwire_single_part`.
2. A declared contact pair was never swept, so a hinge whose lid swings into
   the box passed with 0 positions → `motion_declared_pair_still_swept`.

## Limits

n = 1 per cell: the 5/5 vs 4/5 difference is one task and not a statistical
result. Sonnet, not the model the user runs day to day. Tasks are small (1–3
parts); a large assembly would read more of the skill.

## P18: compact scad-modeler SKILL.md (slim arm)

`scad-modeler/SKILL.md` cut from 56 660 B to 12 817 B (rules, declaration
table, verdicts, report; the old full text moved verbatim to
`references/workflow_details.md`, read on demand). Same 5 tasks, **n = 2 per
task**, against the fixed validator.

| Task | full (n=1) | lean (n=1) | slim (n=2, mean) | slim grade |
|---|---|---|---|---|
| lightening_cutout | 65 716 | 60 568 | 67 107 | PASS ×2 |
| standoffs_on_holes | 59 837 | 60 845 | 63 278 | PASS ×2 |
| flip_keeps_hole | 97 859 | 68 798 | 72 188 | PASS ×2 |
| honest_report | 72 212 | 77 065 | 80 815 | PASS ×2 |
| clear_span_tenons | 99 833 | 77 530 | 85 172 | PASS ×2 |
| **mean tokens / run** | **79 091** | **68 961** | **73 712 (−6.8 %)** | **10/10** |
| mean tool calls | 9.6 | 8.8 | 8.6 | |
| mean wall time | 65 s | 51 s | 47 s | |

Reading: the static saving is ~11 k tokens per read of the file; the measured
mean saving is ~5.4 k, inside the per-task spread (standoffs 56 830 vs 69 726
for two identical runs). Quality held: 10/10, including honest_report, the
task lean failed. The runs also differ from the full arm in the validator
version (full ran before the two fixes), so the comparison is indicative,
not a controlled A/B. No agent opened `workflow_details.md`.
