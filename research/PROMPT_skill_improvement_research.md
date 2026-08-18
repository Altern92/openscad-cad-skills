# RESEARCH BRIEF: Academic & state-of-the-art review of two LLM-agent "skills" for parametric 3D CAD (OpenSCAD)

> **Instruction to the answering AI:** You are being asked to perform a deep,
> rigorous, source-backed research review. You have no prior knowledge of this
> project — everything you need is contained in this document, including the
> complete verbatim source of the artifacts under review. Use every research
> method available to you: academic literature search (Google Scholar, arXiv,
> ScienceDirect, IEEE, SpringerLink), engineering standards bodies (ISO, DIN,
> VDI, AGMA, ASME), manufacturer engineering data (SKF, Misumi, KHK gears),
> open-source repository and documentation review (GitHub, OpenSCAD manual,
> BOSL2 wiki), 3D-printing community empirical data, and recent LLM/AI-for-CAD
> research. Where a claim in the material below is empirically testable, say
> how to test it. Prefer primary sources; cite everything with links.
>
> **Answer in Lithuanian** (the requester is a Lithuanian speaker), but keep
> all technical terms, standard designations, library names, code identifiers,
> and citation titles in their original language.

---

## PART 0 — What this is and what I need from you

### 0.1 Background context you need

**Claude Code** is a command-line AI coding agent made by Anthropic. It supports
a mechanism called **Skills**: a folder containing a `SKILL.md` file (Markdown
with a YAML frontmatter header holding a `name` and a `description`), optionally
accompanied by `references/` (extra docs the agent reads on demand), `scripts/`
(executable helpers the agent runs), and `templates/` (starter files the agent
copies).

How a skill works in practice:

- The frontmatter `description` is the **only** part always loaded into the
  agent's context. The agent reads it to decide *whether* the skill is relevant
  to the user's current request. This is called **triggering**, and a badly
  written description means the skill either never fires or fires on unrelated
  tasks.
- Once triggered, the agent reads the full `SKILL.md` body and follows it as
  procedural instructions — it is essentially a **domain-specific standard
  operating procedure written for a non-deterministic reasoning agent**, not
  for a human and not for a compiler.
- `references/` files are read only when `SKILL.md` points to them ("progressive
  disclosure"), which keeps token cost down.
- The agent executes `scripts/` via a shell, so scripts are the only part of a
  skill with **deterministic, verifiable** behaviour. Everything in `SKILL.md`
  is advisory: the model may deviate from it.

**OpenSCAD** is a script-based, code-only parametric solid modeller. The user
writes a `.scad` text file describing solids via Constructive Solid Geometry
(CSG: `union`, `difference`, `intersection`, `hull`, `minkowski`) and
transformations, and OpenSCAD compiles it to a mesh. Key properties that matter
for this review:

- It is a **mesh/CSG** system, not a **B-rep (boundary representation)** system
  like OpenSCASCADE/FreeCAD/SolidWorks. There are no true parametric features,
  no constraint solver, no sketch-based modelling, and no native fillet/chamfer
  operator on arbitrary geometry.
- Curves are polygonal approximations controlled by the special variables
  `$fn` (fixed facet count), `$fa` (min angle per facet) and `$fs` (min facet
  size). This has direct dimensional consequences (see §3.4 below).
- Trigonometric functions take **degrees**, not radians.
- Two include mechanisms exist: `include <f.scad>` (textually pulls in
  everything, including top-level variables and top-level statements) and
  `use <f.scad>` (imports only module/function *definitions*, silently dropping
  top-level variable assignments and top-level statements).
- It has a CLI capable of headless rendering to PNG and export to STL/3MF/OFF/etc.
- Two geometry backends exist: the legacy **CGAL** backend and the much faster
  modern **Manifold** backend.

**3D printing context:** all output here is destined for FDM/FFF desktop 3D
printing (fused filament deposition), typically in PLA/PETG/ABS/ASA, on a
consumer printer with a ~0.4 mm nozzle and ~0.2 mm layer height. The parts are
functional mechanical parts, not decorative.

**Gridfinity** (mentioned throughout) is a popular open-source modular storage
system: a 42 mm × 42 mm grid, 7 mm height units, with standardised baseplates
and stackable bins. `gridfinity-rebuilt-openscad` by *kennetek* is the de-facto
community-standard parametric OpenSCAD implementation of it.

**BOSL2** (Belfry OpenSCAD Library v2) is the largest OpenSCAD library — it adds
an attachment/anchor system (positioning features by named anchors like `TOP`,
`LEFT` instead of hand-computed `translate()` offsets), rounding/filleting
helpers, involute gear generation with automatic profile shift, threading, and
much more.

### 0.2 Who wrote these skills, and how

These two skills were written by an individual hobbyist/maker (not a
professional mechanical engineer) **in collaboration with LLM agents**, and they
are explicitly **experience-derived**: nearly every non-obvious claim in them
was added *after* a real failure happened during a real project. The authoring
style is unusually good about recording *why* something is the way it is, and
about marking claims as verified-on-a-specific-date. The empirical grounding is
therefore genuine but **narrow**: it reflects one person, one machine, one
printer, and a handful of projects — it has not been checked against the
engineering literature, against published standards, or against the wider
open-source tooling ecosystem.

**That gap is exactly what this research task is for.**

### 0.3 What I want from you, concretely

Produce a **structured improvement report** that answers: *how should these two
skills be rewritten, extended, or restructured so that an LLM agent using them
produces mechanically correct, printable, verified parametric CAD more
reliably?*

I am specifically interested in these dimensions:

1. **Interference / collision checking** — how it is done now, what the
   state of the art is, and what the current approach structurally cannot catch.
2. **Dimensional and geometric verification** — how correctness is currently
   established, and what published methods exist to do better.
3. **The engineering calculations themselves** — what the skills compute, what
   standards say they *should* compute, and what is simply missing.
4. **Tolerance and fit data** — the current values are N≈3 anecdotes; what does
   the standards and academic literature actually say for FDM parts.
5. **The tooling and library ecosystem** — what better/complementary tools exist
   that these skills do not know about.
6. **The design of the skills as LLM artifacts** — structure, triggering,
   verifiability, portability, evaluation.

Do not simply agree with the material. Where a stated claim is wrong, outdated,
or over-generalised from a single observation, say so and cite the evidence.

---

## PART 1 — Complete verbatim source of the artifacts under review

There are **two** skills in a git repository (`claude_skills`). They are related:
`scad-modeler` explicitly declares itself as building on top of `openscad-cad`.

```
claude_skills/
├── README.md
├── openscad-cad/
│   ├── SKILL.md
│   └── references/
│       ├── tolerances.md
│       └── patterns.scad
└── scad-modeler/
    ├── SKILL.md
    ├── references/
    │   └── setup-notes.md
    ├── scripts/
    │   ├── validate_scad.sh
    │   ├── check_dimensions.py
    │   └── check_collisions.py
    └── templates/
        ├── part_template.scad
        └── layout.scad
```

The intended division of labour: **`openscad-cad`** handles a *single* part
(an insert, a bracket, a cover, an enclosure, a Gridfinity bin) — write it,
render it, look at it, export it. **`scad-modeler`** handles *multi-part
mechanical assemblies* (gearboxes, drivetrains, anything where parts must mesh
or fit together) and adds mandatory pre-geometry calculations, a centralised
parameter file, a centralised layout/positioning file, and automated
dimensional + collision validation.

Everything below is the **complete, unedited content** of every file.

## FILE SET A — skill `openscad-cad` (single-part workflow)

### A1. openscad-cad/SKILL.md

**Path:** `openscad-cad/SKILL.md`

`````markdown
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
- `references/patterns.scad` — reusable geometry modules (`gridfinity_contour_pocket`,
  `friction_sleeve`/`sleeve_wire_notch`, `bent_duct`) extracted from real parts;
  `use <patterns.scad>` the ones you need. The single-rectangular-pocket case is
  documented there as a snippet rather than a module — it depends on the Gridfinity
  library's own `compartment_cutter()`, which a module defined *inside* patterns.scad
  can't call (confirmed: `use` only exposes a file's own module names to its caller,
  not the caller's other `use`d modules back into that file).
`````

### A2. openscad-cad/references/tolerances.md

**Path:** `openscad-cad/references/tolerances.md`

`````markdown
# Fit tolerances — reference values from real prints

Clearance values that came out of actual fit decisions on real parts in this
project set, not guesses. Use these as starting points instead of re-deriving
a clearance from scratch each time; adjust from here if a specific print
comes back too tight/loose and note the correction back into this table.

| Fit | Clearance | When to use | Source |
|---|---|---|---|
| Loose drop-in / easy removal | **1.5mm/side** | Default for a Gridfinity locating pocket around a rectangular item (tool box, tin) when grid space isn't tight — item lifts out one-handed, no wiggle needed. | `gridfinity_hardware_storage_inserts/insert_B.scad` and siblings (94×128mm tool box pocket) |
| Loose drop-in, grid-constrained | **1mm/side** | Same as above, but the bin's usable infill (grid size × 42mm − 2×0.95mm wall) barely clears the item — e.g. widest point 205mm against a 208.1mm 5-wide bin only leaves ~1.1mm slack at 1mm/side. Drop below 1.5mm only when the grid genuinely can't grow (printer bed limit, existing box count) — verify the resulting slack is still ≥ ~1mm before committing to it, not just "whatever remains." | `helping_hands_base_insert/helping_hands_base_insert.scad` |
| Snug friction fit | **0.5mm/side** | A part that must grip by friction alone (e.g. a sleeve that slides onto a motor body and stays via friction, no screws) — tight enough to resist sliding under normal handling, still loose enough to hand-assemble without a press. | `nema23_fan_shroud/nema23_fan_shroud.scad` (`motor_clearance = 1` — see note) |

Note on the shroud's motor sleeve: that specific part used **1mm/side**, not
0.5mm — an unusually large motor cross-section (57mm) where 0.5mm/side felt
too tight to slide on by hand over the full 60mm sleeve length. Treat 0.5mm as
the starting point for a *short* friction sleeve (under ~20mm of contact
length) and lean toward 1mm/side as the contact length or the mating surface
size grows, since a longer/larger friction fit is much less forgiving of
being even slightly undersized (or slightly warped from printing) than a
short one.

General principles behind all three rows:
- These are all **per-side** (radius/offset) values — double for total
  diametral/gap clearance.
- FDM printing tends to print holes/pockets slightly undersized and
  bosses/pins slightly oversized relative to the model — these values already
  bias toward "loose enough to still work after that," not the theoretical
  CAD-perfect clearance.
- When grid/space is genuinely not a constraint, default to 1.5mm/side and
  only tighten it once a real constraint (bed size, existing layout) forces
  the question — don't preemptively tighten for no reason.
`````

### A3. openscad-cad/references/patterns.scad

**Path:** `openscad-cad/references/patterns.scad`

`````c
// ============================================================
// patterns.scad -- reusable OpenSCAD snippets pulled from real, tested
// parts in this project set (not written from scratch here). Each pattern
// below cites the project it was first solved in. This is a reference
// library, not a standalone model -- `use <patterns.scad>` the specific
// module(s) you need rather than rendering this file directly (it has
// deliberately no unconditional trailing call).
// ============================================================


// ------------------------------------------------------------
// PATTERN 1: single rectangular locating pocket in a Gridfinity bin
// Source: gridfinity_hardware_storage_inserts/insert_B.scad (and C/D/F)
//
// Documented as a snippet, not a module here, on purpose: it's just the
// gridfinity-rebuilt-openscad library's own bin_render() + compartment_
// cutter(), and a wrapper module in THIS file can't call compartment_
// cutter() itself -- confirmed by testing: `use <patterns.scad>` only
// exposes patterns.scad's own module names to the caller, it does NOT
// give patterns.scad access to modules the caller separately use'd (e.g.
// cutouts.scad) -- OpenSCAD resolves a module's body against its own
// file's scope, not the caller's. See references/tolerances.md for the
// clearance value to use.
//
// Usage (inside your insert's own file, after use'ing the gridfinity
// library's utility/bin/cutouts modules and building `bin1` via new_bin()):
//   bin_render(bin1) {
//       compartment_cutter([item_w + 2*clearance, item_d + 2*clearance, pocket_depth],
//                           center_top=true);
//   }
// ------------------------------------------------------------


// ------------------------------------------------------------
// PATTERN 2: irregular-contour locating pocket in a Gridfinity bin
// Source: helping_hands_base_insert/helping_hands_base_insert.scad
//
// For an item whose footprint isn't a rectangle (traced/measured as a
// polygon outline) -- offsets the outline outward by `clearance`, extrudes
// it into a pocket, and centers it on the outline's own bounding-box
// center so it lands in the middle of the bin regardless of where the
// original points were measured from.
//
// `outline` = list of [x,y] points (any consistent origin -- the
// centering math below removes the original offset for you).
//
// Usage:
//   bin_render(bin1) {
//       gridfinity_contour_pocket(outline=base_outline, clearance=1.0, pocket_depth=13);
//   }
// ------------------------------------------------------------
module gridfinity_contour_pocket(outline, clearance, pocket_depth) {
    xs = [for (p = outline) p.x];
    ys = [for (p = outline) p.y];
    center = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2];

    translate([-center.x, -center.y, -pocket_depth])
    linear_extrude(pocket_depth)
    offset(r = clearance)
    polygon(outline);
}


// ------------------------------------------------------------
// PATTERN 3: friction-fit sleeve with a wire/cable exit slot
// Source: nema23_fan_shroud/nema23_fan_shroud.scad
//
// A rectangular sleeve that slides onto a rectangular body (a motor, a
// bracket) and grips it by friction alone -- see references/tolerances.md
// for the clearance/side to use, and its note on friction fits scaling
// with contact length/size. `notch_side` cuts a slot through one wall so
// a cable/wire can exit without being pinched.
//
// Usage:
//   difference() {
//       friction_sleeve(body_w=57, clearance=1, wall=2.5, sleeve_len=60);
//       sleeve_wire_notch(body_w=57, wall=2.5, sleeve_len=60,
//                          notch_side="right", notch_w=16, notch_h=9);
//   }
// ------------------------------------------------------------
module friction_sleeve(body_w, clearance, wall, sleeve_len) {
    inner = body_w + 2*clearance;
    outer = inner + 2*wall;
    difference() {
        cube([outer, outer, sleeve_len]);
        translate([wall, wall, -1])
            cube([inner, inner, sleeve_len + 2]);
    }
}

module sleeve_wire_notch(body_w, clearance, wall, sleeve_len, notch_side, notch_w, notch_h) {
    inner = body_w + 2*clearance;
    outer = inner + 2*wall;
    x = (notch_side == "right") ? outer - wall - 1 : -1;
    translate([x, (outer - notch_w)/2, -1])
        cube([wall + 2, notch_w, notch_h]);
}


// ------------------------------------------------------------
// PATTERN 4: bent duct / tube via segmented hull()
// Source: nema23_fan_shroud/nema23_fan_shroud.scad
//
// A smooth curved tube (e.g. a fan duct that has to bend around an
// obstruction) approximated as N short straight segments, each built by
// hull()-ing two circles at slightly different positions/rotations along
// the arc. This was genuinely non-obvious to derive correctly the first
// time (getting arc_pos/arc_rot wrong gives a duct that kinks or
// self-intersects instead of curving smoothly) -- reuse this rather than
// re-deriving it.
//
// The arc lies in the plane containing the bend axis; as written here it
// curves from "straight out along -X" toward "+Z" as angle increases (the
// original use case: a duct exiting a wall and curving toward the front
// of a motor). For a different bend plane/direction, adjust arc_pos/
// arc_rot's axes the same way you'd re-derive any parametric curve --
// don't just swap axis labels without re-checking in a render.
//
// Call twice to make a hollow duct: once with the outer diameter as a
// solid, once with the inner (air-path) diameter to subtract.
//
// Usage:
//   difference() {
//       bent_duct(start=[0, 32, 30], radius=45, bend_angle=40, d=61, segments=16);
//       bent_duct(start=[0, 32, 30], radius=45, bend_angle=40, d=56, segments=16);
//   }
// ------------------------------------------------------------
function _bent_duct_arc_pos(start, radius, a) =
    start + [-radius*sin(a), 0, radius*(1 - cos(a))];
function _bent_duct_arc_rot(a) = [0, -(90 + a), 0];

module bent_duct(start, radius, bend_angle, d, segments) {
    for (i = [0 : segments - 1]) {
        a1 = i * bend_angle / segments;
        a2 = (i + 1) * bend_angle / segments;
        hull() {
            translate(_bent_duct_arc_pos(start, radius, a1))
                rotate(_bent_duct_arc_rot(a1))
                cylinder(d=d, h=0.02, center=true, $fn=48);
            translate(_bent_duct_arc_pos(start, radius, a2))
                rotate(_bent_duct_arc_rot(a2))
                cylinder(d=d, h=0.02, center=true, $fn=48);
        }
    }
}
`````

## FILE SET B — skill `scad-modeler` (multi-part assembly workflow)

### B1. scad-modeler/SKILL.md

**Path:** `scad-modeler/SKILL.md`

`````markdown
---
name: scad-modeler
description: Use for complex, multi-part parametric OpenSCAD mechanical assemblies — things with gears, bearings, reductions, multiple interacting printed parts, or where getting a dimension wrong means two parts collide or don't mesh. Triggers on "gear ratio", "reduction", "bearing", "shaft", "assembly", "BOM", "center distance", "mechanical design", "RC car", "gearbox", "multi-part", or requests to design several parts that must fit together and be validated, not just a single organizer/bracket. For a single simple part (an insert, a bracket, a cover, a shroud), use the openscad-cad skill instead — this skill's calculation-table + validation overhead is not worth it for those. This skill builds on openscad-cad (§2 render/export commands still apply) and adds: mandatory engineering calculations before geometry, centralized part positions, per-part local coordinates, and automated dimensional/collision validation.
---

# SCAD Modeler — Multi-Part Mechanical Assemblies

For a single self-contained part, use `openscad-cad` directly — this skill is for
assemblies where multiple parts must fit together correctly (gear meshes, bearing
press-fits, shaft alignments), where a wrong number means two parts collide or a
gear pair doesn't mesh, not just "the pocket is 2mm too small."

## 0. Before anything else: read project facts

Check `CLAUDE.md` (project-level, or the specific project folder) for already-decided
facts: motor/component specs, gear ratios, tolerances, design decisions. Don't ask the
user to repeat facts that are already written down. If a needed fact is missing, ask
once rather than guessing — a wrong bearing bore or shaft diameter is not something a
render will catch; it only shows up when the part doesn't fit.

## 1. Calculation table (mandatory, before writing any geometry)

Write a Markdown table before touching OpenSCAD:

| Part | Formula | Value | Status |
|------|---------|-------|--------|
| Stage 1 ratio | driven_teeth / driver_teeth | 66/11 = 6.00 | OK |
| Center distance 1 | (T1+T2) × mod / 2 | (11+66)×1.0/2 = 38.5mm | OK |
| Bearing bore | per datasheet | 10mm | PATIKRINTI |

Mark anything not sourced from a datasheet/spec/prior decision as `PATIKRINTI` (verify)
— don't silently treat a guess as a fact. Resolve every `PATIKRINTI` (ask the user, or
look it up) before moving to step 2. This table becomes part of the final report.

## 2. `params.scad` — all dimensions, one place

One file, at the project root, containing every dimension used anywhere in the
assembly: component specs (motor, bearings, off-the-shelf parts), gear parameters,
tolerances, and everything derived from the calculation table above. Nothing in any
part file should be a bare number that isn't either a genuinely local/cosmetic detail
(a fillet radius on one specific part, say) or traceable back to this file.

Add `assert()` for anything that must hold for the design to make sense — a gear
ratio near a target, a positive wall thickness after clearance is subtracted, a
bearing bore that's actually bigger than the shaft it rides on. This isn't
decoration: `assert()` is a real top-level OpenSCAD statement (confirmed working)
and it stops the render with a clear message instead of silently producing a part
that's subtly wrong.

```openscad
// params.scad
$fa = 2; $fs = 0.3;
global_clearance = 0.2; // mm, general running clearance

// Motor: RS-550S (datasheet)
motor_d = 36; motor_l = 57; motor_shaft_d = 3.175;

// Gearing (module 1.0 throughout)
gear_module = 1.0;                     // NOT `module` -- that's an OpenSCAD keyword
pinion_teeth = 11; spur_teeth = 66;
ratio_1 = spur_teeth / pinion_teeth;
center_distance_1 = (pinion_teeth + spur_teeth) * gear_module / 2;

assert(ratio_1 > 5.5 && ratio_1 < 6.5, "Stage 1 ratio drifted from target ~6:1");
```

## 3. `layout.scad` — where each *part* sits in the assembly

This is for positioning separate, independently-printed parts relative to a shared
assembly coordinate system (e.g. "the motor mount sits 63mm behind the diff
housing") — a different problem from positioning a *feature within* a single part
(a boss on one housing), which is §4's job.

Define the coordinate system explicitly (origin, axis directions) as a comment, then
a lookup table + `at()` module:

```openscad
// layout.scad
include <params.scad>

// Origin: center of rear differential, on axle centerline. X=right, Y=front, Z=up.
LAYOUT = [
    ["rear_diff_housing", [0, 0, 0], [0, 0, 0]],
    ["rear_jackshaft",    [0, -center_distance_1, 0], [0, 0, 0]],
];

function layout_pos(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][1] : layout_pos(name, i+1);
function layout_rot(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][2] : layout_rot(name, i+1);

module at(name) {
    pos = layout_pos(name); rot = layout_rot(name);
    assert(pos != undef, str("Layout entry not found: ", name));
    translate(pos) rotate(rot) children();
}
```

(Verified: this recursive-lookup pattern and the bare `assert()` both run correctly
under the installed OpenSCAD.)

## 4. Part files — local coordinates, no assembly-level transforms

One file per part. Each part is modeled around its own sensible local origin (a
bearing bore center, a mounting face) — never `translate()`/`rotate()` the whole
part inside its own file; that's `layout.scad`'s job via `at()`. State the local
origin and intended print orientation in a comment at the top.

**For features *within* a part** (a boss on a face, a hole on a corner, ribs), prefer
BOSL2's attachment system over hand-computed `translate()` offsets. A full, real
BOSL2 clone is installed at `~/Documents/OpenSCAD/libraries/BOSL2` (verified: 56
`.scad` files including `std.scad`, and `spur_gear()` below was test-rendered
successfully against this install with the project's actual 11-tooth pinion
parameters — see `references/setup-notes.md` for why this needed re-doing: an
earlier, incomplete drop-in of just `gears.scad` alone was there before and
silently failed on missing dependencies):

```openscad
include <BOSL2/std.scad>

cuboid([housing_w, housing_d, housing_h]) {
    attach(TOP) cyl(h=boss_h, d=boss_d, anchor=BOTTOM);       // boss on top face
    attach(TOP+FWD+RIGHT) screw_hole();                        // corner feature
}
```

Named anchors (`TOP`/`BOTTOM`/`LEFT`/`RIGHT`/`FWD`/`BACK`, combinable with `+` for
edges/corners) are less error-prone than recomputing `width/2 - offset` by hand at
every call site. Gotcha: chaining `attach()` calls without a `{ }` block attaches the
second one to the *first child*, not back to the parent — always use the block form
when attaching more than one feature.

See `templates/part_template.scad`.

## 5. Gears: use BOSL2, do not hand-write involute math

**Do not write a custom involute gear generator.** A from-scratch implementation was
tried and tested for this project already — it failed on two separate points: a
parameter literally named `module` (an OpenSCAD reserved keyword — this is a hard
parse error, confirmed), and mixing radians into `tan()`/`cos()`/`sin()`, which in
OpenSCAD always take **degrees** (confirmed: `tan(20)` = 0.364 correct, but
`tan(20*PI/180)` = 0.0061 — wrong by ~60x). Involute tooth geometry is exactly the
kind of math where a subtly wrong angle produces a tooth that *looks* plausible in a
render but doesn't mesh correctly — the failure mode is invisible until you either
measure carefully or print two parts and try to mate them.

BOSL2's `gears.scad` (part of the full install above) has this solved, including automatic
profile-shift correction for low tooth counts (relevant here — an 11-tooth pinion is
exactly the range prone to undercutting without it):

```openscad
include <BOSL2/std.scad>
include <BOSL2/gears.scad>

spur_gear(mod=gear_module, teeth=pinion_teeth, thickness=15,
          shaft_diam=motor_shaft_d, pressure_angle=20, backlash=0.15);
```

Use `gear_dist(mod=gear_module, teeth1=t1, teeth2=t2)` for center distances instead
of the hand-rolled `(T1+T2)*mod/2` formula once profile shift is involved (the plain
formula is fine for equal/standard gears, but stops being exact once BOSL2's
`profile_shift="auto"` kicks in for small tooth counts).

If BOSL2 truly isn't available for some reason, MCAD's `involute_gears.scad` is
another tested option -- but verify it's a complete MCAD install before relying on
it (`~/Documents/OpenSCAD/libraries/MCAD` on this machine currently has only 2 of
MCAD's files present, not a full clone -- check before use, don't assume). Either
way: a tested library beats a fresh implementation, every time, for gear math.

## 6. `assembly.scad` — MODE switch

Import each part file with `use`, **not** `include`. Every part file ends with an
unconditional top-level call to its own module (see §4/template — that's what makes
it render standalone). `include`-ing it into `assembly.scad` runs that call TOO, in
addition to the positioned `at(...)` call below — silently doubling that part's
geometry in the assembly (confirmed by reproducing it: an `include`d part renders
once unpositioned at the origin and once at its real `at()` position; switching the
same line to `use` removes the stray copy, and the part's own internal top-level
variables still resolve correctly inside its module even though `use` doesn't export
them into `assembly.scad`'s namespace — verified both ways with a minimal repro).

```openscad
// assembly.scad
include <layout.scad>
use <parts/rear_diff_housing.scad>
use <parts/rear_jackshaft.scad>

MODE = is_undef(MODE) ? "assembly" : MODE; // set via -D 'MODE="part"' -D 'PART="name"'
PART = is_undef(PART) ? "" : PART;

// Modules aren't values in OpenSCAD, so PART needs an explicit name dispatch --
// there's no way to look a module up by string and call it directly.
module part_by_name(name) {
    if (name == "rear_diff_housing") rear_diff_housing();
    else if (name == "rear_jackshaft") rear_jackshaft();
    else assert(false, str("Unknown part in layout: ", name));
}

if (MODE == "assembly") {
    at("rear_diff_housing") rear_diff_housing();
    at("rear_jackshaft")    rear_jackshaft();
} else if (MODE == "part") {
    at(PART) part_by_name(PART); // e.g. -D 'MODE="part"' -D 'PART="rear_jackshaft"'
} else if (MODE == "exploded") {
    // same as assembly, but with an extra offset per part along its natural axis
}
```

`MODE="part"` is also how you export each part *positioned* in assembly coordinates
for the collision check in §7 — render once per part name with that `-D` pair, not
from the unpositioned part file directly.

Emit a BOM via `echo()` at the end of assembly mode (part name, material, quantity).

## 7. Validation cycle (mandatory, every part and the full assembly)

```bash
bash scripts/validate_scad.sh --all
```

This renders every `.scad` file it finds under `parts/` plus `assembly.scad`,
checks the OpenSCAD install, and fails loudly on an empty STL — see the script for
exact flags (`--hardwarnings`, `--check-parameters=true`,
`--check-parameter-ranges=true` are all confirmed-real flags on the installed
OpenSCAD build, verified via `--help`).

It also runs a **bounding-box check** on any part that declares one, catching
the failure mode visual inspection alone misses: a part that renders and
*looks* right but is subtly the wrong size. Declare it in the part file, next
to the part's own dimension variables:

```openscad
// EXPECTED_BBOX: [40, 20, 15]
```

`validate_scad.sh` greps for that comment and, if present, runs
`scripts/check_dimensions.py --stl <rendered.stl> --scad <part.scad>` — it
compares the actual STL bounding box to the declared one, tolerance
`max(0.3mm, 1% of the expected dimension)` per axis (confirmed: catches a
deliberate 1mm mismatch on a 10mm part, passes an exact match, and passes a
200mm part with mesh-tessellation-scale slack). No `EXPECTED_BBOX` comment =
check is skipped, not required for every part (e.g. an odd shape where a
bounding box isn't a meaningful sanity check on its own).

For assemblies of 3+ parts, also run collision detection — no two parts that
shouldn't touch should overlap in 3D space:

```bash
python3 scripts/check_collisions.py build/*.stl
```

This needs `trimesh`, `python-fcl` (trimesh's `CollisionManager` doesn't do
collision detection itself — it wraps FCL), and `scipy` (trimesh's own mesh
checks need it). All three confirmed necessary by actually running the script —
`pip install trimesh python-fcl scipy` (macOS Homebrew Python needs a venv for
this: `python3 -m venv .venv && source .venv/bin/activate` first, or it'll refuse
with an externally-managed-environment error). Both STL inputs must be watertight
and already expressed in the shared assembly coordinate system (i.e. exported from
`assembly.scad` with each part positioned via `at()`, not from an unpositioned part
file) or the check is meaningless.

Then render a preview and actually look at it, same as always:
```bash
openscad --backend=Manifold --render -o build/preview.png --imgsize=1200,900 --autocenter --viewall assembly.scad
```

Fix any failure at the source (wrong parameter, wrong layout position) — do not
loosen an `assert()` or a collision threshold to make a failure go away.

## 8. Final report

After every check passes, report:
- Files created/changed.
- BOM: part name, material, quantity, key dimensions.
- Critical dimensions carried over from the calculation table (ratios, center
  distances, bearing fits) — these are what the user needs to double check against
  their own understanding of the mechanism.
- Any remaining `PATIKRINTI` items that couldn't be resolved.
- Suggested print orientation per part.

## Reference files

- `scripts/validate_scad.sh` — render/validate every part + assembly, auto-discovers
  files under `parts/` (no manual list to keep in sync); also runs the bounding-box
  check below for any part that opts in.
- `scripts/check_dimensions.py` — compares a rendered STL's bounding box against
  a part's declared `// EXPECTED_BBOX: [x, y, z]`. Needs only `trimesh` (confirmed
  lighter than check_collisions.py — no scipy/python-fcl needed for this one).
- `scripts/check_collisions.py` — trimesh/FCL-based interference check between
  already-positioned part STLs.
- `templates/part_template.scad` — starting point for a new part file, includes
  the `EXPECTED_BBOX` convention.
- `templates/layout.scad` — starting point for a new assembly's `layout.scad`.
`````

### B2. scad-modeler/references/setup-notes.md

**Path:** `scad-modeler/references/setup-notes.md`

`````markdown
# Setup verification notes (2026-08-16)

Facts below were empirically verified against the actual installed OpenSCAD build
and libraries on this machine, not assumed from documentation or a prior model's
(DeepSeek's) claims. Re-verify if any of this changes (new machine, reinstalled
libraries, etc.) rather than trusting this file blindly forever — same principle
as the rest of this skill.

## OpenSCAD CLI flags (confirmed present via `openscad --help`)

`--hardwarnings`, `--check-parameters=true`, `--check-parameter-ranges=true` all
exist and both the space-separated (`--check-parameters true`) and `=`-joined
(`--check-parameters=true`) forms work.

## OpenSCAD language facts (confirmed by running test files)

- A bare, top-level `assert()` statement is valid OpenSCAD and halts the render
  with the given message on failure.
- Recursive user functions (a function calling itself, e.g. a linear-scan lookup
  over an array) work correctly.
- Trig functions (`sin`, `cos`, `tan`, ...) take **degrees**, always. Passing
  radians silently produces wrong-but-plausible-looking numbers rather than an
  error -- e.g. `tan(20)` = 0.364 (correct for 20°) but `tan(20*PI/180)` = 0.0061
  (wrong by ~60x, because 20*PI/180 in radians is being read as if it were degrees).
  This was the root cause of a bug in an earlier hand-written gear module.
- `module` is a reserved keyword and cannot be used as a variable/parameter name --
  doing so is a hard parse error (`Parser error: syntax error`), not a warning.

## BOSL2 / MCAD install status

As of 2026-08-16, a full, working BOSL2 is installed at
`~/Documents/OpenSCAD/libraries/BOSL2` (56 `.scad` files, cloned from
`https://github.com/BelfrySCAD/BOSL2.git`). `spur_gear(mod=1.0, teeth=11,
thickness=15, shaft_diam=3.175, pressure_angle=20, backlash=0.15)` was
test-rendered against it successfully (`--backend=Manifold --render`, no errors,
1384 triangles, correct-looking 11-tooth profile).

**Before that fix**, `~/Documents/OpenSCAD/libraries/BOSL2/` contained only a
single stray `gears.scad` file (not a real BOSL2 install) -- `include
<BOSL2/std.scad>` failed to resolve, and `gears.scad` itself then errored out
referencing undefined things (`CENTER`, `UP`, `first_defined()`, `is_finite()`)
that live in `std.scad`. The folder *existing* and *sharing BOSL2's name* was not
evidence it was a working install -- had to actually `include` it and render
something before trusting it. Renamed the old folder to
`BOSL2_incomplete_backup` rather than deleting it outright.

## Dimension check (`check_dimensions.py`) -- confirmed working (2026-08-16)

Built from a second DeepSeek DeepThinking pass (`05_deepseek_promptas_matmenu_patikra.md`
in the research folder), which this time correctly flagged its one uncertain
claim ("does `openscad --info` report a bounding box?") instead of asserting it.
Checked directly: `openscad --info` only dumps version/environment info, no
geometry bounding box -- confirms STL export + `trimesh` is the only real option,
as DeepSeek defaulted to.

Also verified directly (not just accepted from the DeepSeek response):
- The `EXPECTED_BBOX` regex still matches correctly even with trailing comment
  text after the closing bracket (as used in `part_template.scad`).
- `check_dimensions.py` needs only `trimesh` -- unlike `check_collisions.py`, it
  does NOT need `scipy`/`python-fcl` (tested in a venv with trimesh alone;
  `mesh.bounds`/`mesh.is_empty` don't hit the graph/connected-components code
  path that `is_convex`/`body_count` do).
- Default tolerance (`max(0.3mm, 1%)`) correctly: passes an exact match, fails a
  deliberate 1mm mismatch on a 10mm test part, and passes a 200mm part despite a
  1.5mm difference (within the wider 1%-based tolerance at that size).
- End-to-end: `validate_scad.sh --all` against two parts, one with a deliberately
  wrong `EXPECTED_BBOX` -- correctly failed and halted before validating the
  remaining part (`set -euo pipefail` doing its job).

`~/Documents/OpenSCAD/libraries/MCAD` is in the same incomplete state (only
`gears.scad` and `involute_gears.scad` present, not a full MCAD clone). Not fixed,
since BOSL2 alone already covers this skill's gear needs -- fix it the same way
(`git clone https://github.com/openscad/MCAD.git`) if MCAD is ever actually needed.

## BOSL2 requires `include`, not `use` -- confirmed by reproducing the failure

`use <BOSL2/std.scad>` followed by `cuboid([...]) { attach(TOP) cyl(...); }` fails:

```
WARNING: Ignoring unknown variable "$tags_shown" in .../BOSL2/attachments.scad
ERROR: Assertion '(is_list($tags_shown) || ($tags_shown == "ALL"))' failed
```

Root cause: `use` imports modules/functions only, not top-level variable
assignments -- BOSL2's default special variables (`$tags_shown`,
`$anchor_override`, `$attach_to`, `$transform`, ...) are declared as top-level
assignments in `std.scad`, so `use` silently drops them and `attach()` then
crashes trying to read one. Switching to `include <BOSL2/std.scad>` fixes it
immediately (verified: a `cuboid()` with an `attach(TOP) cyl(...)` boss rendered
correctly, no warnings, right after making that one change).

This is the exact same `use`-drops-top-level-variables behavior already
documented for this project's other OpenSCAD work (see the `openscad-cad` skill,
`nema23_fan_shroud` project) -- worth remembering as a general rule for *any*
OpenSCAD library, not just BOSL2: if a library defines default parameters as
top-level variables (not inside a function/module), it needs `include`, not `use`.
`use` is only safe for libraries whose public API is 100% modules/functions with
no top-level state.

## `use` also skips a file's top-level *statements*, not just variables (confirmed 2026-08-16)

Found while dogfooding this skill end-to-end (see below): `use <file.scad>` does not
execute `file.scad`'s own top-level module-call statements either (e.g. a part
file's trailing unconditional `part_geometry();`), the same way it doesn't import
top-level variable assignments. Confirmed with a minimal repro: a child file with a
top-level variable, a module using that variable, and a stray top-level
`translate(...) cube(...)` junk statement -- a parent that only `use`s the child and
calls its module rendered a mesh with the exact bounding box of the module's own
geometry, sized correctly from the child's internal variable, with no trace of the
junk statement's geometry.

Practical consequence for this skill: `assembly.scad` must `use` its part files, not
`include` them (see SKILL.md §6) -- `include` would also run each part file's own
trailing unconditional render call, silently duplicating that part's geometry on top
of the positioned copy placed via `at()`.

## End-to-end dogfood run (2026-08-16)

Ran the full workflow once, top to bottom, on a synthetic (not real-project) 2-part
gear assembly -- calculation table, `params.scad`, `layout.scad`, two part files
(one with a BOSL2 `attach()` boss, one with a BOSL2 `spur_gear()`), `assembly.scad`
with the MODE switch, `validate_scad.sh --all`, per-part positioned STL export via
`-D MODE="part"`, `check_collisions.py`, and a rendered preview. This was the one
thing the skill had never been run through before, only unit-tested piece by piece.

Findings:
- The `include`-vs-`use` bug above, and the vague `at(PART) children();` line in the
  old §6 (modules aren't values in OpenSCAD -- there's no way to look one up by
  string without an explicit if/else dispatch) -- both fixed in SKILL.md.
- The collision checker caught a real design mistake in the synthetic assembly (a
  gear housing footprint sized too generously for the actual center distance, which
  really did overlap the motor mount) -- fixed at the source per SKILL.md's own
  instruction (shrank the housing margin and mount footprint, recomputed from the
  same params.scad variables) rather than loosening the check, then re-ran clean.
- `gear_dist()` returned a different center distance than the naive
  `(t1+t2)*mod/2` formula would have for the first (12/36-tooth) attempt, a live
  example of why SKILL.md §5 says to use it instead of hand-deriving.
- Everything else (calculation table -> params.scad -> layout.scad -> part files ->
  assembly.scad -> validate_scad.sh -> check_collisions.py -> preview render) worked
  exactly as documented, no other deviations needed.
`````

### B3. scad-modeler/scripts/validate_scad.sh

**Path:** `scad-modeler/scripts/validate_scad.sh`

`````bash
#!/usr/bin/env bash
# Render/validate every part under parts/ plus assembly.scad, in one call.
# Auto-discovers files (globs parts/*.scad) rather than a hand-maintained list,
# so it can't silently skip a part someone forgot to register.
#
# Usage:
#   scripts/validate_scad.sh --all              # every part + assembly.scad
#   scripts/validate_scad.sh <part_basename>     # just parts/<name>.scad
#
# Flags used below (--hardwarnings, --check-parameters, --check-parameter-ranges)
# were confirmed present via `openscad --help` on 2026-08-16 -- see
# references/setup-notes.md in this skill if that ever needs re-checking.

set -euo pipefail

OPENSCAD=${OPENSCAD:-openscad}
BUILD_DIR=${BUILD_DIR:-build}
BACKEND=${BACKEND:-Manifold}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=${1:---all}

check_openscad() {
    if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
        echo "ERROR: OpenSCAD not found ($OPENSCAD). Install it first." >&2
        exit 1
    fi
    "$OPENSCAD" --version
}

validate_file() {
    local scad="$1"
    local stl="$2"
    echo "--- Validating $scad -> $stl ---"
    mkdir -p "$(dirname "$stl")"
    "$OPENSCAD" --backend="$BACKEND" \
        --hardwarnings \
        --check-parameters=true \
        --check-parameter-ranges=true \
        -o "$stl" "$scad"
    if [ ! -s "$stl" ]; then
        echo "ERROR: STL is empty: $stl" >&2
        exit 1
    fi
    echo "OK: $(du -h "$stl" | cut -f1)"

    # Bounding-box check: only runs if the part declares an expected size via
    # `// EXPECTED_BBOX: [x, y, z]` -- catches a part that renders fine and
    # *looks* right but is subtly the wrong size (wrong -D override, a units
    # slip, a parameter that didn't thread through correctly).
    if grep -q '^[[:space:]]*//[[:space:]]*EXPECTED_BBOX' "$scad"; then
        python3 "$SCRIPT_DIR/check_dimensions.py" --stl "$stl" --scad "$scad"
    fi
}

check_openscad

if [[ "$MODE" == "--all" ]]; then
    shopt -s nullglob
    parts=(parts/*.scad)
    shopt -u nullglob
    if [ ${#parts[@]} -eq 0 ]; then
        echo "WARNING: no files found under parts/*.scad" >&2
    fi
    for scad in "${parts[@]}"; do
        base="$(basename "$scad" .scad)"
        validate_file "$scad" "$BUILD_DIR/$base.stl"
    done
    if [ -f assembly.scad ]; then
        validate_file "assembly.scad" "$BUILD_DIR/assembly.stl"
    fi
else
    scad="parts/$MODE.scad"
    if [ ! -f "$scad" ]; then
        echo "ERROR: $scad not found" >&2
        exit 1
    fi
    validate_file "$scad" "$BUILD_DIR/$MODE.stl"
fi

echo "All validations passed."
`````

### B4. scad-modeler/scripts/check_dimensions.py

**Path:** `scad-modeler/scripts/check_dimensions.py`

`````python
#!/usr/bin/env python3
"""Check exported STL bounding box against expected dimensions declared in SCAD.

Catches the failure mode visual inspection and assert()s in params.scad both
miss: geometry that renders and *looks* right (proportions look plausible) but
is subtly the wrong size -- a wrong -D override, a units slip, a parameter that
didn't thread through correctly. Rendering + eyeballing a preview won't catch a
part that's 5% off in one dimension; comparing the actual STL bounding box
against a stated expectation will.

Reads `// EXPECTED_BBOX: [x, y, z]` from the SCAD source file (declare it near
the top, next to the part's own dimension variables) and compares to the
rendered STL's actual bounding box. If the SCAD file has no such comment, this
prints a note and exits 0 (opt-in, not required for every part -- e.g. odd-
shaped parts where a bounding box isn't a meaningful sanity check).

Requires only `trimesh` (confirmed: unlike check_collisions.py, this script's
mesh.bounds/mesh.is_empty do NOT need scipy or python-fcl -- tested in a venv
with trimesh alone). Install with:
    pip install trimesh

Usage:
    python3 check_dimensions.py --stl build/part.stl --scad parts/part.scad
    python3 check_dimensions.py --stl build/part.stl --scad parts/part.scad \\
        --abs-tol 0.5 --rel-tol 0.01

Tolerance per axis = max(--abs-tol, --rel-tol * expected_dimension) -- a flat
mm floor for small parts, a percentage for large ones where mesh tessellation
error alone can exceed a fixed mm value. Defaults (0.3mm / 1%) confirmed to
correctly pass a exact match, fail a deliberate 1mm mismatch, and pass a
200mm part within its wider absolute tolerance -- see this skill's
references/setup-notes.md.
"""
import argparse
import os
import re
import sys

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: pip install trimesh", file=sys.stderr)
    sys.exit(1)

BBOX_RE = re.compile(
    r'^\s*//\s*EXPECTED_BBOX\s*:\s*\[\s*'
    r'([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*,\s*([0-9.eE+\-]+)\s*\]'
)


def parse_expected_from_scad(scad_path):
    try:
        with open(scad_path, 'r', encoding='utf-8') as f:
            for line in f:
                m = BBOX_RE.match(line)
                if m:
                    return [float(m.group(1)), float(m.group(2)), float(m.group(3))]
    except OSError as e:
        print(f"ERROR: cannot read SCAD file {scad_path}: {e}", file=sys.stderr)
        sys.exit(1)
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stl', required=True)
    parser.add_argument('--scad', required=True)
    parser.add_argument('--abs-tol', type=float, default=0.3)
    parser.add_argument('--rel-tol', type=float, default=0.01)
    args = parser.parse_args()

    if not os.path.isfile(args.stl):
        print(f"ERROR: STL file not found: {args.stl}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.scad):
        print(f"ERROR: SCAD file not found: {args.scad}", file=sys.stderr)
        sys.exit(1)

    expected = parse_expected_from_scad(args.scad)
    if expected is None:
        print(f"WARNING: no '// EXPECTED_BBOX: [x, y, z]' line in {args.scad}; skipping.")
        return 0

    mesh = trimesh.load(args.stl, force="mesh")
    if mesh.is_empty:
        print(f"ERROR: STL is empty or invalid: {args.stl}", file=sys.stderr)
        sys.exit(1)

    bounds = mesh.bounds
    actual = bounds[1] - bounds[0]

    tolerances = [max(args.abs_tol, args.rel_tol * abs(e)) for e in expected]

    errors = []
    for i, axis in enumerate(['X', 'Y', 'Z']):
        diff = abs(actual[i] - expected[i])
        if diff > tolerances[i]:
            errors.append(
                f"{axis}: expected {expected[i]:.3f} mm, got {actual[i]:.3f} mm "
                f"(diff {diff:.3f} mm > tol {tolerances[i]:.3f} mm)"
            )

    if errors:
        print(f"FAIL: {os.path.basename(args.stl)} bbox mismatch:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"OK: {os.path.basename(args.stl)} bbox {actual} within tolerances {tolerances}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
`````

### B5. scad-modeler/scripts/check_collisions.py

**Path:** `scad-modeler/scripts/check_collisions.py`

`````python
#!/usr/bin/env python3
"""Check for unintended interference between already-positioned assembly parts.

Requires: trimesh, python-fcl (trimesh.collision.CollisionManager wraps FCL for
the actual collision math -- trimesh alone does not do this), and scipy (trimesh's
own is_convex/body_count checks need it, even though this script never imports it
directly). Confirmed by actually running this script end-to-end -- install with:
    pip install trimesh python-fcl scipy

Overlap-volume reporting additionally needs a mesh boolean engine (e.g.
manifold3d) to compute the intersection; without one it still correctly
reports collision True/False, just without a volume number.

Usage:
    python3 check_collisions.py build/part_a.stl build/part_b.stl [...]

Every STL passed in must already be in the shared assembly coordinate system
(i.e. exported from assembly.scad with parts positioned via at(), not raw
unpositioned part files) -- checking unpositioned parts against each other is
meaningless, since they'd all be sitting at their own local origins.

Exits non-zero if any pair overlaps, or if any mesh isn't watertight (a
non-watertight mesh makes the collision/volume results unreliable).
"""
import sys
import itertools

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: pip install trimesh python-fcl", file=sys.stderr)
    sys.exit(1)

try:
    from trimesh.collision import CollisionManager
except ImportError:
    print(
        "ERROR: trimesh.collision.CollisionManager unavailable -- this needs the "
        "python-fcl package (trimesh doesn't implement collision detection itself, "
        "it wraps FCL). Run: pip install python-fcl",
        file=sys.stderr,
    )
    sys.exit(1)


def main(paths):
    if len(paths) < 2:
        print("Need at least 2 STL files to check for collisions.", file=sys.stderr)
        sys.exit(1)

    meshes = {}
    for p in paths:
        m = trimesh.load(p, force="mesh")
        if not m.is_watertight:
            print(f"WARNING: {p} is not watertight -- results for it are unreliable")
        meshes[p] = m

    manager = CollisionManager()
    for p, m in meshes.items():
        manager.add_object(p, m)

    is_collision, contact_names = manager.in_collision_internal(return_names=True)

    if not is_collision:
        print(f"OK: no collisions among {len(paths)} parts.")
        return 0

    print("COLLISION(S) FOUND:")
    for a, b in contact_names:
        # Estimate overlap volume via boolean intersection, for a sense of severity.
        try:
            overlap = meshes[a].intersection(meshes[b])
            vol = overlap.volume if overlap is not None and overlap.is_volume else None
        except Exception:
            vol = None
        vol_str = f", approx overlap volume {vol:.1f} mm^3" if vol else ""
        print(f"  - {a}  <->  {b}{vol_str}")

    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
`````

### B6. scad-modeler/templates/part_template.scad

**Path:** `scad-modeler/templates/part_template.scad`

`````c
// ============================================================
// <part_name>.scad
// Local origin: <state the exact datum, e.g. "center of the bearing bore,
//                bore axis = Z" or "bottom face that mounts to the chassis">
// Material: <e.g. PETG>
// Print orientation: <e.g. flat face down, no supports needed>
// EXPECTED_BBOX: [40, 20, 15]   // update to match part_length/width/height below --
//                                 validate_scad.sh checks the rendered STL against
//                                 this automatically; delete the line to skip
//                                 (e.g. for an odd shape where a bbox isn't meaningful)
// ============================================================

include <../params.scad>
include <BOSL2/std.scad>   // MUST be `include`, not `use` -- see setup-notes.md
                            // (delete this line if the part doesn't use BOSL2 attach/anchors)

// ------------------------------------------------------------
// Local dimensions (part-specific only -- shared/derived values
// belong in params.scad, not re-declared here)
// ------------------------------------------------------------
part_length = 40;
part_width = 20;
part_height = 15;
wall = 3;

// ------------------------------------------------------------
// Geometry module -- local coordinates only.
// Do NOT translate()/rotate() the whole part here -- that's
// layout.scad's job via at("<part_name>") in assembly.scad.
// ------------------------------------------------------------
module part_geometry() {
    difference() {
        cuboid([part_length, part_width, part_height]) {
            // Example: a boss on the top face via BOSL2 attach --
            // delete this block if the part doesn't need it.
            // attach(TOP) cyl(h=8, d=10, anchor=BOTTOM);
        }
        // Cutouts (holes, pockets, ...) go here.
    }
}

// Always render unconditionally when this file runs standalone --
// $preview is the only real OpenSCAD mode flag (true in F5/quick-preview,
// false in F6/full render); there is no separate "$render" variable.
part_geometry();
`````

### B7. scad-modeler/templates/layout.scad

**Path:** `scad-modeler/templates/layout.scad`

`````c
// ============================================================
// layout.scad -- where each printed part sits in the shared assembly
// coordinate system. See SKILL.md §3 for the full explanation and
// §6 for how assembly.scad is supposed to consume this file.
//
// State the coordinate system explicitly before the table -- origin,
// what each axis means -- so a position number is checkable against
// a real reference point, not just "whatever made it render right."
// Origin: <e.g. "center of the rear differential, on the axle
//          centerline">. X=<...>, Y=<...>, Z=<...>.
// ============================================================

include <params.scad>

LAYOUT = [
    // ["<part_name>", [x, y, z], [rx, ry, rz]],
    ["<part_a>", [0, 0, 0], [0, 0, 0]],
    ["<part_b>", [0, 0, 0], [0, 0, 0]],
];

function layout_pos(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][1] : layout_pos(name, i+1);
function layout_rot(name, i=0) = i >= len(LAYOUT) ? undef :
    LAYOUT[i][0] == name ? LAYOUT[i][2] : layout_rot(name, i+1);

module at(name) {
    pos = layout_pos(name); rot = layout_rot(name);
    assert(pos != undef, str("Layout entry not found: ", name));
    translate(pos) rotate(rot) children();
}
`````

---

## PART 2 — How the current system actually works (mechanism summary)

This section restates, in condensed analytical form, *what the skills actually
do*, so you can evaluate the mechanism rather than re-derive it from the source.
Nothing here is new information — it is a reading of Part 1.

### 2.1 The single-part loop (`openscad-cad`)

The core epistemic claim of this skill is: **compilation success is not
correctness evidence, and a rendered image is**. The loop is:

1. Write the model with every meaningful dimension hoisted to a named top-level
   variable (which also makes CLI overriding via `-D 'var=value'` possible).
2. Render a PNG headlessly (`openscad -o out.png --render --imgsize=... --autocenter --viewall --projection=ortho model.scad`, wrapped in `xvfb-run -a` on headless Linux).
3. **The agent visually inspects that PNG** — i.e. the verification step is a
   vision-language model looking at a rasterised orthographic view.
4. Iterate; only export STL/3MF once the image looks right.
5. For anything with internal structure, render three views (top / front / iso)
   via explicit `--camera=tx,ty,tz,rx,ry,rz,dist` Euler-form cameras, on the
   stated reasoning that a single isometric view hides internal features.
6. `--render` (full CSG evaluation, equivalent to GUI F6) is mandated over the
   fast OpenCSG preview (F5) whenever booleans are involved, because preview
   mode can display boolean results misleadingly.

Domain knowledge is then layered on: a Gridfinity section that delegates all
grid math to `gridfinity-rebuilt-openscad` rather than reimplementing it, with a
hand-maintained parameter table and an explicit warning that the table has
already drifted from upstream once and must be re-verified against the actual
cloned source (`sed -n '1,80p' gridfinity-rebuilt-bins.scad`); and a threaded-
fastener section delegating to `rcolyer/threads-scad`.

**Verification methods present:** visual inspection of renders; multi-view
rendering; comparing the render against the user's stated dimensions before
declaring done. **That is all.** There is no numeric check of any kind in this
skill — no script, no assertion, no measurement.

### 2.2 The assembly loop (`scad-modeler`)

This skill adds five structural mechanisms on top of the above:

**(a) A mandatory pre-geometry calculation table.** Before any OpenSCAD is
written, the agent must produce a Markdown table of `Part | Formula | Value |
Status`, and mark any value not traceable to a datasheet, spec, or prior
decision as `PATIKRINTI` (Lithuanian for "to verify"). All `PATIKRINTI` items
must be resolved before geometry begins. The table is carried into the final
report. Rationale: a wrong bearing bore or gear ratio is invisible in a render
and only surfaces when the printed parts don't fit.

**(b) `params.scad` — single source of dimensional truth.** Every dimension used
anywhere in the assembly lives in one file. Crucially, this file carries
`assert()` statements encoding design invariants (ratio within a target band,
positive wall thickness after clearance subtraction, bore larger than shaft).
Because a bare top-level `assert()` halts the OpenSCAD render, **these are the
only automatically-enforced engineering constraints in the entire system.**

**(c) `layout.scad` — centralised inter-part positioning.** A `LAYOUT` array of
`[name, [x,y,z], [rx,ry,rz]]` triples, plus recursive lookup functions and an
`at(name) { children(); }` module. An explicit comment must define the assembly
coordinate system (origin datum, axis meanings). Part files are modelled purely
in **local coordinates** around their own datum and must never transform
themselves; all assembly-level placement flows through `at()`. Within a single
part, feature placement is delegated to **BOSL2's anchor/attachment system**
(`attach(TOP)`, `attach(TOP+FWD+RIGHT)`) rather than hand-computed offsets.

**(d) `assembly.scad` with a MODE switch.** `MODE="assembly"` renders everything
positioned; `MODE="part"` + `PART="name"` renders one named part **still in
assembly coordinates**; `MODE="exploded"` for visualisation. Because OpenSCAD
modules are not first-class values, an explicit `if/else` name-dispatch module
is required. Part files must be pulled in with `use`, never `include`, because
`include` would also execute each part file's own trailing unconditional render
call and silently duplicate the geometry. A BOM is emitted via `echo()`.

**(e) The validation cycle.** Three layers:

- `validate_scad.sh --all` — auto-globs `parts/*.scad` plus `assembly.scad`,
  renders each to STL with `--hardwarnings --check-parameters=true
  --check-parameter-ranges=true` under the Manifold backend, and hard-fails on
  an empty STL. `set -euo pipefail` means the first failure aborts the run.
- `check_dimensions.py` — greps the `.scad` for an opt-in
  `// EXPECTED_BBOX: [x, y, z]` comment; if present, loads the rendered STL with
  `trimesh` and compares the actual axis-aligned bounding box against the
  declared one, per axis, with tolerance `max(0.3 mm, 1% × expected)`. Absent
  comment = check silently skipped.
- `check_collisions.py` — loads every passed STL with `trimesh`, warns on
  non-watertight meshes, registers them all in a `trimesh.collision.
  CollisionManager` (a wrapper around **FCL**, the Flexible Collision Library),
  and calls `in_collision_internal(return_names=True)`. For each colliding pair
  it attempts a boolean `intersection()` to report an approximate overlap volume
  as a severity hint. Exits non-zero if any pair collides.

The skill states an explicit anti-pattern: *fix a validation failure at its
source; never loosen an `assert()` or a collision threshold to make the failure
go away.*

### 2.3 How the skills decide what to trust

Both skills share a distinctive epistemic discipline that is worth naming
because your recommendations should preserve it:

- Claims carry **verification dates** and the method by which they were checked
  ("confirmed via `openscad --help` on 2026-08-16", "confirmed by reproducing
  the failure with a minimal repro").
- Failures of *previous versions of the skill itself* are recorded rather than
  quietly fixed — e.g. an earlier version documented Gridfinity parameters
  (`style_lip`, `cdivx`/`cdivy`/`c_orientation`) that do not exist in the
  current source; an earlier `BOSL2` "install" was a single stray `gears.scad`
  file that merely shared the directory name.
- Claims sourced from another LLM (DeepSeek is named) were **independently
  re-verified** before being written down; one such claim (that `openscad --info`
  reports a bounding box) was checked and found false, which is precisely why
  the STL + `trimesh` round-trip exists.
- There is a recorded **end-to-end dogfood run** (2026-08-16) of the whole
  `scad-modeler` workflow on a synthetic 2-part gear assembly, in which the
  collision checker caught a genuine design error (an over-generous gear housing
  footprint overlapping the motor mount), and `gear_dist()` returned a different
  centre distance than the naive `(t1+t2)·m/2` formula.

---

## PART 3 — Weaknesses I have already identified (starting points, not conclusions)

These are my own observations from reading the source. **Treat them as
hypotheses to confirm, refute, quantify, or supersede with better sources — not
as findings.** I expect you to find things I missed, and to tell me where I am
wrong.

### 3.1 Collision detection is static, binary, and blind to intent

- **Single-pose only.** `in_collision_internal()` evaluates one frozen assembly
  configuration. For a gearbox — the skill's own headline use case — the parts
  *move*. Rotating gears, linkages, and any moving carriage can be perfectly
  clear at 0° and interfere at 37°. There is no sweep, no configuration-space
  sampling, no kinematic model at all.
- **No clearance query.** FCL/trimesh expose a `min_distance_internal()`; the
  script does not use it. Two parts sitting 0.02 mm apart pass the check, but
  will fuse in an FDM print. For 3D printing, *proximity below the process
  resolution is functionally a collision*, and only proximity — not overlap —
  detects it.
- **No notion of intentional contact.** Press-fit bearings, interference fits,
  threaded joints, and snap-fits are *supposed* to overlap in the nominal model.
  There is no allowlist / expected-contact-pair mechanism, so the checker
  presumably produces false positives on exactly the joints that matter most,
  which trains the operator to ignore it.
- **No severity threshold.** A 0.001 mm tessellation artefact and a 5 mm design
  blunder are both "COLLISION". The overlap volume is reported only as a
  best-effort side note, and requires a boolean engine that may be absent.
- **Docstring/behaviour mismatch (probable bug).** The module docstring states
  "Exits non-zero if any pair overlaps, **or if any mesh isn't watertight**",
  but the implementation only prints `WARNING:` for a non-watertight mesh and
  continues. Since FCL results on a non-watertight mesh are unreliable, this
  silently degrades from "checked" to "seemed fine".
- **Tessellation sensitivity.** Both bodies are polygonal approximations of
  curved surfaces. A shaft in a bore, both faceted, can produce chordal-error
  collisions or missed collisions depending on facet phase alignment. The
  interaction between `$fa`/`$fs` and collision-check validity is not addressed
  anywhere.
- **Complexity.** All-pairs internal checking is O(n²) broad-phase; irrelevant at
  5 parts, relevant if the workflow ever scales.

### 3.2 Dimensional verification only sees the bounding box

- An axis-aligned bounding box catches gross scale errors (a units slip, a bad
  `-D` override) and nothing else. **Every internal feature is unverified**:
  hole diameters, bore positions, wall thicknesses, thread pitches, pocket
  depths, hole-to-hole spacing — none of it is checked, and none of it is
  visible in a bounding box.
- The check is **opt-in via a comment** and silently skipped when absent, so
  coverage is unknown and unmeasured.
- `EXPECTED_BBOX` is a **hand-maintained literal in a comment**, duplicating
  values that already exist as variables in the same file. It can drift out of
  sync with the geometry, and nothing detects that drift.
- The tolerance `max(0.3 mm, 1%)` is asserted as "confirmed" by three ad-hoc test
  cases. It has no basis in either mesh-tessellation error analysis or FDM
  process capability data. What *should* the tolerance be, and should it be
  derived from `$fa`/`$fs` chordal error rather than guessed?
- **No other geometric property is checked at all**: volume, surface area, mass,
  centre of mass, moments of inertia, minimum wall thickness, overhang angles,
  unsupported bridge spans, minimum feature size vs nozzle diameter, mesh
  manifoldness, self-intersection, degenerate triangles, normal consistency.
- **No regression baseline.** There is no golden-STL hash, no stored volume/bbox
  snapshot, so an unintended geometry change caused by editing a shared
  `params.scad` value is invisible unless a human notices.

### 3.3 The engineering calculation layer is thin and unstandardised

- The calculation table is **prose in Markdown** — an LLM writing numbers into a
  table it also authored. Only those values that are separately re-expressed as
  an `assert()` in `params.scad` are machine-enforced; there is no mechanism
  linking table rows to assertions, so the table can be internally inconsistent
  with the model that gets built.
- **No unit system and no dimensional analysis.** Millimetres are assumed
  everywhere and never checked.
- **No tolerance stack-up analysis whatsoever.** This is a first-order omission:
  in a multi-part assembly, individual per-part clearances accumulate along
  dimension chains. Worst-case, RSS (root-sum-square), and Monte-Carlo stack-up
  are standard practice and completely absent.
- **Gear design coverage is one line deep.** The skill correctly delegates
  involute geometry to BOSL2 (with a well-reasoned argument for why hand-rolled
  involute math fails invisibly), and correctly prefers `gear_dist()` over
  `(t1+t2)·m/2` once profile shift is active. But nothing checks: contact ratio,
  undercut / minimum tooth count, tip-root interference, backlash derivation,
  tip and root clearance, face-width ratio, tooth bending stress (Lewis / AGMA /
  ISO 6336), surface durability, or — most relevant here — the specific design
  rules for **polymer gears** (VDI 2736) and the derating that 3D-printed,
  anisotropic, layer-bonded plastic gears require.
- **Bearing and shaft fits are not standards-based.** There is no reference to
  the ISO 286 hole/shaft fit system (H7/h6, H7/k6, H7/p6 …), no distinction
  between clearance / transition / interference fits, no press-fit interference
  calculation, no consideration of hoop stress in a printed bore.
- **No load, stress, or stiffness analysis of any kind**, and no material
  property data — despite the fact that FDM parts are strongly anisotropic
  (inter-layer/Z strength is typically a large fraction weaker than in-plane),
  which makes print orientation a *structural* decision. The skills treat print
  orientation purely as a support-material convenience.

### 3.4 The tolerance data is a three-row anecdote

`openscad-cad/references/tolerances.md` contains exactly three fit classes
(1.5 mm/side loose, 1.0 mm/side constrained, 0.5–1.0 mm/side friction), each
sourced from a single part printed by one person on one printer, with no
material, nozzle, layer height, slicer, or measurement data recorded.

Missing entirely, and all well-documented elsewhere:

- **The OpenSCAD polygon-inscription problem.** `circle()`/`cylinder()` produce
  an *inscribed* polygon, so a modelled hole is systematically undersized by a
  factor related to `1/cos(180°/$fn)`; the standard community fix is an explicit
  compensation factor. This is an OpenSCAD-specific, purely geometric,
  *deterministic* error source that stacks on top of process error, and neither
  skill mentions it.
- Slicer-side compensation (horizontal expansion / XY size compensation /
  elephant-foot compensation) — which changes the correct CAD clearance.
- Material shrinkage and warp (PLA vs PETG vs ABS/ASA differ substantially).
- Direction dependence: XY holes vs Z holes vs slots vs external pins behave
  differently; hole undersizing on FDM is a documented, measurable phenomenon.
- Any statistical framing: process capability, measured standard deviation,
  achievable IT grade for FDM. There is published academic work measuring FDM
  dimensional deviation — none of it is reflected here.
- A calibration procedure: the standard practice of printing a tolerance/fit
  test coupon once per printer+material and reading the values off it.

### 3.5 Visual inspection is doing more work than it can support

The single-part skill's *primary* correctness mechanism is "render a PNG and
look at it". This asks a vision-language model to judge geometric correctness
from a shaded raster image. Missing supports that would make that judgement much
more reliable:

- **No section / cutaway convention.** Internal geometry is fundamentally
  invisible in an external view; the standard OpenSCAD trick (`difference()`
  against a large half-space cube, or the `--view=cut` style approaches) is not
  used, even though the skill itself acknowledges internal structure is the hard
  case and answers it only with "render more external angles".
- **No dimensional annotation in renders** — no scale bar, no ruler, no
  reference cube, no dimension callouts. A VLM cannot measure an unlabelled
  render, so "check the render against the stated dimensions" is not actually
  achievable by looking.
- No standard view set (the six orthographic views / first- vs third-angle
  projection conventions of engineering drawing) — the three views are ad hoc.
- No wireframe/edge or colour-coded-per-part rendering to disambiguate
  overlapping bodies in an assembly view.

### 3.6 Tooling the skills appear not to know about

Candidates worth investigating (verify each — do not assume my list is correct
or complete):

- **`openscad --summary`** (`all|geometry|bounding-box|…`) and
  `--summary-file`. `setup-notes.md` concludes that STL export + `trimesh` is
  "the only real option" for a bounding box, but that conclusion was reached by
  testing `--info`, not `--summary`. If `--summary` reports bounding box /
  volume / area directly, a whole round-trip disappears and volume becomes a
  cheap regression signal. **Verify this against the current OpenSCAD manual and
  a real binary.**
- **NopSCADlib** — a large OpenSCAD framework with an off-the-shelf-parts
  ("vitamins") library, and, critically, **automatic BOM generation and exploded
  assembly-instruction generation** — directly overlapping with `scad-modeler`
  §6/§8, which does both by hand.
- **Round-Anything** — tolerance-aware rounding/filleting plus explicit
  tolerance-modelling helpers for printed parts.
- **`dotSCAD`**, **`threadlib`**, **BOSL2's own regression/test harness** (as a
  model for how to test OpenSCAD code at all).
- **CadQuery / build123d** — Python, OpenCASCADE B-rep. Real fillets, real
  constraints, exact geometry, and — most relevant — B-rep enables *exact*
  interference volumes, section views, and feature interrogation that a mesh
  pipeline can only approximate. Worth a genuine "should this workflow migrate,
  or hybridise?" assessment.
- **FreeCAD headless (Python API)** — interference checking, drawing generation,
  and an FEA workbench (CalculiX) for load cases.
- **Slicer-in-the-loop validation** — PrusaSlicer / OrcaSlicer / CuraEngine CLI
  can slice headlessly and report non-manifold errors, support volume, print
  time, and material use. This turns "is it printable?" from a judgement call
  into a command that returns an exit code, and is arguably the single highest-
  value missing check.
- **Mesh QA**: `admesh`, `pymeshlab`, `libigl` self-intersection tests,
  `Open3D`, and `manifold3d` (already a soft dependency of the collision script).
- **Kinematic / swept collision**: PyBullet, Drake, `python-fcl`'s continuous
  collision detection, or simply parameter-sweeping rotation angles and re-running
  the existing static check at each step.
- **CI**: none exists. OpenSCAD runs headlessly in containers, so GitHub Actions
  could run `validate_scad.sh` on every commit.

### 3.7 The skills as artifacts: portability, decay, and evaluation

- **Hardcoded machine-specific absolute paths** are baked into the instructions:
  `~/Documents/OpenSCAD/libraries/BOSL2`, and
  `Docs/03_Asmeniniai_projektai/3D_Spausdinimas/gridfinity-rebuilt-openscad/`.
  These make the skills non-portable and will mislead an agent on any other
  machine. What is the right pattern — capability *detection* at run time
  instead of asserted paths?
- **Dated verification claims will rot.** The discipline of dating claims is
  excellent, but there is no re-verification mechanism — nothing prompts the
  agent to re-check a claim whose date is a year old. Can the verification be
  turned into a runnable script (a "doctor" / preflight check) instead of prose?
- **Trigger-boundary ambiguity between the two skills.** Both descriptions are
  long and overlapping ("bracket", "enclosure", "insert" vs "assembly",
  "multi-part"). What does the research on LLM tool/skill selection say about
  writing mutually-exclusive routing descriptions?
- **The validation scripts live only in `scad-modeler`.** A single-part
  `openscad-cad` user gets no dimension check at all, though `check_dimensions.py`
  would work perfectly for them. Is the two-skill split even the right
  decomposition?
- **Mixed natural languages** (`PATIKRINTI` as a status marker in otherwise
  English instructions) — does this measurably affect LLM compliance?
- **No evaluation suite for the skills themselves.** There is one recorded
  dogfood run and no repeatable benchmark. How should an agent skill of this
  kind be evaluated — what does the literature on LLM agent evaluation, and
  specifically on LLM-generated CAD benchmarks, suggest?

---

## PART 4 — Research questions to answer

Organise your report around these. Every substantive claim must carry a citation
(paper, standard number, documentation URL, or repository link). Where the
literature is thin or contested, say so explicitly rather than manufacturing
confidence.

### Q1 — Interference and collision detection
1. What is the state of the art for automated interference detection between
   mesh-based mechanical parts, and how does FCL (BVH + GJK/EPA) sit within it?
2. How should *minimum-distance / clearance* checking be added, and what
   threshold is defensible for FDM-printed assemblies?
3. How is **intentional** interference (press fits, threads, snap fits) handled
   in professional CAD interference checking, and what is the right mechanism
   for an expected-contact allowlist?
4. What are the practical approaches to **swept-volume / kinematic** interference
   checking for rotating and translating assemblies, and what is the cheapest
   version of that a script could implement (e.g. discrete configuration
   sampling — and how fine must the sampling be to be sound)?
5. How does mesh tessellation resolution (`$fa`/`$fs`/`$fn`, chordal error)
   affect collision-check validity, and how should facet resolution be chosen so
   that the check means something?
6. Are there better libraries than trimesh+FCL for this specific job?

### Q2 — Geometric and dimensional verification
1. Beyond bounding boxes, what automatically-checkable geometric invariants are
   used in CAD verification and DfAM validation (volume, mass properties,
   minimum wall thickness, thin-feature detection, overhang analysis,
   accessibility/tool-reachability, manifoldness, self-intersection)?
2. What open-source tools compute each of those on an STL or in a slicer?
3. What is the published approach to **regression testing of parametric CAD** —
   golden geometry, property-based testing, metamorphic testing?
4. Should verification move upstream into the CAD kernel (B-rep feature
   interrogation) rather than downstream on the exported mesh? What is lost and
   gained?
5. What mesh-error magnitude should the bbox tolerance actually be, derived from
   first principles given a facet resolution?

### Q3 — Engineering calculation coverage
1. For a hobby-scale printed gearbox, what is the **minimum defensible set** of
   gear calculations? Map each to its standard (ISO 6336, DIN 3990/3960, AGMA
   2001, and especially **VDI 2736** for polymer gears).
2. What derating factors apply to **3D-printed** polymer gears (anisotropy,
   layer adhesion, tooth-root layer orientation, wear, heat)? Is there peer-
   reviewed experimental data on printed gear load capacity and failure modes?
3. What are the standard **bearing and shaft fit** recommendations (ISO 286,
   SKF/manufacturer engineering data), and how must they be adapted for printed
   bores?
4. What is the correct method for **tolerance stack-up** in a printed assembly —
   worst case vs RSS vs Monte Carlo — and is there a lightweight way to make an
   LLM agent do it correctly and verifiably?
5. Which of these calculations can be encoded as machine-checkable `assert()`s
   in `params.scad`, and which fundamentally cannot?

### Q4 — Tolerance and fit data for FDM
1. What does the **peer-reviewed literature** report for FDM dimensional
   accuracy — systematic hole undersizing, external-dimension oversizing,
   direction dependence, achievable ISO IT grades, and the influence of
   material, nozzle, layer height, speed and cooling?
2. What are the best-documented **community/empirical** fit tables and
   calibration coupons, and how well do they agree with the academic data?
3. Quantify the **OpenSCAD polygon-inscription** error and give the correct
   compensation approach, including how `$fn` interacts with it.
4. How should the three-row `tolerances.md` be restructured — what columns,
   what fit classes, what provenance metadata — so it is honest about its own
   uncertainty and extensible as data accumulates?
5. What calibration procedure should the skill instruct a user to run once, so
   its numbers become *their printer's* numbers?

### Q5 — Tooling and ecosystem
1. Verify the `openscad --summary` question in §3.6 and state exactly what the
   current OpenSCAD CLI can report without a mesh round-trip.
2. Evaluate NopSCADlib, Round-Anything, BOSL2, dotSCAD and any others against
   what these skills currently do by hand (BOM, exploded views, filleting,
   tolerance modelling, vitamins).
3. Give an honest assessment of **CadQuery / build123d vs OpenSCAD** for this
   use case — including the specific question of whether an LLM agent writes
   correct code more reliably in one than the other, and whether any published
   work measures that.
4. Assess **slicer-in-the-loop validation** as a printability gate: which slicer
   CLI, which checks, which exit codes, what it can and cannot catch.
5. What would a sensible CI setup look like for a repository of parametric
   printed parts?

### Q6 — Visual verification by a vision-language model
1. What is known about VLM accuracy at judging 3D geometry from rendered views,
   and what rendering choices measurably improve it (orthographic vs
   perspective, section views, annotated dimensions, colour coding, wireframe,
   multi-view grids, known-scale reference objects)?
2. Is there published work on **render-inspect-correct feedback loops** for
   LLM-generated 3D models, and what do the results say about how much such a
   loop actually improves correctness?
3. What should the skill's rendering convention be, concretely, to maximise the
   information a VLM can extract?

### Q7 — LLM-generated CAD: what the research says
1. Survey the recent literature on **LLMs generating CAD / parametric 3D models**
   (text-to-CAD, LLM code generation for OpenSCAD/CadQuery, self-correction with
   execution or visual feedback, benchmarks and datasets). What are the measured
   failure modes?
2. Which of those documented failure modes do these two skills already mitigate,
   and which do they not?
3. What guardrail patterns from that literature (verification-first, executable
   specifications, self-consistency, constraint checking, program repair loops)
   should be adopted here?

### Q8 — Skill design as an artifact
1. What are the current best practices for authoring agent skills / system
   procedures for LLMs — structure, length, imperative specificity, progressive
   disclosure, description writing for reliable triggering, and the
   deterministic-script vs advisory-prose boundary?
2. Should the two skills be merged, re-split, or restructured? Propose the
   decomposition you would defend.
3. How should machine-specific state (library paths, installed versions) be
   handled — runtime capability detection, a preflight "doctor" script, a
   generated environment manifest?
4. How should dated verification claims be prevented from silently rotting?
5. How should these skills be **evaluated**? Propose a concrete eval suite:
   representative tasks, ground truth, pass criteria, and what to measure.

---

## PART 5 — Required output format

Produce a single structured report in **Lithuanian**, with these sections:

1. **Santrauka** — the 5–10 highest-leverage changes, ranked by
   (impact × confidence) ÷ effort, each with a one-line justification.
2. **Radiniai pagal sritį** — one section per Q1–Q8, each containing:
   - what the current skill does,
   - what the literature / standards / state of the art says,
   - the specific delta, with citations,
   - a concrete, actionable recommendation (down to the level of "add this
     column", "replace this call with that call", "add this script").
3. **Faktinių klaidų sąrašas** — every claim in Part 1 you found to be wrong,
   outdated, or unsafely over-generalised, with the correction and its source.
   Include verdicts on the specific items I flagged: the `--summary` vs `--info`
   conclusion, the `check_collisions.py` watertight docstring/behaviour mismatch,
   the `max(0.3 mm, 1%)` tolerance, and the three-row fit table.
4. **Siūloma nauja struktūra** — the file/folder layout you would recommend for
   the skill set, including any new scripts, with a one-paragraph spec for each
   new script (inputs, outputs, exit codes, dependencies).
5. **Nauji/atnaujinti `references/` failai** — draft the actual content you would
   put in a standards-based tolerance table and any new reference documents.
6. **Prioritetinis įgyvendinimo planas** — phased: what to do first, what needs
   empirical calibration by the user (print-and-measure), what is a longer-term
   architectural change.
7. **Šaltiniai** — full citation list, grouped by theme, with links, and marked
   by type (peer-reviewed / standard / official documentation / community).

**Explicitly flag your own uncertainty.** Where you could not verify something,
say "neatsakyta — reikia patikrinti X būdu" rather than guessing. The material
you are reviewing was built on the principle of never asserting an unverified
claim as fact, and the review should hold itself to the same standard.
