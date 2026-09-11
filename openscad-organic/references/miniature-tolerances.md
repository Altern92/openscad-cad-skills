<!-- RAG-passport: file=references/miniature-tolerances.md | skill=openscad-organic | applies_to=[miniature, detail-minimum, nozzle, supportless] | units=mm | printer=FDM | version=2026-09-11 | source=06_RAG_taisykles (T2) -->
# Miniature tolerances (FDM, verified practice)

| Nozzle | Min wall | Min feature | Min gap | Layer (faces) |
|---|---|---|---|---|
| 0.4 | 0.6 | 0.5 | 0.3 | 0.1-0.12 |
| 0.2 | 0.3 | 0.25 | 0.15 | 0.06-0.08 |
| resin | 0.2 | 0.1 | 0.05 | 0.025-0.05 |

- Supportless: overhangs <= 45 deg from vertical; limbs along own axis.
- skin() pitfalls: profiles same winding; method="distance" on count change;
  slices>=8; refine>=10-12; NEVER self-intersecting (cryptic CGAL).
- sweep pitfalls: path smooth (bezier N>=32); profile smaller than path curvature radius.
- $fa/$fs globally, never $fn; $preview ? 12 : 72 pattern.
- Details live in XY plane (slicer resolution); orient figure accordingly.
- minkowski() grows objects — lock with resize() (constrain pattern).
- convexity >= 2 for folded/holed preview correctness.
- Adeptus-dad lesson: OpenSCAD compile times explode on dense nurb/VNF —
  keep profiles coarse, refine only at export; small flair is hard, budget time.
