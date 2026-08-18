# RESEARCH ORDER — standalone, for a fresh conversation

> Paste this as the first message in a new chat. It is self-contained.

---

You are doing a **source-backed research pass**, not a design consultation.
I need retrieved, citable facts. I do not need architecture proposals,
restatements of my question, or reasoning from memory.

## Context — the minimum you need

I maintain a set of instruction documents ("skills") that drive an AI coding
agent to produce parametric 3D-printable CAD in **OpenSCAD**, then verify it
before export. Output is FDM/FFF printed functional mechanical parts — brackets,
enclosures, storage inserts, and multi-part assemblies with gears, bearings and
shafts — on a consumer printer, ~0.4 mm nozzle, ~0.2 mm layer, PLA/PETG.

Current verification chain: render → look at the image → export STL → check the
bounding box against a declared value → check parts for overlap with
trimesh + FCL. I am replacing the weak parts of that chain and need external
evidence for four specific areas before I commit engineering time.

**Already settled — do NOT re-derive, re-check, or comment on these.** They were
verified against OpenSCAD's upstream source and are closed:

- OpenSCAD emits circle/cylinder vertex `i` at `phi = 360·i/n`, so a vertex
  always lies at angle 0.
- Fragment count is `ceil(max(min(360/$fa, 2πr/$fs), 5))`, with an `$fn > 0`
  short-circuit and an `r < GRID_FINE` (2⁻²⁰) short-circuit to 3.
- Circles are inscribed polygons, so a modelled hole is undersized flat-to-flat
  by `d·(1 − cos(π/n))`; the exact compensation is `d/cos(π/n)`.
- Consequently a bounding-box check is nearly blind to that deficit and is the
  wrong instrument for round fit-critical features.

Spending output on any of the above is wasted.

## Rules — read before answering

1. **Every factual claim carries a resolvable source**: a full URL, and for
   papers author/year/venue/DOI. Footnote markers that link to nothing are
   worse than no citation.
2. **Quote, don't paraphrase, for anything load-bearing.** If you claim a CLI
   flag exists, quote the line from the documentation. If you claim a library
   generates a BOM, quote the README sentence that says so.
3. **Label every claim by how you established it**: read in official docs /
   read in a README or repo / peer-reviewed paper / secondary industry article /
   inferred / not verified.
4. **"Not verified" is an acceptable and useful answer.** Write
   `NEPATIKRINTA — reikia [tikslus būdas]`. A confident guess is not acceptable
   and is worse than an admission, because I will act on it.
5. **Do not propose architecture, file layouts, tier models, or rewritten
   instructions.** I am building that myself. You supply facts.
6. Answer in **Lithuanian**; keep technical terms, library names, flags,
   standard numbers and citation titles in their original language.

## Block A — OpenSCAD library audit

For each of **NopSCADlib**, **Round-Anything**, **dotSCAD**, and **BOSL2**,
read the actual repository README and documentation, then report:

1. Concrete feature list relevant to: bill-of-materials generation, exploded
   assembly views, assembly instruction generation, filleting/rounding,
   tolerance-aware geometry for printed fits, off-the-shelf part ("vitamin")
   models, and gear generation.
2. For **NopSCADlib** specifically: does it generate a BOM automatically, and
   does it generate exploded views or assembly instructions? Quote the
   documentation. This is the one I most need settled — it overlaps work my
   system currently does by hand.
3. For **Round-Anything** specifically: what does it actually provide beyond
   rounding — is there real tolerance/fit tooling, or is that a
   misunderstanding on my part?
4. Maintenance signal: last release or last commit date, open issue count,
   whether it appears actively maintained.
5. Installation/dependency cost and any known incompatibilities between them.

## Block B — Headless slicer validation

Can "is this printable?" become a command with an exit code, rather than a
judgement call? For **PrusaSlicer**, **OrcaSlicer** and **CuraEngine**:

1. The exact CLI invocation for headless slicing of an STL with a given
   profile. Quote the documented flags.
2. Which validation signals are obtainable without a GUI: non-manifold or
   self-intersection detection, thin-wall or unprintable-feature warnings,
   support volume, print time, material use. Quote where documented.
3. **Exit-code semantics** — does the CLI return distinct non-zero codes for
   distinct failure classes, or a single generic failure? Where is this
   documented, and is there a known gap between documented and actual
   behaviour?
4. Where the output goes: stdout, a log file, a G-code comment header?
5. Verdict: is a slicer-based printability gate realistically implementable
   today, or does the tooling not expose enough to build one?

## Block C — FDM dimensional accuracy, by feature type

I need to replace an anecdotal three-row clearance table with something
defensible.

1. What does the **peer-reviewed** literature report for FDM dimensional
   deviation, separated by feature type where possible: internal holes in XY,
   internal holes in Z (axis vertical), external cylinders, slots, and thin
   walls? I need magnitudes and, where reported, spread — not just "accuracy is
   limited".
2. Is hole undersizing on FDM a **systematic, measured** effect? Give figures
   and conditions (material, nozzle, layer height, diameter range).
3. What **IT grade** (ISO 286) is realistically achievable on hobby FDM, by
   feature type? If the literature does not support a feature-by-feature
   mapping, say so plainly rather than constructing one.
4. Does published data support or contradict the common community practice of
   ~0.2–0.5 mm per-side clearance for a sliding fit and ~0.1–0.2 mm interference
   for a light press fit in printed plastic?
5. Is there a published, reproducible **calibration coupon protocol** — printed
   test artefact plus measurement procedure — that yields per-printer,
   per-material offsets? Point me at the best-documented one.

## Block D — Two literature questions

### D1 — Vision-language models judging 3D geometry from renders
1. Is there any benchmark or study measuring VLM accuracy at assessing **CAD or
   mechanical geometry** from rendered 2D views — detecting wrong dimensions,
   interference, or missing internal features?
2. Do any studies measure whether specific rendering choices improve that:
   orthographic vs perspective, section cuts, dimensional annotation, colour
   coding, multi-view grids, known-scale reference objects?
3. If the evidence base is thin, state that as the finding and say what the
   closest adjacent evidence actually shows. Do not substitute general 3D
   reasoning benchmarks and present them as if they answered the question.

### D2 — LLM-generated CAD: measured failure modes
1. Survey the literature on LLMs generating CAD and parametric 3D models
   (text-to-CAD, OpenSCAD and CadQuery code generation, execution-feedback and
   visual-feedback repair loops, benchmarks and datasets).
2. **What failure modes are measured, and at what rates?** Named categories with
   numbers, from papers' results — not a plausible taxonomy you construct.
3. Which guardrail patterns have **measured** effect sizes: execution feedback,
   visual feedback, constraint checking, self-consistency, program repair?
   Report the numbers and the benchmark they were measured on.
4. Is there published evidence that an LLM writes correct CAD more reliably in
   one representation than another — OpenSCAD vs CadQuery/build123d vs a
   JSON/DSL intermediate? If the only evidence is blog benchmarks, say so and
   label it as such.

## Output format

1. **Blocks A–D**, in order, each ending with a one-line verdict of the form
   *"Pakanka įrodymų / Įrodymų per mažai / Nepatikrinta"*.
2. **Šaltiniai** — grouped by block, resolvable URLs, source-type labels, DOIs
   where they exist.
3. **Ko nepavyko rasti** — an explicit list of every sub-question you could not
   close, each with the specific search, document, or command that would close
   it.

If a whole block turns out to be unsupportable from available sources, say so
and stop — a short honest answer is more useful to me than a long one padded
with adjacent material.
