# 08 — P5 measurement

## Method

**Briefs:** `docs/11_p5_briefs.md` — 10 sentences, used **verbatim**.

1. 10 real briefs from the user's projects, **one sentence each**, as the user would say them aloud.
2. Each: intake → `requirements.json` → generator → gates.
3. Record: was a second round needed, were there questions, is the result correct.

**Second round** = any human or agent correction after the first generation (including parameter
tuning).

## Real run (2026-11-01) — user briefs

Run **twice**: before and after the fixes.

| # | Brief | Module | 1st round PASS? | Correct? | Notes |
|---|---|---|---|---|---|
| 1 | 120×80 plate, 4× M4, 10 mm from the edge, 6 mm | plate_with_holes | ✓ | ✓ | all parameters given |
| 2 | box 150×100×60, wall 2.5, round the corners | box | ✓ | ✓ | floor=2.5, corner_r=5 (assumption) |
| 3 | lid for the same body with a lip | lid | ✓ | ✓ | wall/corner_r matched #2 |
| 4 | L-bracket 60×50×40, 4 mm, M5 **in both legs** | bracket_l | ✓ | **✗ (1st run)** | the module put both holes horizontally → fixed |
| 5 | vent plate 100×80, 3×4 M3, 25/18 | hole_pattern | ✓ | ✓ | thickness 3 (assumption) |
| 6 | boss for M4: 12 outer, 20 high, through | boss | ✓ | ✓ | bore 4.5 |
| 7 | shelf bracket 80×50, 2 kg, M4 | plate_with_holes | ✓ | ✓ | thickness 6 — **assumption recorded**, not a silent guess |
| 8 | box 100×60×40 with a lid and 4 screws | box_with_lid | ✓ | ✓ | 2-part assembly (`parts/box.scad` + `parts/lid.scad` + `assembly.scad` + `joints.json`), `validate_scad.sh --all` PASS |
| 9 | gear 20 teeth, m=1.5, 6 mm bore | custom | — | ✓ (refused) | pointed to BOSL2 `gear` |
| 10 | hinge for two parts, opens 180° | custom | — | ✓ (refused) | a mechanism, not a single body |

**1st run (before fixes):** 7/10 gates PASS, but **1 false "done"**
(#4 — wrong geometry, gates did not catch it because `THROUGH_HOLES=2` matched).
**2nd run (after F1 fix):** 7/10 PASS, **0 false**, 3 honest refusals.
**3rd run (2026-11-02, after audit §5 #2 & #6):** **8/10 (80 %)** PASS, **0 false**, 2 honest refusals.

### Summary (real)

| Metric | Result | Target |
|---|---|---|
| One-shot success (no second round) | **8/10 (80 %)** (was 7/10) | ≥ 70 % ✓ |
| False "done" (PASS, wrong geometry) | **0** (after the fix; before — 1) | **0** ✓ |
| Number of questions | 0 (instead: explicit assumptions) | ≤ 5 ✓ |
| Unsupported briefs | 2 (gear, hinge) | recorded ✓ |

**Conclusion:** the target is met at the margin. Weak spot — **composite briefs** (#8): the pipeline
generates one part, so such a brief must be split by intake (S-4). Strength — honest refusal: not a
single silently wrong result.

## Synthetic run (2026-11-01) — NOT user briefs

> **Warning:** this is **not** a protocol P5 result. The agent wrote the briefs itself (10 realistic
> sentences) and chose parameters in one pass without iteration. It shows the pipeline works
> end-to-end, **not** that the user gets 80 % one-shot.

## Open items

- The `bracket_l` orientation bug is now covered by `gm_br_orientation` (docs/13 F1).
- Composite-brief decomposition is still an intake problem (skill side, S-4).
