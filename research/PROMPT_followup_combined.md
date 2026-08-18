# FOLLOW-UP PROMPT — combined (fills the template placeholders + corrects the review scope)

> Paste this whole block as the next message. It replaces both the unfilled
> template and the separate feedback list.

---

Here are the placeholders you asked for, filled in:

- **Topic:** Improving two LLM-agent "skills" (`openscad-cad`, `scad-modeler`) that make an AI coding agent generate, verify, and export parametric 3D-printable CAD in OpenSCAD — with the specific goal of raising *first-pass* correctness (geometrically valid, dimensionally right, printable, and — for assemblies — non-interfering through motion).
- **Number of examples:** 4 (worked end-to-end, see §3 below for which)
- **Audience level:** advanced
- **Field/domain:** mechanical design for additive manufacturing (FDM/FFF), applied geometry/computational geometry, and LLM agent/tool design
- **Length preference:** exhaustive

Everything you need about the subject matter is in the research brief I already
sent you — the full verbatim source of both skills, a mechanism summary of how
they currently verify correctness, my own gap analysis, and research questions
Q1–Q8. Treat that brief as the primary input to this task. Do not restate it
back to me.

## 0. Read this before you start — what was wrong with your last answer

Your previous response was a well-organised **restatement of the gap list I gave
you**. It contained zero citations, verified none of my claims, answered none of
my four specific factual questions, and introduced no tool, standard, or paper I
had not already named. It was an executive summary, not research. The following
requirements are non-negotiable for this pass.

**R1 — Citations are mandatory.** Every substantive claim carries a source:
standard number, paper (with author/year/venue), documentation URL, or
repository link. Mark each source as peer-reviewed / standard / official
documentation / community-empirical. An uncited recommendation is an opinion,
and I already have my own.

**R2 — Treat my gap list as hypotheses, not findings.** I wrote it from reading
the source, unverified. Confirm, refute, or quantify each. If you agree with all
of them you have added no independent signal — I need you to find where I am
wrong or over-stated.

**R3 — Answer these four factual questions explicitly, stating how you verified
each:**
   a. Does `openscad --summary` (any sub-option: `all`, `geometry`,
      `bounding-box`, …) report bounding box / volume / surface area? Quote the
      current manual. If yes, the skill's entire STL→`trimesh` round-trip for
      dimension checking is unnecessary and one of its documented conclusions is
      wrong.
   b. Is the `check_collisions.py` docstring-vs-behaviour mismatch on
      watertightness real as I described it (docstring promises non-zero exit,
      code only prints a warning)?
   c. Is the `max(0.3 mm, 1 %)` bounding-box tolerance defensible? Derive from
      first principles what it *should* be, given chordal error at `$fa = 2`,
      `$fs = 0.3`.
   d. Quantify the OpenSCAD inscribed-polygon hole-undersizing error exactly,
      give the compensation formula, and explain how it interacts with `$fn`,
      `$fa`, `$fs` and with slicer XY-compensation (do the two double-count?).

**R4 — Cost every recommendation.** `SKILL.md` is a prompt an LLM must actually
read and follow; instruction-following degrades as it grows, and every gate adds
latency and failure surface. For each proposal state: token/complexity cost,
maintenance burden, what it displaces, and who maintains it. Rank everything by
(impact × confidence) ÷ effort. **Explicitly name which of your own previous
proposals are not worth it** for a single hobbyist user with one printer — a
recommendation list with nothing cut is not an engineering judgement.

**R5 — The design contract must not become an interrogation.** A skill that
refuses to start until it has eleven specification fields will simply be
abandoned. Design it as *infer sensible defaults → state every assumption
explicitly in the output → escalate the confidence tier only when the user
supplies real data*. Give the actual default table (field, default value,
source of that default, what breaks if the default is wrong).

**R6 — Cover the questions you skipped.** Q3 (gear standards, incl. **VDI 2736**
for polymer gears, **ISO 6336**/AGMA, **ISO 286** fits, tolerance stack-up
methods), Q4 (peer-reviewed FDM dimensional-accuracy data), Q5 (NopSCADlib,
Round-Anything, BOSL2, CadQuery/build123d, slicer CLI validation), Q6 (VLM
accuracy at judging geometry from renders), Q7 (LLM-for-CAD literature and its
*measured* failure modes).

**R7 — Keep and ground the tier model.** The 1–5 confidence tiers from your last
answer are the single best idea in it. Keep them, but make them rigorous: entry
requirements, mandatory validation gates, expected first-pass success rate, and
the evidence that expectation rests on. A tier with no stated evidence is
decoration.

## 1. Core concepts — define these precisely

Define, unambiguously and with sources, the fundamental principles that govern
whether this workflow can succeed. At minimum:

- **CSG/mesh vs B-rep modelling** and what each makes verifiable or unverifiable.
- **Tessellation and chordal error** — the exact relationship between `$fn`,
  `$fa`, `$fs`, facet count, and dimensional deviation from the ideal surface.
- **Interference vs clearance vs intentional contact** — why binary collision
  detection is the wrong primitive for printed assemblies.
- **Process capability and fit classes** in the context of FDM: nominal
  dimension, systematic bias, random variation, achievable IT grade.
- **Tolerance stack-up**: worst-case vs RSS vs Monte-Carlo, and when each is
  the correct choice.
- **Anisotropy in FDM parts** and why print orientation is a structural, not
  cosmetic, decision.
- **What "validated" means for a generated model** — the distinction between
  compiled, rendered, geometrically valid, printable, dimensionally correct,
  and functionally correct. Define each as a separately checkable gate.

## 2. Mathematical formulas — full treatment

For every formula: define each variable and constant, give the derivation or
underlying logic, give a step-by-step application procedure, and state its
validity limits and failure modes. Cover at least:

- Chordal/sagitta error for a polygonised circle; inscribed-polygon
  undersizing and its compensation factor; the correct facet resolution for a
  target dimensional accuracy.
- Gear geometry: module/pitch relations, centre distance with and without
  profile shift, contact ratio, minimum tooth count before undercut, backlash,
  tip/root clearance — and the **polymer-specific** load rating and derating
  path (VDI 2736), including what changes for a 3D-printed, layer-bonded tooth.
- Fits: ISO 286 hole/shaft deviations for the grades relevant here; press-fit
  interference and the resulting hoop stress in a printed bore; how to translate
  a standard fit into an OpenSCAD clearance value on a real printer.
- Tolerance stack-up: worst-case sum, RSS, and a Monte-Carlo formulation, each
  applied to a dimension chain.
- Bounding-box and mesh-metric tolerances: what deviation is attributable to
  tessellation, what to the model, what to the process.
- Motion/sweep sampling: how fine an angular or linear step is provably
  sufficient to not miss an interference, as a function of part geometry and
  the minimum clearance threshold. This one matters — state honestly if a
  rigorous bound is not practical and what the accepted heuristic is.

## 3. Practical examples — four, worked end to end

Each example: problem statement → structured specification (per R5's default
table) → calculations with formulas applied → the actual OpenSCAD/params
structure → the validation commands run and their expected output → the final
result, its interpretation, and the residual risk that remains unverified.

1. **Shaft–hole fit** (running fit) on a specified printer/material — the
   simplest case where standards, tessellation compensation, and empirical
   calibration all collide.
2. **Press-fit bearing seat** — the case where intentional interference must
   pass a collision check that would otherwise flag it as a failure.
3. **A meshing spur-gear pair with a housing** — centre distance, contact ratio,
   undercut check, polymer derating, plus swept-motion interference through a
   full rotation.
4. **A hinged or sliding two-part mechanism** — where static collision
   detection passes and motion or assembly-sequence checking fails.

## 4. Real-world applications

Where these methods are used in practice — professional CAD interference
checking, DfAM validation pipelines, slicer-based printability gating,
automated design/KBE systems — and what measurable benefit each delivers.
Be concrete about what industry actually does that this hobby workflow does not.

## 5. Related concepts and dependencies

The prerequisite knowledge a reader (and the agent itself) needs, and the
tooling dependency graph: what must be installed, detected, or calibrated
before each validation gate is meaningful.

## 6. Pitfalls and common mistakes

Both categories:
- **Domain pitfalls** — the geometry/tolerance/gear/fit errors that produce
  plausible-looking but wrong parts.
- **Agent pitfalls** — the documented failure modes of LLMs generating CAD code
  (per Q7), and which guardrails in the literature measurably reduce them.

For each: how it manifests, why it survives current checking, and the specific
gate that would catch it.

## 7. Visual aids — conceptual descriptions

Describe every diagram/chart that would materially help, what it plots and what
it demonstrates. Additionally — and this is a deliverable, not decoration —
specify the **render convention the skill itself should adopt** so a
vision-language model can actually verify geometry: which views, which section
cuts, what annotation, what scale reference, what colour coding, and what
evidence supports those choices (Q6).

## 8. Required output structure

Deliver in **Lithuanian** (technical terms, standard designations, library
names, code identifiers and citation titles stay in their original language):

1. **Santrauka** — top 5–10 changes ranked by (impact × confidence) ÷ effort,
   plus the explicit "not worth doing" list required by R4.
2. **Sections 1–7 above**, in that order.
3. **Faktinių klaidų sąrašas** — every claim in the brief you found wrong,
   outdated, or over-generalised, with correction and source. Must include
   verdicts on R3 a–d.
4. **Confidence-tier specification** per R7.
5. **Siūloma nauja struktūra** — recommended file/folder layout for the skill
   set, with a one-paragraph spec per new script (inputs, outputs, exit codes,
   dependencies).
6. **Nauji `references/` failai** — draft the actual content of a
   standards-based tolerance/fit table and the printer calibration procedure
   that populates it.
7. **Prioritetinis planas** — phased, separating what I can implement now, what
   requires me to print and measure calibration coupons, and what is a
   longer-term architectural change.
8. **Šaltiniai** — grouped by theme, with links and source-type labels.

**Flag your own uncertainty explicitly.** Where you could not verify something,
write "neatsakyta — reikia patikrinti X būdu" rather than producing a confident
guess. The material you are reviewing was built on the principle of never
asserting an unverified claim as fact; this review is held to the same standard.
