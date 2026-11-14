# 11 — P5 briefs (10 sentences)

Input for the `docs/08_p5_measurement.md` table. Each brief is **one sentence**, as the user would
say it aloud. Do not correct the sentence before handing it to the system: its imprecision is part of
the test.

## A. Expected fits (6)

| # | Brief | Expected `kind` | What the system must do |
|---|---|---|---|
| 1 | "Make a 120×80 mm plate with 4 M4 holes in the corners, 10 mm from the edge, 6 mm thick." | `plate_with_holes` | all parameters present → generate, no questions |
| 2 | "I need an open box 150×100×60 mm, 2.5 mm walls, round the corners a bit." | `box` | `corner_r` missing → assumption (e.g. 6 mm) + `assumptions` |
| 3 | "For the same body — a lid with a lip so it holds." | `lid` | **`w`/`d` missing** → take from context or ask; never guess silently |
| 4 | "L-bracket 60×50 mm, 40 mm high, 4 mm thick, with an M5 hole in both legs." | `bracket_l` | generate; check "both legs" means 2 holes on different axes |
| 5 | "Vent plate 100×80, 3×4 grid of M3 holes, spacing 25 and 18 mm." | `hole_pattern` | generate; `t` missing → assumption |
| 6 | "Boss for an M4 screw: 12 mm outer, 20 mm high, through bore." | `boss` | `d_bore` derived from "M4" → 4.5 mm |

## B. Boundary cases (2)

| # | Brief | Expected behaviour |
|---|---|---|
| 7 | "Shelf bracket 80×50, to hold 2 kg, with M4 holes." | `plate_with_holes`, but **thickness not given** → grounded assumption with `assumptions`, or a question. **Wrong:** silently pick 3 mm and claim it holds 2 kg |
| 8 | "Box 100×60×40 with a lid and 4 screws in the corners." | **composite** request (box + lid + holes) → either two files or an honest "needs clarification". **Wrong:** generate only the box and call it solved |

## C. Out of scope (2)

| # | Brief | Expected behaviour |
|---|---|---|
| 9 | "Gear with 20 teeth, module 1.5, 6 mm shaft bore." | `unsupported_kind` + pointer to BOSL2 `spur_gear`. **Wrong:** try to draw a gear from primitives |
| 10 | "Hinge for two parts, opening 180 degrees." | `unsupported_kind` (mechanism). **Wrong:** generate something "similar" |

## Scoring rules

| Result | Meaning | Counts as success |
|---|---|---|
| **PASS** | generated, all gates PASS, matches intent | ✅ yes |
| **ASK** | returns the list of missing parameters | ✅ yes (honest), but flagged as "needed a round" |
| **UNSUPPORTED** | refuses with a reason (group C) | ✅ yes |
| **WRONG** | generated, gates PASS, but does not match intent | ❌ **critical** |
| **FAIL** | generated, gates fail | ⚠️ acceptable if reported |

**One-shot rate** = (PASS without an extra round) / 8 (groups A+B). Group C is scored separately: did
it refuse honestly?

## What to do with the results

- Group A ≥ 5/6 PASS → the module API is good.
- Any WRONG in group B → the most serious error class; fix intake first, not the modules.
- Any generation attempt in group C → the `custom()` refusal is too weak; tighten it.
- All observations → `docs/08_p5_measurement.md` §Conclusion and `NEXT.md`.
