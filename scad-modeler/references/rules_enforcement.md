# Rules-enforcement engine (how to make the skill follow its own rules EVERY time)

> Goal: zero "forgot the rule" cases. Principle — **a rule must be
> machine-checkable, not just remembered by the model**. A prompt reminds;
> a script proves. If a script can't prove a step actually happened, work
> stops.

## 1. Why agents drift from stated rules (3 main reasons)

1. **Context overload** — in a long SKILL.md, rules "drown" among details;
   the model follows the last example it saw, not the rule.
2. **No consequence** — if a step is skipped, nothing stops; the model gets
   positive feedback for a "fast" answer even without verification.
3. **The rule isn't checkable** — "must do X" with no mechanism to confirm
   X actually happened (and happened correctly).

Confirmed counter-evidence from the literature: iterative verify-judge-correct
loops reduce LLM errors without damaging already-correct answers — DISC
(Denoising Iterative Self-Correction, Yin/Ken/Stremmel, Thomson Reuters Labs,
[arxiv 2606.21724](https://arxiv.org/abs/2606.21724)), which **beats**
Chain-of-Verification (CoVe) as a baseline (verified 2026-08-19 via
Perplexity — an earlier citation incorrectly called this "the CoVe paper",
when CoVe is only the comparison baseline in it and the proposed method is
DISC with a binary judge-gate),
"an agent checking its own work before answering" ([BeFailProof](https://befailproof.ai/guides/how-to-make-ai-agents-reliable/)),
restricted actions and structured outputs ([n8n](https://blog.n8n.io/make-ai-agents-more-reliable-and-restrict-the-actions-they-can-take/),
[Gemma 4 guardrails](https://dev.to/system_rationale/part-3-making-gemma-4-agents-production-ready-guardrails-structured-outputs-and-self-healing-575n)),
and that production agents need more than prompts — they need a state
machine and deterministic gates ([Production AI agents](https://www.mygreatlearning.com/blog/production-ai-agents/)).

## 2. Layered execution model (4 layers)

### L1 — Prompt layer (reminds)
- At the top of SKILL.md — a **short "before doing anything" line**
  pointing to this document and to `validation_decision_tree.md` (not
  repeating every rule — those live below; just "where to look").
- Every mandatory step has **one** instruction in one place (duplicates
  diverge — the model picks whichever it saw last).

### L2 — Deterministic gates (proves)
Existing example: `check_plan.py` — proves §0.5 planning actually happened
(not just in prose). Every mandatory step gets a gate like this:

| Mandatory step | Gate (script proves it) |
|---|---|
| Intake done | `requirements.json`/`design_manifest.json` exists and matches the schema (`check_intake.py`, ✅ exists, tested against 4 synthetic cases 2026-08-19) |
| Planning (§0.5) | `check_plan.py` (exists) |
| Calculation table (§1) | `calculations.md` with a decisions log (exists via `check_assumptions.py`) |
| Physical narrative (§0.6) | R-03 in `rules_manifest.yaml` — currently MANUAL (no automated gate; content quality isn't script-checkable) |
| Geometry | `validate_scad.sh --all` (exists) |
| Moving parts | `joints.json`'s `motion` array → `motion_sweep.py` (exists; auto-triggered via `validate_scad.sh`, gated by `rules_manifest.yaml` R-09) |
| Change recalculation | `check_dependencies.py` (✅ exists, see `change_propagation.md`) |

Note (2026-08-19): not every rule HAS an automated gate, and that's a
deliberate decision, not a gap — R-03/R-05/R-07/R-08/R-10 in
`rules_manifest.yaml` are marked `kind: manual` because checking them
would need either content-quality judgment (does the narrative actually
answer the question, not just fill in a field) or a step the system
doesn't have yet (exporting assembly-positioned STLs for a collision
check). `check_rules.py` still prints them and requires an explicit
verdict from the model — silent omission isn't allowed, but a rubber-stamp
"PASS" isn't either, since that would be a false sense of certainty.

**A real trap found and fixed (2026-08-19):** `validate_scad.sh` used to
use `set -e`, so ONE unrelated failure (e.g. an unresolved Critical
assumption in `calculations.md`) aborted the WHOLE script before the
connectivity/bore/mechanics checks ever ran. A different model then
"manually confirmed those checks separately" — an unverifiable claim of
certainty, exactly the same trap this whole system exists to close. Fixed:
`validate_scad.sh` no longer stops at the first failure — every
independent check runs and prints its own `CHECK_RESULT <name>=PASS|FAIL|
SKIP` line; `check_rules.py` can carry a `success_pattern` field that
determines the R-04/R-09 verdict from that SPECIFIC `CHECK_RESULT` line,
not from the whole script's exit code (which can be non-zero because of a
completely unrelated failure). Tested: a project with an unresolved
Critical assumption but otherwise-clean geometry now correctly shows
R-04/R-09 = PASS, R-11 = FAIL — with no "manual" confirmation needed.

### L3 — Self-check loop (the model checks itself)
Before the §8 final report, the model runs the **rules manifest** (L4) and
assesses each line itself: `done / skipped / not applicable`. Skipped →
go back, do it, re-run. This step is not optional "if I have time" — it's
a mandatory gate before answering the user.

### L4 — Rules manifest (machine-checkable list)
The file `rules_manifest.yaml` (next to SKILL.md): the **single** list of
every mandatory rule, ✅ exists (12 rules, 2026-08-19). `scripts/check_rules.py`
runs it before §8 — tested against an empty project, a fully populated
project, and a deliberately broken (`status: "unknown"`) case; a
real-format example (simplified from the actual 12-rule YAML):

```yaml
rules:
  - id: R-01
    rule: "Intake: requirements.json exists and is valid"
    check: "file exists requirements.json && schema valid"
    gate: check_intake.py
    applies: new_design
  - id: R-02
    rule: "Planning: plan.md exists for a 3+ part assembly"
    check: "check_plan.py passes"
    gate: check_plan.py
    applies: assembly_3plus
  - id: R-03
    rule: "validate_scad.sh --all after EVERY change"
    check: "last run green + mtimes newer than last .scad edit"
    gate: validate_scad.sh
    applies: any_change
  # ... full list
```

The model must run `check_rules.py` and **cite its output** in the §8
report. If no script exists for a given step, the rule is treated as not
implemented.

## 3. Failure handling (what happens when a gate doesn't pass)

1. **Stop** — don't patch "around" it, don't rewrite the output.
2. **Fix at the source** (the parameter, the script, the geometry) — not
   the output.
3. **Re-run from the top** — not just the one gate that failed (cascading
   effect: downstream only passes once upstream is clean).
4. **Record it** — if a gate let a bug through (a false pass), log an
   incident in `INCIDENTS.md` (already established practice).

## 4. Why this will work for this skill

The skill already has the right foundation: a set of scripts that check
geometry **independently of the model** (`check_*.py`). This engine extends
that same principle to **process** steps (intake, planning, narrative,
change-propagation) and adds the last missing piece — a **mandatory
self-check before answering** (L3+L4). At that point, following the rules
no longer depends on the model's memory: scripts prove it, and the model's
job is just to run them and cite the results.

## Source log

| ID | Claim | Source (URL) | Type | Date | Status |
|---|---|---|---|---|---|
| E-001 | DISC: iterative verify-judge-correct loops with a binary judge-gate reduce LLM errors without damaging correct answers; beats CoVe and Self-Refine as baselines (the paper's actual subject -- not "the CoVe paper" as incorrectly cited earlier; corrected 2026-08-19 via Perplexity verification) | https://arxiv.org/abs/2606.21724 | primary | 2026-08-19 (corrected) | ✅ sourced, verified |
| E-002 | Agent reliability: restrict actions, structured outputs, self-healing | https://befailproof.ai/guides/how-to-make-ai-agents-reliable/ ; https://blog.n8n.io/make-ai-agents-more-reliable-and-restrict-the-actions-they-can-take/ ; https://dev.to/system_rationale/part-3-making-gemma-4-agents-production-ready-guardrails-structured-outputs-and-self-healing-575n | primary | 2026-08-19 | sourced |
| E-003 | Production agents need more than prompts -- a state machine and gates | https://www.mygreatlearning.com/blog/production-ai-agents/ | primary | 2026-08-19 | sourced |
| E-004 | Formally verified code generation via self-refinement (AlphaVerus) | https://mlanthology.org/icml/2025/aggarwal2025icml-alphaverus/ | primary | 2026-08-19 | sourced |
| E-005 | A verification loop improves CAD generation results (CADCode-Verify) | https://proceedings.iclr.cc/paper_files/paper/2025/hash/81a934cd364e18ea6fdeaf57a93c17d4-Abstract-Conference.html | primary | 2026-08-19 | sourced |
