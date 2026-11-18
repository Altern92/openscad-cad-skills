# P24 Surinkimo kinematika ir statinis stiprumas (AC, 2026-11-18)

Kilmė: P23 (`check_behavior.py`) patikrina, kad dalys liečiasi, nesikerta ir stovi, bet ne fiziką:
- ESP32 RC priekinė ašis: viršutinio rutulinio šarnyro pasvirimas 22.8°, o pirktas antgalis
  (RC4WD Z-S0398) realiai leidžia apie ±15° (◇ įvertis, gamintojas nenurodo).
- 13 įvorių skylių Ø4.6 = įvorės rifliavimo OD (CNC Kitchen / ruthex: 4.0, spausdintai CAD 4.2),
  gylis 5.7–6.5 < 6.7. Joks vartas to nepagavo.
- Kūnas, laikomas vienu rutuliniu šarnyru, „laikosi“ pagal P23 (tarpas ≤ 1 mm), nors realiai laisvai sukasi.

Vartotojas 2026-11-18: „daryk ... kad nebekabėtų kažkur ore ir nepažeistų fizikos“.
Tyrimas: vault `Research/Runs/2026/2026-11-18-surinkimo-fizikos-patikra-openscad-skill-ui-dof-stiprumas-si.md`.

Tier: feature. Architektūra: plečiamas `check_behavior.py` (tie patys renderiai ir pozos) + naujas
`check_strength.py` (vartai `strength`). Ne simuliacija: momentinis Jakobianas ir analitinė sija.

## behavior.json papildymai

```json
"joints": [{"a": "upright", "b": "cup_u", "type": "ball", "at": [52.1, 18.0, 71.5],
            "max_gap": 0.3, "why": "stud in the cup",
            "angle": {"echo": "ub_mis", "max_deg": 15, "source": "RC4WD Z-S0398, no datasheet value: estimate"}}],
"dof": {"count": 2, "why": ["BUMP", "STEER"], "idle": [{"body": "tie_rod", "why": "spins about its own axis"}]}
```
`type`: `fixed` | `ball` | `revolute` | `slider` (`axis` būtina dviem paskutiniams). Be `type` = `fixed`.

## AC

**Laisvės laipsniai (DOF)**
- AC-1: Given joints with `type` and `at`, when the check runs at the first pose, then it builds the
  instantaneous constraint Jacobian (ball 3 rows, revolute 5, slider 5, fixed 6; static bodies have no
  twist) and prints `DOF: computed N, declared M` where N = 6 × moving bodies − rank (SVD, tol 1e-9 × max σ).
- AC-2: Given N > `dof.count` + len(`dof.idle`), then FAIL names the body (or bodies) that can still move,
  taken from the Jacobian's null space (a body held only by one ball joint is named).
- AC-3: Given N < declared, then FAIL "mechanism locked: declared motion impossible".
- AC-4: Given a joint `at` farther than its `max_gap` from either body's mesh at the first pose, then FAIL
  (the anchor point cannot be invented away from the geometry).
- AC-5: Given `dof` absent while any joint has `type`, then FAIL "declare dof"; given no joint has
  `type`, the DOF block prints SKIP with a hint (old behavior.json files keep passing).

**Šarnyrų ribos**
- AC-6: Given a joint `angle` with `echo: VAR`, when the check runs, then it evaluates VAR through
  OpenSCAD (`echo` at each pose of the grid) and FAILs with the pose when |value| > `max_deg`;
  the worst value per joint is always printed.
- AC-7: Given `angle` without a non-empty `source`, or an `echo` variable OpenSCAD does not print, then
  exit 4 → FAIL (never a silent pass).

**Įvorės (strength gate, part level)**
- AC-8: Given `fasteners.json` entry with `"insert": "M3x5.7"` (table in `references/inserts.json`:
  M2, M2.5, M3, M4, M5 — hole, OD, length, min wall, source CNC Kitchen/ruthex), when the check runs,
  then it measures the hole in the `into` part along the screw axis: diameter (from the mesh ring
  probe) must be within [hole − 0.1, hole + 0.15], blind depth ≥ length + 1.0 (or the hole goes through),
  wall around the knurl OD ≥ min wall; each miss is FAIL with the measured value.
- AC-9: Given the RC model before the fix (Ø4.6), the check FAILs; after `ins_hole = 4.2`,
  `ins_depth = 6.7` it PASSes (fixture copies both).

**Statinis stiprumas (strength gate, load cases)**
- AC-10: Given `loads.json` case `{"part", "support": [x,y,z], "at": [x,y,z], "force_N": [...],
  "print_up": [0,0,1], "material": "PETG"}`, when the check runs, then it slices the part's positioned
  mesh at 10 stations between support and load, computes I and c of each section polygon and the bending
  stress σ = M·c/I, and FAILs when σ × safety (default 2.0) > allowable.
- AC-11: Allowable stress depends on layer direction: when the section normal is within 30° of
  `print_up`, use the inter-layer (Z) value; materials table `references/materials.json` with sources
  (PETG, PLA, ABS, ASA, PA-CF); unknown material → exit 4.
- AC-12: Given a section that splits into 2+ polygons or is empty at a station, then FAIL "load path
  broken at station k" (a part that does not connect support to load cannot carry it).

**Laidai ir neigiami atvejai**
- AC-13: `validate_scad.sh --all` prints `CHECK_RESULT strength=PASS|FAIL|SKIP`; SKIP when neither
  `insert` nor `loads.json` is declared, with a hint line. Rule R-25: applies when `fasteners.json` has an
  insert-like `into` (or `loads.json` exists), success `strength=PASS`.
- AC-14: Fixtures (each FAIL case proven to fail): single-ball-held body FAIL / two-ball+tie PASS;
  locked four-bar FAIL; angle over limit FAIL / within PASS; insert Ø4.6 FAIL / Ø4.2 PASS; shallow
  insert FAIL; thin arm σ over limit FAIL / thick PASS; Z-loaded layer FAIL where XY passes.
- AC-15: Mutants in `tests/mutants.tsv` for both checkers; suite green in dev and installed.
- AC-16: Applied to front_axle_v4, rear_axle_v4, vehicle_v4: DOF declared (front: BUMP, STEER, tie-rod
  idle per side), ball angle limits with sources, inserts declared, landing load case 3 g on each arm.
  Whatever FAILs is reported to the user before any geometry change.
- AC-17: Docs: SKILL.md §0.6 table, `references/validation.md`, templates `loads.json` and
  `behavior.json` updated; `design_constraints.md` line "insert hole = knurl OD".

Ne apimtyje: dinamika (MuJoCo), FEA, nuovargis, šliaužimas, trintis.
