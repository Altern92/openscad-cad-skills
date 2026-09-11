---
name: openscad-organic
description: 'Model organic high-detail 3D-printable figurines in OpenSCAD — characters, creatures, miniatures with precise small features. Use when the user asks for a figurine, miniature, character, creature, bust, toy figure, or any organic/decorative model that needs smooth curved surfaces and fine details, not just technical brackets or enclosures. ALWAYS load openscad-cad alongside (render/export commands live there); for multi-part articulated figures ALSO load scad-modeler (planning, joints, tolerances, validation).'
---

# OpenSCAD Organic — Figurines and Miniatures

Builds on openscad-cad (§2 render/export commands still apply) and follows
scad-modeler discipline (§0 project facts, calculations before geometry,
validation). This skill adds what neither covers: smooth organic surfaces
and print-safe fine details in a CSG modeler.

**Not sure which skill to load, or where a fact lives? See `../references/retrieval.md` — the routing table (skill choice, passport format, abstention).**

## 0. Before anything else

1. Load openscad-cad (render/export) and, for 2+ interacting parts
   (articulated limbs, head+body+base), scad-modeler (planning, tolerances).
2. Read ../INCIDENTS.md — a logged organic bug never re-read will recur.
3. Require BOSL2 (`use <BOSL2/std.scad>`): skin(), path_sweep(),
   bezier() live there. No BOSL2 — single-hull blobs only, say so honestly.
4. RESEARCH-FIRST for replicas (INCIDENTS 2026-09-09): before modeling a
   real-world object, use agent-reach (Exa/GitHub/web) to fetch REAL
   dimensions + print practice. Never model from one artwork photo alone.
   v1 without research = blockout, not a model.

## 1. Core techniques (use in this order)

### 1.1 Piecewise hull, never single hull (jack rule)
One hull() over all spheres = plastic-wrap box, not organic shape.
Connect CENTER sphere to EACH satellite separately (makerblock jack trick):
```openscad
for (i = [0 : len(pts)-1])
  hull() { sphere_at(center); sphere_at(pts[i]); }
```
Each satellite = one limb joint, muscle bulge, cheek. Concavity survives
because hulls never span the gaps between satellites.

### 1.2 skin() for bodies (profiles, not primitives)
Body = list of 2D cross-sections at heights, connected by BOSL2 skin():
```openscad
use <BOSL2/std.scad>
profiles = [circle profile at z=0, ellipse at z=10, smaller at z=20];
skin(profiles, slices=8, refine=12, method="distance", caps=true);
```
Rules: same winding direction every profile; method="distance" when point
counts differ; slices for smoothness; NEVER self-intersecting (cryptic CGAL).
Head/hands = high-res profiles; torso = fewer.

### 1.3 path_sweep() for limbs, tails, horns
Fixed 2D profile (circle/oval) along a 3D path, ideally a bezier():
```openscad
path = bezier([p0, p1, p2, p3], N=32);
path_sweep(circle(d=4), path);
```
Twist/scale along path for claws, ears, decorative ridges. Limbs print
best along their own axis — orient the sweep, not the slicer.

### 1.4 Details ON the surface, never separate bodies
Eyes, wrinkles, scales, rivets: small hull()/sphere() blobs unioned onto
the skinned surface (adeptus-dad ork-plating pattern: VNF surface →
offset outward → union). Separate floating bodies = slicer artifacts.
Detail minimums (0.4 nozzle): wall >= 0.6, feature >= 0.5, gap >= 0.3.
Below that: 0.2 nozzle or resin — say so, do not fake it.

## 2. Print discipline (FDM)

- Supportless first: angles <= 45 deg from vertical; add Cura/Orca
  "Make Overhangs Printable" only as fallback (visible ramps).
- $fa/$fs globally, never $fn (Wikibooks rendering guide); $preview low,
  full render high: `FN = $preview ? 12 : 72;`
- Details in XY plane (resolution lives there); layer 0.1-0.12 for faces.
- minkowski() for fillets LOCKS final size with resize() (infinityplays
  constrain pattern) — minkowski grows objects, compensate or oversize.
- convexity >= 2 for folded/holed shapes (preview correctness).

## 3. Validation (before STL)

1. Render + LOOK (openscad-cad §2): front, top, iso — gross errors.
2. Manifold NoError + watertight (scad-modeler scripts where present).
3. Dimension check: bounding box vs brief; detail calipers (>= 0.5).
4. Self-intersection hunt: any skin()/sweep added since last render gets
   a solo render first — CGAL errors come from the NEW profile, not old code.

## 4. Output conventions

- One project folder per figure; .scad source is the deliverable.
- PNG renders (--render, not preview) in the final response.
- README: render/export commands, confirmed vs estimated dims.
- Real bug this session -> ../INCIDENTS.md entry before finishing.

## Reference files

- ../references/retrieval.md — routing table: which skill to load, passport format, abstention rule.

- references/organic-patterns.scad — copy-paste: piecewise hull chain,
  skin() body template, sweep limb, detail-on-surface, snap-fit base.
- references/miniature-tolerances.md — FDM detail minimums per nozzle,
  supportless angles, VNF/skin pitfalls (self-intersection, winding).
- ../INCIDENTS.md — shared log with scad-modeler. Read before, append after.
