# 03 — Module API (kit v0)

## Conventions

- Units: **mm**. Angles: degrees.
- Coordinate system: `+Z` up, `+X` right, `+Y` back.
- **Every module's local origin is the centre of its bottom face** (`[0,0,0]`), except `boss`
  (origin at the centre of its base) and `snap_hook` (origin at the centre of the mounting base).
- Module name: `kit_<name>`; file `kit/<name>.scad`.
- Every module:
  1. `assert()`s impossible parameters **with a number and a suggestion**;
  2. provides `function kit_bbox_<name>(...)` → `[w, d, h]`;
  3. never calls `translate()` with a "magic" number — only values derived from parameters.
- A module **cannot** print `// EXPECTED_*` — OpenSCAD cannot write comments into a file. The
  generator writes the declarations using the same `kit_bbox_<name>` formula (Python mirror). If
  the two formulas disagree, `check_dimensions.py` catches it.

## `requirements.json` schema

```json
{
  "version": 1,
  "kind": "plate_with_holes",
  "params": { "w": 80, "d": 50, "t": 6, "hole": "M4", "inset": 8 },
  "assumptions": ["plate bolted to an MDF shelf, load ~2 kg"],
  "source": { "brief": "shelf bracket 80x50", "date": "2026-11-01" }
}
```

| Field | Required | Meaning |
|---|---|---|
| `version` | yes | always `1` |
| `kind` | yes | one of the 8 module names, or `custom` |
| `params` | yes | object keys = module parameters |
| `assumptions` | no | list; every unconfirmed assumption |
| `source.brief` | yes | the original user sentence |
| `source.date` | yes | ISO date |

**Rule:** if a parameter is absent and cannot be reasonably defaulted, the generator returns it in
the `missing` list and **writes no file** (exit 4).

## Modules

| Module | Parameters (required in bold) | bbox | Declarations |
|---|---|---|---|
| `plate` | **w, d, t**, corner_r, chamfer | `[w,d,t]` | BBOX |
| `plate_with_holes` | **w, d, t, hole, inset**, corner_r, pattern | `[w,d,t]` | BBOX, THROUGH_HOLES=4 (corners) |
| `bracket_l` | **w, d, h, t, hole** | `[w,d,h]` | BBOX, THROUGH_HOLES=2, **HOLE ×2 (Z and Y axes)** |
| `box` | **w, d, h**, wall, floor, corner_r | `[w,d,h]` | BBOX, THROUGH_HOLES=0 |
| `lid` | **w, d**, t, lip, clearance, wall, corner_r, hole, inset | `[w,d,t+lip]` | BBOX, THROUGH_HOLES=0 (or 4 with `hole`) |
| `boss` | **d_out, d_bore, h** | `[d_out,d_out,h]` | BBOX, HOLE, THROUGH_HOLES=1 |
| `hole_pattern` | **nx, ny, dx, dy, hole, t** | `[nx*dx, ny*dy, t]` (2026-11-01 fix, see below) | BBOX, THROUGH_HOLES=nx*ny |
| `snap_hook` | **beam_l, beam_w, beam_t, hook_h, undercut** | `[beam_w,beam_t,beam_l]` | BBOX |

`hole` accepts `"M3"`, `"M4"`, `"M5"`, `"M6"` (clearance holes from the table below) or a number (mm).

> **Message format.** The `assert` lines below state the *condition* and *what the message must
> say*. The full message must follow `docs/05_tests_and_errors.md` §Format:
> `KLAIDA: <number with unit> → <number> < <limit> → <suggestion>`.
> Example, first `plate` assert:
> ```openscad
> assert(t >= 1.2, str("KLAIDA: storis ", t, " mm → ", t, " < 1.2 mm (FDM minimumas) → didink t iki 1.2"));
> ```
> Messages are Lithuanian (user-facing); the format is fixed.

## 1. `plate`

Rectangular plate with optional corner rounding. **Never** takes a `translate` from the caller.

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| `w` | number | — | width X |
| `d` | number | — | depth Y |
| `t` | number | — | thickness Z |
| `corner_r` | number | 0 | corner radius (0 = sharp) |
| `chamfer` | number | 0 | top-edge chamfer |

`assert`:
1. `t >= 1.2` → "thickness {t} mm < 1.2 mm (FDM minimum); increase t"
2. `corner_r * 2 < min(w, d)` → "corner_r {r} too large for {w}×{d}; max {min/2}"
3. `corner_r >= 0 && chamfer >= 0 && chamfer < t`

## 2. `plate_with_holes`

Corner holes, centred by `inset` measured from the edge to the hole **centre**.

| Parameter | Type | Default | Meaning |
|---|---|---|---|
| `w, d, t` | number | — | as `plate` |
| `hole` | string/number | — | M3/M4/M5/M6 or Ø mm |
| `inset` | number | — | edge-to-centre distance |
| `corner_r` | number | 0 | corner rounding |
| `pattern` | string | `"corners"` | `"corners"` (4) or `"corners6"` (6) |

`assert`:
1. `hole_d > 0` (guard) → "hole {hole} unknown; use M3..M6 or Ø"
2. `hole_d >= 3.0 && hole_d <= 6.5` → "hole {hole} = Ø{d} mm; supported 3.0–6.5"
3. `inset >= hole_d/2 + 2.0` → "inset {i} mm leaves {wall} mm of wall (< 2.0); increase inset to {min}"
4. `2*inset + hole_d <= min(w, d)` → "holes {hole} with inset {i} do not fit {w}×{d}"
5. `t >= 1.2` → as `plate`
6. `corner_r * 2 < min(w, d)` → as `plate`

> Note: the earlier assert `hole_d <= 0.5*min(w,d)` was removed — it is logically implied by 3 and 4.
> A dead assert is decoration, not protection (`docs/10` §4).

Declarations: `// EXPECTED_BBOX: [w,d,t]`, `// EXPECTED_THROUGH_HOLES: 4`.

## 3. `bracket_l`

Two plates (horizontal `w×d×t`, vertical `w×t×h`) joined in an L.
**One hole per leg** (horizontal — through Z, vertical — through Y), matching the real brief
"with a hole in both legs" (P5, 2026-11-01).

| Parameter | Type | Default |
|---|---|---|
| `w` | number | — |
| `d` | number | — |
| `h` | number | — |
| `t` | number | — |
| `hole` | string/number | — |

`assert`:
1. `hole_d > 0` (guard) → "hole {hole} unknown"
2. `t >= 2.5` → "L-bracket thickness {t} < 2.5 mm; will not carry the load"
3. `h > t + 2` → "vertical leg {h} too low for {t} thickness"
4. `hole_d + 2*2.0 <= min(w, d)` → "hole Ø{d} does not fit {w}×{d} with a 2 mm wall"
5. `hole_vz - hole_d/2 >= t + 2.0` → "vertical-leg hole does not fit h; increase h"

Declarations: `// EXPECTED_BBOX: [w,d,h]`, `// EXPECTED_THROUGH_HOLES: 2` and **two `EXPECTED_HOLE`**:

```openscad
// EXPECTED_HOLE: [0, -d/2 + hole_d/2 + 2, t/2, "Z", hole_d]        // horizontal leg
// EXPECTED_HOLE: [0, d/2 - t/2, h - (hole_d/2 + 2), "Y", hole_d]  // vertical leg
```

Without them the gates cannot see **which plane** a hole is in (P5 bug: both horizontal —
`THROUGH_HOLES` and `BBOX` still match, so it passes).

## 4. `box`

Open-top box (enclosure body).

| Parameter | Type | Default |
|---|---|---|
| `w, d, h` | number | — |
| `wall` | number | 2.4 |
| `floor` | number | 2.4 |
| `corner_r` | number | 0 |
| `hole` | string/number | `""` — corner screw boss bores (M3..M6 / Ø); `""` = none |
| `inset` | number | 0 — edge-to-centre distance (when `hole` is given) |

`assert`:
1. `wall >= 1.2` → "wall {wall} < 1.2 mm"
2. `2*wall < w && 2*wall < d` → "walls {wall}×2 do not fit {w}×{d}"
3. `floor >= 1.2 && floor < h` → "floor {floor} must satisfy 1.2 ≤ floor < h={h}"
4. `corner_r >= 0 && corner_r*2 < min(w, d)` → "corner_r {r} does not fit {w}×{d}"
5. `hole = "" || 3.0 <= hole_d <= 6.5` → "hole = Ø{d}; supported 3.0–6.5"
6. `hole = "" || inset >= hole_d/2 + 2.0` → "box inset leaves {wall} mm of wall"
7. `hole = "" || 2*inset + hole_d <= min(w,d)` → "box holes with inset do not fit {w}×{d}"

Declarations: `// EXPECTED_BBOX: [w,d,h]`, `// EXPECTED_THROUGH_HOLES: 0` (or `4` + four `EXPECTED_HOLE` when `hole` is given).

### 4b. `box_with_lid` (composite 2-part enclosure)

Generates `parts/box.scad`, `parts/lid.scad`, `assembly.scad` and `joints.json` from a single `requirements.json` (`w, d, h` + optional `wall, floor, corner_r, lid_t, lip, clearance, hole, inset`).

## 5. `lid`

Lid with an inner lip that enters the box with `clearance`.

| Parameter | Type | Default |
|---|---|---|
| `w, d` | number | — |
| `t` | number | 3 |
| `lip` | number | 1.8 |
| `clearance` | number | 0.2 |
| `wall` | number | 2.4 |
| `corner_r` | number | 0 (must match `box` `corner_r`) |
| `hole` | string/number | `""` — corner screw holes (M3..M6 / Ø); `""` = none |
| `inset` | number | 0 — edge-to-centre distance (when `hole` is given) |

`assert`:
1. `clearance >= 0.15` → "gap {c} < 0.15 mm; FDM parts will not assemble"
2. `lip >= 1.0` → "lip {lip} < 1.0 mm — the lid will not hold"
3. `t >= 1.6` → "lid thickness {t} < 1.6 mm"
4. `wall > 2*clearance` → "wall {wall} too thin for gap {clearance}"
5. `lip_outer > 2*wall` → "lip too small for walls {wall}×2"
6. `corner_r*2 < min(w,d)` → "corner_r {r} does not fit {w}×{d}"
7. `hole = "" || 3.0 <= hole_d <= 6.5` → "hole = Ø{d}; supported 3.0–6.5"
8. `hole = "" || inset >= hole_d/2 + 2.0` → "inset leaves {wall} mm of wall"
9. `hole = "" || 2*inset + hole_d <= min(w,d)` → "holes with inset do not fit {w}×{d}"

Declarations: `// EXPECTED_BBOX: [w,d,t+lip]`, `// EXPECTED_THROUGH_HOLES: 0` (or `4` when `hole` is given).

## 6. `boss`

Boss (standoff) with a central bore.

| Parameter | Type | Default |
|---|---|---|
| `d_out` | number | — |
| `d_bore` | number | — |
| `h` | number | — |

`assert`:
1. `(d_out - d_bore)/2 >= 1.5` → "wall {(d_out-d_bore)/2} < 1.5 mm"
2. `d_bore >= 2.0` → "bore Ø{d_bore} < 2.0 mm"
3. `h >= 2.0` → "boss {h} < 2.0 mm"

Declarations: `// EXPECTED_BBOX: [d_out,d_out,h]`, `// EXPECTED_HOLE: [0,0,0,"Z",d_bore]`.

## 7. `hole_pattern`

Grid of `nx × ny` holes.

| Parameter | Type | Default |
|---|---|---|
| `nx, ny` | int | — |
| `dx, dy` | number | — |
| `hole` | string/number | — |
| `t` | number | — |

`assert`:
1. `hole_d > 0` (guard) → "hole {hole} unknown"
2. `nx >= 1 && ny >= 1 && nx*ny >= 2` → "a grid needs at least 2 holes"
3. `dx >= hole_d + 2*2.0` → "spacing dx {dx} < Ø{d}+4 mm"
4. same for `dy`
5. `hole_d <= 0.5 * min(nx*dx, ny*dy)` → "hole Ø{d} too large for the grid"

Declarations: BBOX, `// EXPECTED_THROUGH_HOLES: nx*ny`.

> **2026-11-01 contract fix.** The original bbox formula was
> `[(nx-1)*dx+hole_d, (ny-1)*dy+hole_d, t]`, which made the holes **tangent** to the plate edge
> (0 mm wall → non-watertight mesh, `topology=FAIL`, genus −4). Assert 4 uses `nx*dx` — the same
> cell count. Agreed contract: plate = `nx*dx × ny*dy`, holes at **cell centres**, wall
> `(dx − hole_d)/2 ≥ 2 mm`.

## 8. `snap_hook`

Cantilever snap hook.

| Parameter | Type | Default |
|---|---|---|
| `beam_l` | number | — |
| `beam_w` | number | — |
| `beam_t` | number | — |
| `hook_h` | number | — |
| `undercut` | number | — |

`assert`:
1. `beam_t >= 1.2` → "beam {beam_t} < 1.2 mm"
2. `undercut <= 0.3 * beam_t` → "undercut {u} > 30 % of the beam ({0.3*beam_t}); will snap"
3. `hook_h >= undercut + 0.5` → "hook needs hook_h ≥ undercut + 0.5"
4. `beam_l >= 4 * beam_t` → "beam too short ({beam_l} < 4×{beam_t}) — no spring"
5. `hook_h < beam_l` (guard) → "the hook is taller than the beam"

Declarations: BBOX.

## `custom()` — escape hatch

When a part does not fit the 8 modules:

```openscad
// REQUIRED: hand-written declarations, otherwise the gates will reject it
// EXPECTED_BBOX: [..]
// EXPECTED_THROUGH_HOLES: N
custom() { /* free coordinates */ }
```

The generator **does not generate** `custom` — it returns `unsupported_kind` and asks a human.
That is a deliberate boundary: an honest "I cannot" beats a silent guess.

## Hole table

| Mark | Ø mm |
|---|---|
| M3 | 3.4 |
| M4 | 4.5 |
| M5 | 5.5 |
| M6 | 6.6 |

Source: ISO 273 medium clearance. **Changing it requires a decision record.**

## Example: a full generated file

```openscad
// GENERATED: gen/emit_part.py from examples/bracket_80x50.json
// kind: plate_with_holes
include </abs/path/kit/lib.scad>
include </abs/path/kit/plate_with_holes.scad>

// EXPECTED_BBOX: [80, 50, 6]
// EXPECTED_THROUGH_HOLES: 4

$fn = 64;
kit_plate_with_holes(w = 80, d = 50, t = 6, hole = "M4", inset = 8, corner_r = 5, pattern = "corners");
```

**Why includes are absolute:** the generator writes `include <$KIT/...>` so the generated file works
from `out/`, from `/tmp/genkit_test/` (docs/05 `run_all.sh`) and regardless of where `openscad` is
started. The `kit/` directory can be overridden with `--kit-root` (default: the project's `kit/`).
Module files include each other with a relative `include <lib.scad>`.

**boss** additionally gets `// EXPECTED_HOLE: [0, 0, 0, "Z", d_bore]` (docs/03 §6).
