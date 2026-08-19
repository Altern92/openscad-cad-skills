# Mechanics & Motion Planning Stage

> **When to apply**: Any assembly where parts move relative to each other — rotation, translation, flexure, or constrained rolling/sliding. This stage plans the mechanism, declares it in a machine-readable manifest, and verifies it through automated checks that catch failures visual inspection cannot.

**Sources cited in this document** (see Source Journal below for details):
- 3D printed fits/clearances: [AON3D Engineering Fits](https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/), [The Virtual Foundry Moving Parts](https://thevirtualfoundry.com/3d-print-moving-parts/), [Creative3DP Press Fit Calculator](https://tools.creative3dp.com/tools/press-fit-calculator/), [FTC Wiki Tolerances](https://www.ftcwiki.org/manufacturing-and-assembly/machining/tolerances)
- NopSCADlib vitamins/BOM: [NopSCADlib GitHub](https://github.com/nophead/NopSCADlib), [DeepWiki NopSCADlib](https://deepwiki.com/nophead/NopSCADlib/4-component-library-(vitamins))
- LLM CAD generation/verification: [CADCode-Verify ICML 2025](https://huggingface.co/papers/2410.05340), [CAD-Coder VLM](http://arxiv.org/pdf/2410.05340)
- LLM reliability patterns: [BeFailProof AI Agent Reliability](https://befailproof.ai/guides/how-to-make-ai-agents-reliable/), [n8n Restrict Agent Actions](https://blog.n8n.io/make-ai-agents-more-reliable-and-restrict-the-actions-they-can-take/)

---

## 1. Motion Taxonomy

The skill must know what moves before it can verify it. This taxonomy defines every type of relative motion the skill recognizes, what must be planned for each, and which geometry rules apply.

### 1.1 Rotation

| Subtype | Description | What Must Be Planned | Geometry Rules |
|---------|-------------|---------------------|----------------|
| **Gear pair (spur/helical/bevel)** | Two meshing gears, external (opposite rotation) or internal (same direction) | Axis of each gear, center distance, teeth count, module/pressure angle, backlash, drive direction sign | • Center distance = `(T1+T2)*module/2` for standard spur (exact); use `gear_dist()` from BOSL2 once profile shift applies<br>• External mesh: one gear's ratio is **negative** in motion manifest<br>• Internal mesh: same-direction rotation (both positive)<br>• Backlash ≥ 0.1mm for FDM at module ≥ 1.0 |
| **Lever/arm pivot** | Rigid body rotates about fixed pin/bearing | Pivot axis, pin diameter, arm length, angular travel range, stops (mechanical or soft) | • Pin bore clearance per fit table (§2)<br>• Stops modeled as separate geometry if physical<br>• Travel envelope cleared against all static parts via `motion_sweep.py` |
| **Hinge** | Two bodies rotate relative to each other around shared pin | Hinge axis, pin length/diameter, leaf thickness, angular range | • Pin interfaces with both leaves (two clearances)<br>• Pin extends beyond leaf interface by ≥ 1mm on each end (retention)<br>• No undercuts that trap pin during assembly |
| **Knob/dial** | User-operated rotary input | Axis, grip diameter, travel limits, detent locations (if any) | • Grip clearance from surrounding parts ≥ 5mm (finger space)<br>• Detent notches modelled as negative space in mating part |

### 1.2 Translation

| Subtype | Description | What Must Be Planned | Geometry Rules |
|---------|-------------|---------------------|----------------|
| **Slider-on-track** | Linear motion along a rail, groove, or shaft | Track axis, travel distance, guide geometry (rail, v-slot, round bar), end stops | • Rail clearance per fit table (§2)<br>• Slider width > track width by ≤ clearance allowance<br>• End stops positioned at declared travel limits<br>• Anti-rotation feature (flat, key, D-shape) if rotation must be prevented |
| **Rack-and-pinion** | Rotating pinion drives linear rack | Pinion axis, rack path, module match, teeth engagement zone, travel range | • Pinion module = rack module (verified by `assert()`)<br>• Rack centerline offset from pinion axis = pinion pitch radius<br>• Engagement arc sufficient to cover full travel<br>• Backlash same rule as gear pairs |
| **Lead screw/threaded rod** | Rotary input → linear output via thread | Screw axis, pitch, nut travel, lead angle, thrust bearing support | • Nut bore matches screw OD minus thread depth<br>• Thread depth subtracted from nut ID vs. screw OD<br>• Thrust face perpendicular to screw axis (checked via normal vectors) |

### 1.3 Constrained Rolling/Sliding

| Subtype | Description | What Must Be Planned | Geometry Rules |
|---------|-------------|---------------------|----------------|
| **Bearing on shaft** | Ball or roller bearing rides on rotating shaft | Bearing bore Ø, shaft OD, shaft shoulder, axial retention method, seal clearance | • Bore/shaft fit: transition or light press (ISO k6/K7 typical)<br>• Shaft shoulder ≥ bearing inner ring width for axial seating<br>• Outer race clearance in housing per fit table (§2), loose fit (J7/H7)<br>• Use NopSCADlib `ball_bearing(type="608")` etc. for real dimensions — verified source: [NopSCADlib vitamins](https://github.com/nophead/NopSCADlib/blob/main/vitamins/ball_bearings.scad) |
| **Pin-in-slot** | Pin translates within elongated slot (constrains two degrees of freedom, allows one) | Slot axis, slot length, pin Ø, travel range, slot edge clearance | • Slot width = pin Ø + clearance (slip fit)<br>• Slot ends rounded to pin radius (or larger) to avoid corner snagging<br>• Pin retention (cotter, snap ring, press fit) modelled or declared in narrative (§0.6) |
| **Worm gear** | Worm shaft drives worm wheel at ~90°; self-locking | Worm axis, wheel axis, centre distance, worm leads, wheel tooth count, lead angle | • Axes orthogonal (verify dot product = 0)<br>• Centre distance derived from worm/wheel pitch diameters<br>• Self-locking if lead angle < friction angle (~6° for PLA/PLA) — declare in narrative whether lock is intended |

### 1.4 Flexure

| Subtype | Description | What Must Be Planned | Geometry Rules |
|---------|-------------|---------------------|----------------|
| **Living hinge** | Thin section of material bends repeatedly | Hinge thickness, bend radius, cycle life estimate, material choice | • Thickness 0.6–1.0mm for PLA (cycle life ~10K)<br>• Bend radius ≥ 3× thickness to avoid surface cracking<br>• Stress concentration at transition filleted ≥ 0.5mm |
| **Cantilever beam** | Printed element deflects under load (clip, latch, spring tab) | Beam length/width/thickness, max deflection, yield stress of material, load direction | • Tip deflection δ = PL³/(3EI) — check δ < allowed<br>• Root fillet radius ≥ 1mm to delay crack initiation<br>• Declare expected cycles in narrative (§0.6) — flexures fail by fatigue, not geometry |

### 1.5 Combined Mechanisms

When multiple types combine (e.g., a lever driving a slider via a pin-in-slot):
- Each joint gets its own entry in the motion manifest
- A **dependency graph** (part A's rotation → part B's translation) is recorded so the change-propagation tree knows which parts recalculate when a dimension upstream changes

---

## 2. Mechanical Checks Pipeline for Printed Moving Assemblies

### 2.1 Clearance Per Fit Type (FDM Reality)

These clearances are measured on **printed parts**, not CAD models. The skill adjusts parameters in params.scad to compensate for known FDM error layers.

| Fit Type | CAD Gap (mm) | Print Reality Adjustment | Notes |
|----------|-------------|-------------------------|-------|
| **Press fit** | −0.10 to −0.25 (interference) | Add −0.05mm (total interference slightly higher due to surface roughness) | Shrinkage increases effective interference. Elephant foot on outer diameter makes press-in easier at the entry but harder to seat fully. Test print mandatory. |
| **Transition fit** | 0.00 to +0.05 | No adjustment (CAD gap ≈ functional gap) | For bearing outer races in printed housing: tight enough to prevent spin, loose enough to seat by hand. ISO J7/H7 nominal. |
| **Slip fit (light)** | +0.15 to +0.25 | Add +0.05mm (layer lines reduce effective gap) | Minimum reliable sliding clearance for PLA at 0.2mm layer height. Source: [FTC Wiki — structural backlash adds ~0.1mm on top of nominal clearance](https://www.ftcwiki.org/manufacturing-and-assembly/machining/tolerances). |
| **Slip fit (loose)** | +0.30 to +0.50 | No adjustment needed | For pins in slots, fast-moving sliders. Layer lines and slight warping have minimal effect at these gaps. |
| **Running clearance** | +0.50 to +1.00 | No adjustment | Shaft rotating in printed journal bearing. Surface finish dominates — smooth bore requires printing on-curve (circle in XY plane, not vertical). |

**FDM error layers** that modify theoretical clearances:

| Error Source | Effect on Clearances | Compensation |
|--------------|---------------------|--------------|
| **Shrinkage** (cooling) | Dimensions smaller than CAD by ~0.2–0.5% depending on material | Calibrate with test cube; adjust all critical bores upward by measured bias |
| **Elephant foot** (first layer squeeze) | First-layer OD larger than CAD by ~0.1–0.3mm | Reduce first-layer height; for press fits on cylindrical bases, reduce CAD OD by elephant-foot amount |
| **Layer lines** (stair-stepping) | Effective bore diameter oscillates ±0.1× layer_height | Print circular bores in XY plane (horizontal), not vertical. If vertical bore unavoidable, add +0.1mm to CAD diameter per 0.2mm layer height |
| **Nozzle diameter tolerance** | All features biased toward smaller internal / larger external by up to ±0.025mm | Calibrate nozzle actual vs. nominal; adjust global clearance in params.scad |

Calibration profiles (per printer/material/settings) should be stored and loaded by `doctor.py` — see `openscad-cad/references/confidence-tiers.md`. Without calibration, the skill uses conservative defaults from the table above and flags `PATIKRINTI` on every fit dimension.

### 2.2 Interference Detection Pipeline

**Static pose** (already implemented):
1. Render every part positioned via `MODE="part"` (see SKILL.md §5)
2. Run `check_collisions.py --min-clearance X --expected-contacts joints.json`
3. Verdicts: **pass** (gap ≥ min-clearance or declared contact in range), **degraded** (non-watertight mesh, can't measure), **fail** (undeclared overlap or gap too small)

**Dynamic sweep** (motion_sweep.py):
- Triggered when the design manifest contains a `motion` block (see §3)
- Sweeps each driver through its declared range at the given step resolution
- Gear periodicity collapse: if all drivers are revolute with tooth counts that share a common period, sweep collapses to **one tooth pitch** (e.g., 18° for 20-tooth gear instead of 360°) — 20× speedup
- Adaptive refinement: after coarse pass identifies the tightest pair/position, re-samples ±5° around that point at half the step size
- Exempt contacts (press fits) declared in `joints.json` are skipped
- Output: worst-case clearance value and the position where it occurs

**Making motion_sweep automatic**: The trigger is the existence of a `motion` block in the design manifest (`design_manifest.json`, see §3). `validate_scad.sh --all` already auto-discovers `joints.json`; extending it to also look for `design_manifest.json.motion` and launch `motion_sweep.py` is a single conditional in the shell script. The motion block supplies everything needed: axes, ranges, ratios (with correct signs for opposite-rotation meshes), and tooth counts for periodicity detection.

**Limitation**: Sampling, not proof. A clash narrower than the step interval can hide between samples unless it falls within the refinement window. Lower `--step-deg` before finalizing a design. Never widen `min_clearance` to make a failure disappear.

### 2.3 Bearing Fits & Shaft Alignment

Standard bearings (608, 608ZZ, 6000, 6001, etc.) are modelled using NopSCADlib vitamins — real dimensional data, not placeholder cylinders. Confirmed working: [ball_bearings.scad in NopSCADlib](https://github.com/nophead/NopSCADlib/blob/60659a43f8cc5e0acc10ca7c513ba626754ee924/vitamins/ball_bearings.scad) provides exact OD, ID, width, and shoulder geometry.

**Fit checks** (applied automatically once the bearing vitamin is positioned):

| Check | Method | Threshold |
|-------|--------|-----------|
| **Bore-to-shaft** | Measure shaft OD vs. bearing ID (nominal) | Transition: 0.00 to +0.01mm gap at CAD; compensates to light interference after print |
| **Outer race-to-housing** | Measure housing pocket ID vs. bearing OD | Loose: +0.10 to +0.20mm gap at CAD (printed hole shrinks; target ~+0.05mm effective) |
| **Shaft shoulder** | Distance from bearing seat face to shoulder vs. bearing inner ring width | Shoulder contact ≥ 0.8 × inner ring width |
| **Axial retention** | Snap ring, pressured outer race, or threaded lock present? | Verified by presence of retaining geometry OR declared in §0.6 narrative |
| **Concentricity** | Bore center vs. shaft center (both extracted from mesh) | Offset < 0.05mm |

**Shaft alignment across multiple bearings**:
- Co-linearity of bore axes (multiple bearings on one shaft): cross-product of axis direction vectors must be < 0.01 (nearly parallel).
- Distance between bore axes measured at midpoints: < 0.1mm for acceptable misalignment.
- Checked automatically when the design manifest declares a `shaft` entity spanning multiple bearing positions.

---

## 3. Design Manifest (JSON) — motion block schema

The design manifest (`design_manifest.json`) lives next to `layout.scad` and is the **single source of truth** for what moves, how, and with what clearances. When it exists, the mechanics pipeline runs automatically — `validate_scad.sh --all` auto-discovers it (single conditional in the shell script, same pattern as the existing `joints.json` discovery).

### 3.1 Top-level structure

```json
{
  "$schema": "scad-modeler-motion-v1",
  "assembly_name": "string",
  "parts": ["drivewheel.scad", "idler.scad", "chassis.scad"],
  "purchased_components": [
    { "name": "608ZZ bearing", "qty": 4, "bore_mm": 8, "od_mm": 22, "width_mm": 7 }
  ],
  "shafts": [
    { "id": "main_shaft", "diameter_mm": 8, "material": "stainless_steel_8mm" }
  ],
  "motion": []
}
```

### 3.2 Motion block — one entry per degree of freedom / kinematic pair

```json
{
  "id": "m001",
  "type": "rotation",                       // "rotation" | "translation" | "flexure"
  "subtype": "gear_pair",                   // see taxonomy in §1
  "driver": {
    "part": "drivewheel.scad",
    "axis": { "origin": [0, 0, 0], "direction": [0, 0, 1] },
    "range": { "min_deg": -180, "max_deg": 180, "continuous": true },
    "teeth": 20
  },
  "driven": {
    "part": "idler.scad",
    "axis": { "origin": [30, 0, 0], "direction": [0, 0, 1] },
    "ratio": -0.5,                          // negative = opposite rotation (external mesh)
    "teeth": 40
  },
  "clearance_mm": 0.15,
  "fit_type": "slip_light"                  // from fit table §2.1
}
```

Key fields for automation: `axis` (motion_sweep rotation center), `range` (sweep limits; `continuous` collapses to one tooth pitch when all drivers are revolute), `ratio` with correct sign (periodicity + drive direction checks), `teeth` (periodicity detection), `fit_type` (picks the clearance class from §2.1 for the `min_clearance` argument).

For combined mechanisms (§1.5), add a `drives` array linking joint ids so the change-propagation tree knows part A's rotation feeds part B's translation:

```json
{ "id": "m003", "type": "translation", "subtype": "slider_on_track", "drives": ["m001"], "...": "..." }
```

### 3.3 Trigger wiring

- `motion_sweep.py` runs when `design_manifest.json` contains a non-empty `motion` array (mirror of how `check_collisions.py` triggers on `joints.json` presence).
- `check_collisions.py` static pose is always a precondition of the sweep (same ordering rule as `validation_decision_tree.md`: sweep over static geometry that already collides is meaningless).
- Failure of any mechanical check short-circuits: fix at source, re-run `validate_scad.sh --all` from the top.

---

## Šaltinių žurnalas

| ID | Teiginys | Šaltinis (URL) | Tipas | Data | Būsena |
|---|---|---|---|---|---|
| M-001 | FDM tarpų (press/transition/slip/running) klasės ir korekcijos | https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/ ; https://tools.creative3dp.com/tools/press-fit-calculator/ | pirminis | 2026-08-19 | su šaltiniu |
| M-002 | Slip tarpas ~0.1mm padidėja dėl struktūrinio backlash; slankiojimo tarpai | https://www.ftcwiki.org/manufacturing-and-assembly/machining/tolerances | pirminis | 2026-08-19 | su šaltiniu |
| M-003 | Judančių spausdintų dalių poveikis (trintis, tarpai, dizaino taisyklės) | https://thevirtualfoundry.com/3d-print-moving-parts/ | pirminis | 2026-08-19 | su šaltiniu |
| M-004 | NopSCADlib vitaminų (guoliai, varžtai) realūs matmenys + BOM | https://github.com/nophead/NopSCADlib ; https://deepwiki.com/nophead/NopSCADlib/4-component-library-(vitamins) | pirminis | 2026-08-19 | su šaltiniu |
| M-005 | Vizualus patikrinimas nepakankamas; verifikacijos kilpa gerina CAD generavimą (CADCode-Verify) | https://huggingface.co/papers/2410.05340 | pirminis | 2026-08-19 | su šaltiniu |