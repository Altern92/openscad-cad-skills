---
name: openscad-cad
description: Drive OpenSCAD directly from the CLI to write, render, visually verify, and export parametric 3D models — without opening OpenSCAD's GUI. Use whenever the user mentions OpenSCAD, .scad files, parametric CAD, Gridfinity bins/baseplates/inserts, enclosures, brackets, or wants a "3D printable part," even if they just describe dimensions and don't name the tool. Also use this skill when the user wants to modify an existing .scad file, generate STL/3MF for 3D printing, or batch-generate several sizes of the same design.
---

# OpenSCAD CAD Skill

Write the model as OpenSCAD code, render it to a PNG, actually look at the PNG,
fix what's wrong, and only export STL/3MF once the render looks right. The whole
loop runs through the CLI — the human never has to open the OpenSCAD GUI, though
they can if they want to tweak the `.scad` file by hand afterward.

## 0. Check installation

```bash
openscad --version || which openscad
```

If missing on macOS, install the **`openscad@snapshot`** cask, not the plain `openscad`
cask. As of this writing Homebrew's `openscad` cask is pinned to the 2021.01 stable
release, which is both flagged deprecated (fails macOS Gatekeeper, scheduled for
removal) and too old to even parse current-generation libraries like
gridfinity-rebuilt-openscad (they use newer OpenSCAD language syntax such as trailing
commas in argument lists). `openscad@snapshot` tracks the actively-maintained nightly
and is what you actually want:

```bash
brew install --cask openscad@snapshot
```

This places the binary on PATH automatically (Homebrew casks link their `Binary`
artifact into the prefix's `bin/` at install time) — confirm with `which openscad`
rather than assuming a manual symlink step is needed; only add one by hand
(`ln -sf /Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD "$(brew --prefix)/bin/openscad"`)
if `which openscad` comes up empty after install.

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y openscad
```

On headless Linux (containers/servers, no attached display), OpenSCAD still needs a
display context to rasterize PNGs even in CLI mode — install Xvfb:

```bash
sudo apt-get install -y xvfb
```

Then prefix every PNG-producing command with `xvfb-run -a` (shown below). This is a
Linux-only concern — never wrap macOS commands in `xvfb-run`; macOS renders through
Cocoa and just needs a normal logged-in session. STL/3MF-only exports (no PNG) don't
need a display on either platform, since they're pure geometry export, not a viewport
capture — but running everything through the same render step keeps the workflow simple.

## 1. Core workflow

1. **Write** the model as a `.scad` file — the editable source of truth. Put every
   key dimension (width/depth/height, wall thickness, divider count, hole sizes...)
   as a named variable at the top of the file, so the file stays a true parametric
   template instead of a one-off. This also makes step 4's `-D` overrides possible.
2. **Render a preview PNG** and look at it before doing anything else. Don't assume
   the geometry is correct just because it compiled without errors — compilation
   only checks syntax, not whether the shapes ended up where you meant them to.
3. **Iterate**: adjust variables/code, re-render, re-view, repeat until it's right.
4. **Export final geometry** (STL for printing) only once the preview looks right.

**How much to trust step 2.** Looking at the render catches gross mistakes —
wrong proportions, a missing feature, a part in the wrong place — and that is
worth doing every time. It is not evidence that dimensions are correct. A
literature check (2026-08) found no benchmark measuring how well a
vision-language model detects wrong dimensions, interference, or missing
internal features from rendered views; the CAD benchmarks that exist
(CADPrompt, Text2CAD-Bench, CadBench, MUSE) measure *generation*, not
*inspection*, and the one measured visual-feedback repair loop, CADCodeVerify,
moved accuracy 64.6% → 68.2% — real but small. Treat the render as a sanity
layer, never as a gate. Anything dimensional needs a number: an `assert()` in
the model, or the STL-side checks in the `scad-modeler` skill
(`check_dimensions.py` for the envelope, `check_features.py` for bores).

## 2. Commands

Fast preview render (uses the OpenCSG preview path — same as pressing F5 in the
GUI; quick, but boolean operations like subtracted holes or divider cuts can render
misleadingly, e.g. showing overlapping faces that aren't really there):

```bash
openscad -o preview.png --imgsize=1200,900 --autocenter --viewall --projection=ortho model.scad
```

Add `--render` for a full geometry evaluation (same as F6) whenever the model has
subtractions, unions of overlapping solids, or anything with internal structure —
this is what you actually want to eyeball before trusting the shape, since preview
mode is only a rough approximation of the final CSG result:

```bash
openscad --render -o preview.png --imgsize=1200,900 --autocenter --viewall --projection=ortho model.scad
```

On headless Linux, wrap it:

```bash
xvfb-run -a openscad --render -o preview.png --imgsize=1200,900 --autocenter --viewall --projection=ortho model.scad
```

Render multiple angles for real QA (top, front, iso) — do this for anything with
internal structure like dividers or pockets, since a single iso view hides a lot:

```bash
openscad --render -o preview_top.png   --imgsize=1000,1000 --camera=0,0,0,0,0,0,300   --projection=ortho model.scad
openscad --render -o preview_front.png --imgsize=1000,1000 --camera=0,0,0,90,0,0,300  --projection=ortho model.scad
openscad --render -o preview_iso.png   --imgsize=1200,900  --autocenter --viewall     model.scad
```

(`--camera=tx,ty,tz,rx,ry,rz,dist` is the Euler-angle form: translate, rotate, then
distance. Adjust `dist` if the model is clipped or too small in frame.)

Export the final STL (binary — much smaller than the ASCII default, which is why
`--export-format` needs to be stated explicitly rather than left to the default):

```bash
openscad -o output.stl --export-format=binstl model.scad
```

Export 3MF (no `--export-format` needed — selected by the `.3mf` extension):

```bash
openscad -o output.3mf model.scad
```

Override top-level variables from the CLI without editing the file — useful for
generating several sizes from one template. Quote string values on both the shell
and OpenSCAD side, e.g. `-D 'label="Screws"'`:

```bash
openscad -o output.stl --export-format=binstl \
  -D 'bin_width=3' -D 'bin_depth=2' -D 'bin_height=6' -D 'divider_count=4' \
  model.scad
```

On the `openscad@snapshot` build, pass `--backend=Manifold` on render/export
commands — it's dramatically faster than the default CGAL backend (a bin render
that takes several seconds under CGAL can drop to well under a second), which
matters a lot when you're iterating render→look→adjust in a loop. Confirm the
flag is present with `openscad --help | grep -i backend` before relying on it —
older builds don't have it.

## 3. Gridfinity work specifically

Don't reinvent Gridfinity math by hand. Use the community-standard parametric
library **gridfinity-rebuilt-openscad** (by kennetek) — it already implements
correct 42 mm grid units, 7 mm height units, magnet/screw holes, scoops, labels,
and baseplates, and is the de facto standard the ecosystem expects:

### 3.1 Setup

```bash
git clone https://github.com/kennetek/gridfinity-rebuilt-openscad.git
```

Keep the cloned directory intact and invoke the entry-point `.scad` files from
inside it (or with paths relative to it) — they pull in `src/core/...` via
relative imports, so a copied-out single file will fail with missing-include
errors.

Entry points — the only files to invoke or override params on:
- `gridfinity-rebuilt-bins.scad` — bins/inserts: compartments, dividers, scoops,
  label tabs, magnet/screw holes, lips.
- `gridfinity-rebuilt-baseplate.scad` — baseplates: thin/weighted/skeletonized,
  drawer-fit, magnet holes.

Everything else in the repo (`src/core/...`, `src/helpers/...`) is internal
plumbing the entry points `include`/`use` — don't edit it, and don't override
its internals with `-D`; go through the entry-point variables instead.

The table below was verified against the repo as cloned on 2026-08-09 — this is
a live community project and its variable names/defaults can and do change
between clones. Before trusting the table blind on a fresh clone (or one that's
been sitting around a while), skim the actual current variable block — it's
right at the top of the entry-point file and doubles as the OpenSCAD Customizer
UI, so it's always current with what that copy of the repo actually accepts:

```bash
sed -n '1,80p' gridfinity-rebuilt-bins.scad
```

### 3.2 Parameters and custom cutouts

Key bin parameters (override with `-D`) — verified against `gridfinity-rebuilt-bins.scad`
as cloned 2026-08-09; re-confirm with the `sed` command above before trusting blind, since
this table has already drifted once this week (see caveat above — an earlier version of
this skill had `style_lip` and a `cdivx`/`cdivy`/`c_orientation` cylindrical-grid API that
turned out not to exist in the current source at all):

| Variable | Meaning |
|---|---|
| `gridx`, `gridy` | footprint in 42mm grid units |
| `gridz`, `gridz_define` | height; `gridz_define`: 0=height in 7mm units, 1=internal mm (excl. base+lip), 2=external mm (excl. lip), 3=external mm |
| `half_grid` | half-size grid units; implies `only_corners` |
| `include_lip` | boolean — whether the top stacking lip exists (not a style enum despite older docs/skills saying so) |
| `divx`, `divy` | number of evenly-spaced compartments along each axis; either set to 0 for a solid bin |
| `depth` | override compartment depth in mm; 0 = default |
| `cut_cylinders` | boolean — use one cylindrical pocket of diameter `cd` per division instead of rectangular compartments (there's no separate `cdivx`/`cdivy`; it reuses the `divx`/`divy` grid) |
| `cd`, `c_chamfer` | cylinder diameter / top-rim chamfer, only used when `cut_cylinders=true` |
| `style_tab` | 0=full-width, 1=auto, 2=left, 3=center, 4=right, 5=none |
| `place_tab` | 0=every division, 1=top-left division only |
| `scoop` | 0=off, 1=full finger scoop, other values scale it |
| `only_corners` | magnet/screw holes only at bin corners, not every base unit — saves print time on large bins |
| `refined_holes` | Gridfinity-Refined hole style — incompatible with `magnet_holes` |
| `magnet_holes`, `screw_holes` | add base magnet (6×2mm) / M3 screw cavities |
| `crush_ribs`, `chamfer_holes` | magnet-retention ribs / insertion chamfer on the holes |
| `printable_hole_top` | bridges magnet holes so no slicer supports are needed |
| `enable_thumbscrew` | adds a Gridfinity-Refined M15×1.5 threaded thumbscrew hole per base — built with the vendored `src/external/threads-scad/threads.scad` (see §4 below) |

Custom/uneven compartments — no `cut()`/`cut_move()` (that API is on the project's docs
site but is stale; it's not in the current source). Instead, use `bin_translate()` +
`compartment_cutter()` inside `bin_render()`, with `cgs()` converting base-unit sizes to
mm. The grid origin is the bin's bottom-left corner, 1 unit = 1 base length, and positions
can be fractional:

```openscad
bin_33 = new_bin([3, 3], fromGridfinityUnits(6));
bin_render(bin_33) {
    bin_translate(bin_33, [0, 0])
    compartment_cutter(cgs([1.5, 0.5]), center_top=false);
    bin_translate(bin_33, [1.5, 0])
    compartment_cutter(cgs([1.5, 1]), center_top=false);
}
```

More worked examples (varying-radius cylinders per division, one custom child shape per
division, etc.) are in the `// ===== EXAMPLES ===== //` block at the bottom of
`gridfinity-rebuilt-bins.scad` — read that block directly for copy-paste patterns instead
of reconstructing the API from memory.

For clearance values (how much to add around an item for a given fit) and for
non-Gridfinity-specific reusable geometry patterns (a friction sleeve with a wire
notch, a bent duct via segmented `hull()`, an irregular-contour locating pocket via
`polygon()`+`offset()`), see `references/tolerances.md` and `references/patterns.scad`
— both extracted from real parts built in this project set, not written fresh.

Key baseplate parameters — verified against `gridfinity-rebuilt-baseplate.scad`:

| Variable | Meaning |
|---|---|
| `gridx`, `gridy` | footprint in grid units |
| `style_plate` | 0=thin, 1=weighted, 2=skeletonized, 3=screw-together, 4=screw-together minimal |
| `distancex`, `distancey`, `fitx`, `fity` | drawer-fit: min baseplate size in mm (0=ignore) and where extra slack goes (-1..1 per axis) |
| `enable_magnet` | add magnet cavities (defaults to `true` in this file) |
| `style_hole` | 0=none, 1=countersink, 2=counterbore |
| `d_screw`, `d_screw_head`, `screw_spacing`, `n_screws` | only relevant when `style_plate` is one of the screw-together styles — joins adjacent baseplate tiles with screws instead of relying on friction/magnets alone, useful for large multi-tile layouts |

Two other entry points exist for specific needs — read their own top variable block the
same way before using:
- `gridfinity-rebuilt-lite.scad` — a simpler/faster single-file bin variant; notably it
  *does* still use the old `style_lip` (0/1/2) enum, so don't assume parameter names are
  identical across entry points just because they're both "bins."
- `gridfinity-spiral-vase.scad` — generates a single continuous-wall bin or base for
  slicer vase/spiral mode (near-zero infill, very fast/cheap prints, but no dividers or
  holes in the usual sense). Takes printer-specific params (`nozzle`, `layer`) because
  wall thickness in vase mode is derived directly from extrusion width. Only reach for
  this when the user specifically wants a lightweight vase-mode print, not a normal bin.

Example — a 2×3 bin, 4 height-units tall, six compartments, scooped, magnet holes:

```bash
cd gridfinity-rebuilt-openscad
openscad --backend=Manifold -o ../my-bin.stl --export-format=binstl \
  -D 'gridx=2' -D 'gridy=3' -D 'gridz=4' -D 'gridz_define=0' \
  -D 'divx=2' -D 'divy=3' -D 'scoop=1' -D 'style_tab=1' -D 'include_lip=true' \
  -D 'refined_holes=false' -D 'magnet_holes=true' -D 'screw_holes=false' -D 'printable_hole_top=true' \
  gridfinity-rebuilt-bins.scad
```

A working clone already exists at
`Docs/03_Asmeniniai_projektai/3D_Spausdinimas/gridfinity-rebuilt-openscad/` on
this machine — reuse it (`git pull` first if it's been a while) instead of
re-cloning, and put generated bins in the sibling `Gridfinity_bins/` folder.

Prefer these `-D` overrides (or editing the top variable block of a copy) over
writing Gridfinity geometry from scratch, unless the user explicitly wants a
fully custom implementation.

## 4. Threaded holes and bolts (threads-scad)

Not Gridfinity-specific — reach for this any time a design needs real printed
screw threads (a threaded lid, a bolt-on bracket, a threaded insert cavity)
rather than a plain clearance hole. Gridfinity's own `enable_thumbscrew`
(§3.2) is actually built on this same library, vendored inside that repo at
`src/external/threads-scad/threads.scad` — for non-Gridfinity work, clone it
directly:

```bash
git clone https://github.com/rcolyer/threads-scad.git
```

Include it with `use <threads.scad>`, not `include` — `include` also pulls in
the file's own example/test geometry into your model, `use` just gives you the
modules. Key modules (verify exact parameter order/defaults in `threads.scad`
itself before relying on them — tolerances in particular matter for fit):

- `ScrewHole(outer_diam, height, position, rotation, pitch, ...) { <children> }`
  — cuts an internal threaded hole into children; the usual case for a
  threaded lid or insert.
- `ScrewThread(outer_diam, height, pitch, ...)` — external threads on a rod.
- `ClearanceHole(...)` / `CountersunkClearanceHole(...)` — plain or
  countersunk bolt passthroughs (no threads, for a bolt to pass through).
- `MetricBolt(diameter, length)`, `MetricNut(diameter)`, `MetricWasher(diameter)`
  — printable or reference hardware geometry.
- `RodStart()` / `RodEnd()` / `RodExtender()` — for rods/dowels longer than the
  printer's build volume, joined with threaded couplers.

Per the library's own notes: printed internal threads work fine from M2+;
external M3 threads are print-quality sensitive; M4+ is reliable. Flag this to
the user if they're designing something load-bearing at M3 or below.

## 5. Output conventions

- **Each distinct design gets its own project folder** (e.g.
  `936DH_soldering_station_insert/`, `gridfinity_demo_bin/`), not shared with
  other unrelated designs in one folder — the user has stated this preference
  explicitly. A shared library clone (`gridfinity-rebuilt-openscad/`,
  `threads-scad/`) is not itself "a design" and can stay a sibling shared
  dependency referenced by relative path from each project folder.
- Keep the `.scad` source as the deliverable to hand back for future edits.
- Always include at least one PNG render (rendered with `--render`, not just
  preview) in the final response so the user can see the result without opening
  a slicer.
- Name variables and the file itself descriptively (e.g. `gridfinity_bin_3x2x6.scad`),
  not `model.scad`, once the design is finalized.
- Give each project folder its own short `README.md`: what it is, the exact
  render/export commands used, and — when dimensions came from a photo/caliper
  reading rather than a stated spec — which numbers are confirmed vs. still
  estimated, so a future edit knows what's safe to trust.
- Before declaring a task done, re-check the rendered image against the user's
  stated dimensions — measure against what they asked for, don't just trust that
  the code "looks right" syntactically.

## Reference files

- `references/tolerances.md` — per-side clearance values for common fits (loose
  drop-in, grid-constrained drop-in, friction fit), each sourced from a real part
  in this project set rather than guessed.
- `references/patterns.scad` — Pattern 0 is `true_hole_d()`/`true_hole()`, the
  exact compensation for OpenSCAD's inscribed-polygon hole undersizing; apply it
  to any round fit-critical hole (holes only, never pins). The rest are reusable
  geometry modules (`gridfinity_contour_pocket`,
  `friction_sleeve`/`sleeve_wire_notch`, `bent_duct`) extracted from real parts;
  `use <patterns.scad>` the ones you need. The single-rectangular-pocket case is
  documented there as a snippet rather than a module — it depends on the Gridfinity
  library's own `compartment_cutter()`, which a module defined *inside* patterns.scad
  can't call (confirmed: `use` only exposes a file's own module names to its caller,
  not the caller's other `use`d modules back into that file).
