# Calculations — single-stage spur reduction

## 1. Calculation table

| Part | Formula | Value | Status |
|------|---------|-------|--------|
| Reduction ratio | spur_teeth / pinion_teeth | 66/11 = 6.00 | OK |
| Center distance | (T1+T2) × module / 2 | (11+66)×1.0/2 = 38.5mm | OK |
| Pinion bore | matches a generic 5mm shaft, no real motor selected | 5mm | ILLUSTRATIVE (no `PATIKRINTI`/verify item — this is a demo, not a real build) |

This example intentionally skips §0.5 Planning and §0.6 Physical assembly
narrative (both apply to real, uncertain-architecture, purchased-hardware
assemblies -- see `scad-modeler/references/planning.md` and SKILL.md §0.6).
A 2-part, single-purpose gear pair with an obvious architecture is exactly
the case SKILL.md names as safe to skip both for.
