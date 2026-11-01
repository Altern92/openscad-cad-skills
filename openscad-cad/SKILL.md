---
name: openscad-cad
description: 'Drive OpenSCAD directly from the CLI to write, render, visually verify, and export parametric 3D models — without opening OpenSCAD''s GUI. Use whenever the user mentions OpenSCAD, .scad files, parametric CAD, Gridfinity bins/baseplates/inserts, enclosures, brackets, or wants a "3D printable part," even if they just describe dimensions and don''t name the tool. Also use this skill when the user wants to modify an existing .scad file, generate STL/3MF for 3D printing, or batch-generate several sizes of the same design. ALSO USE when the user asks to delete/remove a part, change a joint/magnet interface, rename a module, or archive obsolete versions — §4.6 impact analysis (dependents + callers + archive-first) is mandatory before any such change. MULTI-PART assemblies (2+ interacting parts that must fit: racks, gearboxes, enclosures with panels): ALSO load the scad-modeler skill — it adds gated planning, engineering calculations before geometry, and automated validation; openscad-cad alone is NOT enough there.'
---

# OpenSCAD CAD Skill

Write the model as OpenSCAD code, render a PNG, look at it, fix, and export STL/3MF only
once it is right — all through the CLI. Reasoning, caveats and incident history behind
every rule here: `references/workflow_details.md` (same section numbers). Which skill to
load, where a fact lives: `references/retrieval.md` (sibling `claude_skills/references/`).

## 0. Check installation

```bash
openscad --version || which openscad
```

- macOS: `brew install --cask openscad@snapshot` (the plain `openscad` cask is 2021.01 and
  cannot parse current libraries). Check `which openscad` afterwards.
- Debian/Ubuntu: `sudo apt-get install -y openscad xvfb`; prefix every PNG command with
  `xvfb-run -a` on headless Linux (never on macOS).

## 1. Core workflow

1. **Write** a `.scad` file with every key dimension as a named variable at the top.
2. **Render a PNG with `--render`** and look at it. Compiling proves syntax, not shape.
3. **Iterate** until it looks right, then **export**.

The render is a sanity layer, never a gate: it catches a missing feature or a part in
the wrong place, not a wrong dimension. Anything dimensional needs a number — an
`assert()` in the model, or `validate_scad.sh` (§4.5).

## 2. Commands

```bash
openscad --render -o preview.png --imgsize=1200,900 --autocenter --viewall --projection=ortho model.scad
# internal structure (dividers, pockets): top, front, iso
openscad --render -o preview_top.png   --imgsize=1000,1000 --camera=0,0,0,0,0,0,300  --projection=ortho model.scad
openscad --render -o preview_front.png --imgsize=1000,1000 --camera=0,0,0,90,0,0,300 --projection=ortho model.scad
openscad --render -o preview_iso.png   --imgsize=1200,900  --autocenter --viewall    model.scad
openscad -o output.stl --export-format=binstl model.scad     # binary STL
openscad -o output.3mf model.scad
openscad -o output.stl --export-format=binstl -D 'bin_width=3' -D 'label="Screws"' model.scad
```

- Without `--render` the PNG is the F5 preview, which can misdraw subtractions.
- `--camera=tx,ty,tz,rx,ry,rz,dist`; raise `dist` if the model is clipped.
- Add `--backend=Manifold` to render/export on the snapshot build (much faster); check
  `openscad --help | grep -i backend` first.
- On the 2026.06.12 snapshot `is_undef(X)` returned `true` even with `-D X=...`. If a `-D`
  flag seems ignored after 2 tries, pass the value as a module argument or make a separate file.

## 3. Gridfinity

Use **gridfinity-rebuilt-openscad** (kennetek); never hand-write Gridfinity math.

```bash
find ~ -maxdepth 6 -type d -name 'gridfinity-rebuilt-openscad' 2>/dev/null | head   # reuse a clone (git pull)
git clone https://github.com/kennetek/gridfinity-rebuilt-openscad.git                # only if none
sed -n '1,80p' gridfinity-rebuilt-bins.scad    # the CURRENT variable names; they drift
```

- Invoke only the entry points, from inside the clone: `gridfinity-rebuilt-bins.scad`,
  `gridfinity-rebuilt-baseplate.scad` (also `-lite`, which still uses `style_lip`, and
  `gridfinity-spiral-vase.scad` for vase mode). Never edit or `-D` into `src/`.
- Parameter tables: `references/gridfinity-params.md`.
- Custom compartments: `bin_translate()` + `compartment_cutter()` inside `bin_render()`,
  sizes via `cgs()`; there is no `cut()`/`cut_move()`. Copy patterns from the
  `// ===== EXAMPLES ===== //` block at the bottom of `gridfinity-rebuilt-bins.scad`.

```bash
cd gridfinity-rebuilt-openscad
openscad --backend=Manifold -o ../my-bin.stl --export-format=binstl \
  -D 'gridx=2' -D 'gridy=3' -D 'gridz=4' -D 'gridz_define=0' -D 'divx=2' -D 'divy=3' \
  -D 'scoop=1' -D 'style_tab=1' -D 'include_lip=true' -D 'magnet_holes=true' gridfinity-rebuilt-bins.scad
```

Clearances: `references/tolerances.md`. Reusable geometry: `references/patterns.scad`.

## 4. Threads (threads-scad)

`git clone https://github.com/rcolyer/threads-scad.git`, then `use <threads.scad>` (not
`include`). Modules: `ScrewHole(outer_diam, height, ...) { children }`,
`ScrewThread(...)`, `ClearanceHole(...)`, `CountersunkClearanceHole(...)`,
`MetricBolt/MetricNut/MetricWasher`, `RodStart/RodEnd/RodExtender`. Check parameter order
in `threads.scad`. Internal threads print from M2; external M3 is fragile; M4+ is
reliable — warn the user about load-bearing threads at M3 or below.

## 4.5 Checking a part numerically

One validation path, from the part's directory (scripts live in the `scad-modeler` skill):

```bash
bash .../scad-modeler/scripts/validate_scad.sh part.scad
```

- Read its `CHECK_RESULT` and `COVERAGE` lines. Report the part done only after a run on
  its current content. Exit 2 (`NOT VERIFIED`) is not a pass.
- `CHECK_RESULT env=FAIL`: stop, show the `ENV_FAIL:` lines, fix
  (`bash .../scad-modeler/scripts/setup_env.sh`).
- Never run `check_dimensions` / `check_features` by hand instead.
- Declare in the `.scad` file (`declarations=FAIL` without the first two, or write
  `// NO_BBOX: <why>` / `// NO_THROUGH_HOLES_CHECK: <why>`):

```openscad
// EXPECTED_BBOX: [40, 20, 15]
// EXPECTED_THROUGH_HOLES: 1
// EXPECTED_HOLE: [0, 0, 5, "Z", 8.0]     // optional: x, y, z, axis, diameter
```

- Measuring an STL yourself: `.../scad-modeler/scripts/stl_extent.py`, never an inline parser.
- Printability (advisory, judge each finding):
  `$(bash .../scad-modeler/scripts/resolve_python.sh --print) .../scad-modeler/scripts/check_printability.py --stl build/part.stl`
- Fit-critical hole (press fit, bearing, insert, snap) and no calibration profile:
  **propose a calibration coupon first** (`calibration_coupon()`, `references/patterns.scad`
  Pattern 5). Use `true_hole()` (Pattern 0) for round fit-critical holes.
- Name the confidence tier in the final response (`references/confidence-tiers.md`).

## 4.6 Impact analysis before any design change (mandatory)

Before deleting a part, changing a joint/pocket interface, or renaming a module:

1. **Dependents**: `grep -rn '^use\|^include' scad/`
2. **Callers**: `grep -rn '<module_name>' scad/`
3. **Show the list to the user** before executing.
4. **Archive first**: move superseded `.scad`/`.stl` to `archive/` in the same step. Nothing is deleted outright.

## 5. Output conventions

- One project folder per design; shared library clones stay siblings.
- Hand back the `.scad` source, at least one `--render` PNG, and the exported STL/3MF with
  a viewer command — stills hide interpenetration and Z-collapsed views mislead.
- Descriptive file and variable names once final; a short `README.md` per project: what it
  is, the exact commands, which dimensions are confirmed vs estimated.
- Before declaring done, check the result against the user's stated dimensions.
- Something actually went wrong this session (bug, false pass, wrong claim): append an
  entry to `../INCIDENTS.md`.

## Reference files

- `references/workflow_details.md` — full text behind every section above.
- `references/retrieval.md` (sibling `claude_skills/references/`) — skill routing.
- `references/gridfinity-params.md` — bin/baseplate `-D` tables.
- `references/confidence-tiers.md` — what each tier may promise.
- `references/tolerances.md` — per-side clearances from real parts.
- `references/patterns.scad` — `true_hole()`, `calibration_coupon()`, pocket/sleeve/duct modules.
- `../INCIDENTS.md` — append-only bug log shared with scad-modeler.
