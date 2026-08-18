# ROUND 3 PROMPT — corrections + the research that is still open

> Paste this whole block as the next message.

---

This pass was a real improvement: you answered R3(a)–(d) with verdicts, confirmed
the `check_collisions.py` defect, derived the compensation formula from first
principles, and — importantly — marked Q5/Q6/Q7 as unanswered instead of
improvising them. The error-layer separation (CAD/tessellation → mesh validity →
process capability → fit intent → motion → mechanical load) is the correct
organising idea and I am adopting it.

I checked your arithmetic and it holds: the `d ≈ 17.2 mm` crossover,
`1 − cos(1°) = 1.523×10⁻⁴`, `$fs²/(2d) = 0.045/d`, and the `max(5, …)` fragment
floor are all correct.

Do **not** produce the new `SKILL.md` or the file-by-file script plan yet. I will
write those myself — I have direct access to the repository and you do not, so
that split wastes your effort. What I need from you is the part only external
research can supply. Four corrections first, then the three question blocks you
left open.

## A. Corrections to your last answer

### A1 — You conflated across-flats error with bounding-box error

Your §2.3–2.4 treats `Δ_bbox,max ≈ 2e` where `e = r(1 − cos(π/n))`. That is wrong
as stated, and the error matters.

OpenSCAD's `circle()`/`cylinder()` places a vertex at angle 0. When `n` is
divisible by 4 — and `$fa = 2` gives exactly `n = 180`, which is — vertices land
at 0°, 90°, 180° and 270°, so the axis-aligned bounding box touches the *ideal*
radius on all four sides and **the bounding-box error is approximately zero, not
`2e`**.

The `r(1 − cos(π/n))` deficit is real, but it is the **across-flats** deficit —
the apothem-to-apothem dimension — which is what governs whether a shaft enters
a hole. A bounding box barely sees it.

Redo this properly:

1. Derive bounding-box deviation as a function of `n` **and the polygon's
   rotational phase**, covering `n mod 4 = 0`, `n` even but not divisible by 4,
   and `n` odd. State OpenSCAD's actual starting phase and cite where that is
   specified or how you determined it.
2. Separately and explicitly define the **fit-relevant** deficit (across-flats,
   inscribed-polygon) — this is the one the compensation formula
   `d_model = d_target / cos(π/n)` corrects.
3. Then answer the question this raises: **is a bounding-box check the wrong
   instrument for round, fit-critical features altogether?** If it is largely
   blind to the deficit that actually causes a failed fit, say so, and specify
   what feature-level check should replace or supplement it — and how to obtain
   that measurement from an STL or from OpenSCAD directly.

Your conclusion that `max(0.3 mm, 1 %)` is far too loose as a *tessellation*
tolerance survives this correction. The derivation behind it does not.

### A2 — Your ISO 286 recommendation contradicts your own VDI 2736 warning

You correctly argue against pretending to run full VDI 2736 without material
data, because that manufactures pseudo-rigour. Then your `fit_defaults.yaml`
proposes H7/g6, H7/h6, H7/p6 as the reference frame for FDM fits.

An H7 hole at Ø8 mm is roughly +0.015/0 mm. Hobby FDM does not hold 15 µm. So
citing ISO fit designations risks exactly the pseudo-rigour you warned about —
a standard-looking label over a process that cannot realise it.

Resolve this explicitly:

1. What **IT grade** is actually achievable on hobby FDM, by feature type
   (XY hole, Z hole, external cylinder, slot, wall)? Cite measured data.
2. Given that, is it defensible to use ISO 286 designations at all here — as
   *intent vocabulary* only, as a source of nominal clearance magnitudes, or not
   at all?
3. If not, propose an **FDM-native fit class table** that does not borrow
   unachievable precision-machining labels: class name, functional definition,
   nominal per-side clearance range, and how a calibration profile shifts it.
4. State plainly which of the two you recommend and why.

### A3 — Your citations do not resolve

The `<sup data-citation="N">` markers point to nothing I can open, and the source
list at the end gives names without URLs or DOIs. Every source needs a
resolvable link, and for papers: author, year, venue, DOI.

Also mark, per claim, **how you established it**: read in official
documentation / read in a standard / read in a peer-reviewed paper / inferred
from source code / derived mathematically / community-empirical. I need to know
which claims rest on reading versus on execution.

### A4 — Which claims did you verify by running something?

You presented the `--summary` finding from documentation. Separate clearly:
what you confirmed from the current OpenSCAD manual text, versus what would
still require running a current binary. In particular, state the exact command
that would settle whether `--summary` reports volume, and whether `--summary`
requires an accompanying export operation to produce output at all.

## B. The three question blocks still open

These are the highest-value remaining work, because they need external sources I
cannot substitute for.

### Q5 — Tooling and ecosystem

For each of **NopSCADlib**, **Round-Anything**, **BOSL2**, **dotSCAD**,
**CadQuery**, **build123d**, and headless slicer CLIs (**PrusaSlicer**,
**OrcaSlicer**, **CuraEngine**):

1. What does it actually provide that this workflow currently does by hand?
   Be concrete — NopSCADlib's BOM and exploded-view generation directly overlap
   sections of my skill that are manual today.
2. Maturity, maintenance status, and dependency cost.
3. For the slicer CLIs specifically: exactly which validation signals are
   available headlessly (non-manifold detection, support volume, print time,
   material use, thin-wall or unprintable-feature warnings), the exact
   invocation, and the exit-code semantics. This determines whether
   "printability" can become a gate rather than a judgement call.
4. **CadQuery / build123d vs OpenSCAD, honestly assessed.** Not on aesthetics:
   does B-rep make the verification problems in this brief tractable in a way
   mesh CSG cannot — exact interference volumes, feature interrogation, real
   fillets, section analysis? And is there any published evidence about whether
   an LLM writes correct code more reliably in one than the other?
5. A recommendation: adopt, ignore, or revisit later — with the cost accounting
   you applied well in your last answer.

### Q6 — Vision-language models judging geometry from renders

1. What is the measured accuracy of VLMs at assessing 3D geometry from rendered
   2D views? Benchmarks and papers, not blog posts.
2. Which rendering choices measurably improve it: orthographic vs perspective,
   section cuts, dimensional annotation, colour coding, multi-view grids,
   known-scale reference objects, wireframe overlay?
3. Given the evidence, what role should visual inspection hold — verification
   gate, sanity layer, or dropped? You suspected "sanity layer only"; confirm or
   refute it with sources.
4. If the evidence is genuinely thin, say so — that is a legitimate finding, and
   more useful to me than a confident guess.

### Q7 — LLM-generated CAD: measured failure modes

1. Survey the literature on LLMs generating CAD and parametric 3D models
   (text-to-CAD, OpenSCAD/CadQuery code generation, execution- and
   visual-feedback self-correction loops, benchmarks and datasets).
2. What failure modes are **measured**, with what frequency?
3. Which of those does my current skill set already mitigate, and which not?
4. Which guardrail patterns have **evidence** of reducing them — verification-
   first prompting, executable specifications, constraint checking, program
   repair loops, self-consistency? Rank by demonstrated effect size where
   reported.

## C. Output format

Lithuanian, same conventions as before. Structure:

1. **Pataisos** — A1–A4, each with the corrected result and its source.
2. **Q5 / Q6 / Q7** — one section each, ending in a concrete adopt / ignore /
   defer recommendation with cost accounting.
3. **Atnaujintas prioritetų sąrašas** — if A1–A4 or Q5–Q7 change the ranking
   from your previous summary table, give the revised table; say so explicitly
   if nothing moved.
4. **Šaltiniai** — resolvable links, source-type labels, DOIs for papers.
5. **Kas lieka nepatikrinta** — anything still resting on inference, with the
   specific command, measurement, or source that would settle it.

Keep the honesty discipline from your last answer: `neatsakyta — reikia
patikrinti X būdu` is an acceptable and useful answer. A confident guess is not.
