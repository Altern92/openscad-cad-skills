# Gridfinity parameter reference

Full `-D` override tables for `gridfinity-rebuilt-openscad`'s two entry points.
Moved out of `SKILL.md` itself (progressive disclosure -- this is lookup
material, needed only when actually setting parameters, not on every skill
load) on 2026-08-18. See `SKILL.md` §3 for setup, gotchas, and the custom-cutout
example -- this file is the table only.

**Verified against the repo as cloned 2026-08-09** -- this is a live community
project; before trusting this table on a fresh or stale clone, skim the actual
current variable block (it's the OpenSCAD Customizer UI source, always current
with that copy):

```bash
sed -n '1,80p' gridfinity-rebuilt-bins.scad
```

## Bin parameters (`gridfinity-rebuilt-bins.scad`)

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
| `enable_thumbscrew` | adds a Gridfinity-Refined M15×1.5 threaded thumbscrew hole per base — built with the vendored `src/external/threads-scad/threads.scad` (see SKILL.md §4) |

## Baseplate parameters (`gridfinity-rebuilt-baseplate.scad`)

| Variable | Meaning |
|---|---|
| `gridx`, `gridy` | footprint in grid units |
| `style_plate` | 0=thin, 1=weighted, 2=skeletonized, 3=screw-together, 4=screw-together minimal |
| `distancex`, `distancey`, `fitx`, `fity` | drawer-fit: min baseplate size in mm (0=ignore) and where extra slack goes (-1..1 per axis) |
| `enable_magnet` | add magnet cavities (defaults to `true` in this file) |
| `style_hole` | 0=none, 1=countersink, 2=counterbore |
| `d_screw`, `d_screw_head`, `screw_spacing`, `n_screws` | only relevant when `style_plate` is one of the screw-together styles — joins adjacent baseplate tiles with screws instead of relying on friction/magnets alone, useful for large multi-tile layouts |
