# 05 — Tests and error format

## Error format (frozen)

Every `assert` message has three parts:

```
KLAIDA: <what is wrong> → <number with unit> < <limit> → <suggestion>
```

**Examples (must match this shape exactly):**

```
KLAIDA: inset 4 mm palieka 1.9 mm sienelę → 1.9 < 2.0 mm → didink inset iki 5.1 arba plotį iki 84 mm
```

```
KLAIDA: storis 1.0 mm → 1.0 < 1.2 mm (FDM minimumas) → didink t iki 1.2
```

```
KLAIDA: undercut 0.8 mm → 0.8 > 0.3×beam_t=0.6 → mažink undercut iki 0.6 arba didink beam_t iki 2.7
```

### Rules

1. Messages are **Lithuanian** (user-facing); numbers carry units (`mm`, `Ø`).
2. Always say **what to do** — never "invalid parameters".
3. No internal variable names without a value.
4. Numbers formatted with 1–2 decimals.

### Where they live

`tests/expected/<mutant>.txt` — **only the message part** (no OpenSCAD `ERROR:` prefix, no file name).
The harness compares with `grep -F`.

## Test structure

```
tests/
├── fixtures/              # 11 good inputs
│   ├── plate.json
│   ├── plate_chamfer.json
│   ├── plate_with_holes.json
│   ├── pwh_corners6.json
│   ├── bracket_l.json
│   ├── box.json
│   ├── lid.json
│   ├── lid_screws.json
│   ├── boss.json
│   ├── hole_pattern.json
│   └── snap_hook.json
├── mutants/               # 40 bad inputs — one per assert
├── expected/              # 40 expected messages
├── p5/                    # P5 runner + brief sets
├── assert_coverage.tsv    # module → assert → mutant → expected text
└── run_all.sh
```

## `run_all.sh` behaviour (4 sections)

1. **Golden** — for each `fixtures/*.json`: emit → gates must end `0 failed, 0 inconclusive`,
   and `dimensions` / `topology` / `features` / `declarations` must be PASS (not SKIP).
2. **Mutants** — for each `mutants/*.json`: emit → `openscad` must **fail** → the output must
   contain the text from `expected/<name>.txt`.
3. **Assembly** — box + lid in assembly mode with `joints.json`; gates must pass (covers
   collisions and the coplanar case).
4. **Gate mutant** (`gm_br_orientation`) — builds a mutated `kit/` where both `bracket_l` holes are
   horizontal, emits, and requires `features=FAIL`. This is the regression guard for the P5 bug:
   `THROUGH_HOLES` and `BBOX` still match, so only the hole declarations can catch it.

Prints `PASS <name>` / `FAIL <name>: <reason>`, ends with `N passed, M failed`, exits 0 only when
`M == 0`.

**Forbidden:** writing into the project directory (only `/tmp/genkit_test/`), network access,
depending on `HOME` state.

## Mutant examples

| Mutant | Module | Changed parameter | Expected message (start) |
|---|---|---|---|
| `plate_t` | plate | `t: 6 → 1.0` | `KLAIDA: storis 1.0 mm` |
| `plate_corner_r` | plate | `corner_r: 8 → 50` | `KLAIDA: corner_r 50.0 per didelis` |
| `pwh_inset` | plate_with_holes | `inset: 8 → 4` | `KLAIDA: inset 4.0 mm palieka` |
| `br_t` | bracket_l | `t: 4 → 2.0` | `KLAIDA: L laikiklio storis 2.0` |
| `box_wall` | box | `wall: 2.4 → 1.0` | `KLAIDA: sienelė 1.0` |
| `lid_clearance` | lid | `clearance: 0.2 → 0.05` | `KLAIDA: tarpas 0.05` |
| `boss_wall` | boss | `d_out: 24 → 13` | `KLAIDA: sienelė 1.25` |
| `sh_undercut` | snap_hook | `undercut: 0.5 → 1.0` | `KLAIDA: undercut 1.0` |

The full mapping is in `tests/assert_coverage.tsv` (40 rows).

## Adding a module (order)

1. `kit/<name>.scad`: `module kit_<name>(...)` + `function kit_bbox_<name>(...)`.
2. `docs/03_module_api.md`: parameter table + numbered `assert` list.
3. `tests/fixtures/<name>.json` + one mutant per assert + `tests/expected/<mutant>.txt`.
4. `tests/assert_coverage.tsv` rows.
5. `gen/emit_part.py`: `KINDS` entry + bbox/through-hole formulas (+ `EXPECTED_HOLE` if the part has
   fit-critical bores).
6. `gen/schema.json`: `$defs/<name>` + the `if/then` branch.
7. `bash tests/run_all.sh` → 54/54.

## Manual commands

```bash
# one module
openscad -o /tmp/x.stl kit/plate.scad

# measured bbox
python3 ~/Skills-plugins-etc/skills/scad-modeler/scripts/stl_extent.py /tmp/x.stl

# through-holes via Euler characteristic
python3 ~/Skills-plugins-etc/skills/scad-modeler/scripts/check_topology.py --stl /tmp/x.stl --scad kit/plate.scad

# full chain on one file
python3 gen/emit_part.py tests/fixtures/bracket_l.json -o /tmp/b.scad
bash ~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh /tmp/b.scad
```
