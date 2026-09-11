<!-- RAG-passport: file=references/validation.md | skill=scad-modeler | applies_to=[validation, gates, connectivity, bbox, holes, collisions, motion, bores, subfeature-overlap, printability] | version=2026-09-11 | source=split from SKILL.md section 7 (progressive disclosure, RAG T3) -->
# Validation cycle — full reference

Moved out of `SKILL.md` §7 on 2026-09-11 (progressive disclosure: the run order and
what each gate catches stays in SKILL.md; the reasoning history, exact declaration
fields, tolerances and edge cases live here). **Nothing was removed** — this is the
verbatim former §7 body.

Read this when: a gate fails and you need the cause; you are declaring `joints.json` /
`bores.json` fields (`expected_bounds`, `forbidden_regions`, `derivation`,
`multi_region_ok`, `joint_type`); you need tolerance derivations or exit-code
semantics; or you are deciding whether a check is wired into `validate_scad.sh` or
manual.

## Contents

| Gate | Wired into `validate_scad.sh --all`? |
|---|---|
| Analytic pre-flight (`assert()` in params.scad) | yes |
| `check_assumptions.py` (calculations.md Criticality) | yes, opt-in by file |
| `check_service_envelope.py` | yes, opt-in by file |
| `check_connectivity.py` | yes, always |
| `check_dimensions.py` (EXPECTED_BBOX) | yes, opt-in by declaration |
| `check_features.py` (EXPECTED_HOLE) | yes, opt-in by declaration |
| `check_collisions.py` | yes, 3+ parts |
| `motion_sweep.py` | yes, when motion declared |
| `check_bore_reachability.py` | yes, opt-in by bores.json |
| `check_attachment.py` | yes, opt-in by attachments.json |
| `check_subfeature_overlap.py` | **no** — manual, needs solo sub-feature STLs |
| `check_printability.py` | **no** — manual, standalone |
| load / strength | **not checked at all** (needs datasheet + material properties) |

---

```bash
bash scripts/validate_scad.sh --all
```

This renders every `.scad` file it finds under `parts/` plus `assembly.scad`,
checks the OpenSCAD install, and fails loudly on an empty STL — see the script for
exact flags (`--hardwarnings`, `--check-parameters=true`,
`--check-parameter-ranges=true` are all confirmed-real flags on the installed
OpenSCAD build, verified via `--help`).

**Before any part is rendered, it runs an analytic pre-flight gate** (added
2026-08-21): every `assert()` in `params.scad` gets evaluated at near-zero
cost (no real geometry, just a trivial placeholder solid so OpenSCAD doesn't
treat a definitions-only file as an empty-object failure). This exists
because the single most expensive class of defect found across every
project this skill has been used on was **purely algebraic** — two circular
features' outer radii summing to more than their actual center distance
(`r1 + r2 > center_distance`) — something one `assert()` line catches for
free, instead of requiring a full render, mesh export, collision analysis,
and human interpretation to discover after the fact (a real case took 12
validation rounds). **Write an `assert()` in `params.scad` for every
geometric relationship you can bound in closed form** (two circles: sum of
radii vs. center distance; two boxes: interval separation on at least one
axis; coaxial parts: axial clearance) **before writing the geometry that
depends on it** — this is not optional bookkeeping, it is the cheapest check
in the entire chain and it runs first.

Before any of that, it also runs two **project-level** gates (once, not per
part), both opt-in by file existence: `check_assumptions.py` fails if
`calculations.md` has any `Criticality: Critical` row in its decisions log
(§0.5/`references/planning.md`) still unresolved, and
`check_service_envelope.py` fails if a `service_envelope.md` exists with a
blank field. These target "unverified initial assumptions" and "service-load
mismatch" specifically — research (2026-08-19) found these to be the two
most evidence-backed root causes of real mechanical failures, and nothing
else in this chain checks either one, since every other check validates
geometry *against* the calculation table, not whether the table's own inputs
were right.

It also runs a **connectivity check** on every part, by default, with no
declaration needed: a single printed part must render as one connected
solid. A fix to one collision can silently break contact between two OTHER
features that used to touch — a leg widened to clear a gear teeth can lose
contact with the disc it was supposed to hold up, while the overall bounding
box and every other check still passes clean (`INCIDENTS.md`, 2026-08-19).
`scripts/check_connectivity.py` catches this via `trimesh`'s connected-body
count; declare `// EXPECTED_BODIES: N` only for the rare part that's
genuinely meant to be more than one disconnected solid in one STL.

It also runs a **bounding-box check** on any part that declares one, catching
the failure mode visual inspection alone misses: a part that renders and
*looks* right but is subtly the wrong size. Declare it in the part file, next
to the part's own dimension variables:

```openscad
// EXPECTED_BBOX: [40, 20, 15]
```

`validate_scad.sh` greps for that comment and, if present, runs
`scripts/check_dimensions.py --stl <rendered.stl> --scad <part.scad>`. The
tolerance is **derived from the model's own facet resolution**, not fixed: per
axis it is `max(tessellation bound, 0.005mm)`, with `$fn`/`$fa`/`$fs` read from
the part file and one level of its `include`s. The former flat
`max(0.3mm, 1%)` was not a tessellation tolerance at all — at `$fa=2, $fs=0.3`
the real mesh error is ~0.003mm at Ø20 and ~0.030mm at Ø200, so it was 10–65×
too loose and would pass a part that was genuinely the wrong size. Pass
`--abs-tol/--rel-tol` to opt back into a flat tolerance for a part whose
declared bbox is deliberately a rounded nominal. No `EXPECTED_BBOX` = skipped.

**A bounding box is nearly blind to the error that actually breaks fits.**
OpenSCAD puts a polygon vertex at angle 0 (verified in upstream
`primitives.cc`), so the bbox touches the ideal radius on any axis where a
vertex lands — it sees the envelope, not the inscribed-polygon *across-flats*
deficit that makes a bore too tight. Green bbox check ≠ the bearing will seat.

For round fit-critical features, declare them and let them be measured:

```openscad
// EXPECTED_HOLE: [0, 0, 5, "Z", 8.0]   // axis point, axis, target across-flats Ø
```

`validate_scad.sh` then runs `scripts/check_features.py`, which slices the mesh
perpendicular to that axis and measures the shortest distance across the bore —
the dimension a shaft actually binds on. Default tolerance 0.05mm. It also
reports across-corners, and when a hole is short flat-to-flat while correct
across corners it names the cause: inscribed-polygon undersizing rather than a
wrong parameter.

How much this matters is entirely a function of facet resolution, which is why
it's worth checking: a Ø8 hole is undersized by 0.006mm at `$fa=2, $fs=0.3` —
negligible — but by **0.233mm at OpenSCAD's defaults**, which is a failed fit
that nothing else in this chain notices. Fix it with `true_hole_d()` from
`openscad-cad/references/patterns.scad` (Pattern 0) or by setting `$fa`/`$fs`
finer. See `references/tolerances.md` for which error layer is corrected where —
this is the CAD layer only, and the printer's own hole bias sits on top of it.

For assemblies of 3+ parts, also run interference/clearance checking:

```bash
python3 scripts/check_collisions.py --min-clearance 0.3 \
    --expected-contacts joints.json build/*.stl
```

It distinguishes three verdicts rather than one boolean, because "do they
overlap?" is the wrong question for a printed assembly:

- **Unintended interference** — overlap with nothing declaring it. Fail. If
  the overlap/gap is very shallow (within `--touch-tolerance`, default
  0.05mm) it's reported instead as **candidate intentional touch** — still
  a fail, but with a ready-to-paste `joints.json` stub, since this shape
  is often a benign design touch (a clamshell split line) that was
  correctly reasoned about but never formalized as a declaration
  (`INCIDENTS.md`, 2026-08-18/2026-08-22). A gap just past that, up to
  `--near-miss-tolerance` (default 0.2mm), is a non-fatal **near miss**
  note instead — that band is more often a real design sensitivity than a
  benign touch, so it's surfaced, not auto-suggested. Both are checked
  unconditionally, not only when `--min-clearance` is passed.
- **Insufficient clearance** — no overlap, but a gap below `--min-clearance`.
  Two parts 0.02mm apart pass a pure overlap test and fuse in the print, so
  without a threshold the check is close to meaningless. Default is 0 (overlap
  only); set it to something the process can actually resolve.
- **Intentional contact** — press fits, snap fits and threads are *supposed* to
  overlap. Declare them in `templates/joints.json` and they are range-checked
  by penetration depth (mm, matching the units `expected_interference_mm` is
  written in) instead of flagged; an undeclared overlap still fails, and a
  declared press fit whose parts don't touch fails too. A pair within range
  is ALSO required to touch in exactly one contiguous region by default — a
  max-over-all-contact-points depth can't tell a legitimate contact zone from
  that same zone plus a separate, unrelated structural collision hiding
  behind the same declared range; confirmed live, not hypothetical: a
  declared gear-mesh contact's overlap split into 7 disjoint regions, one
  entirely outside the meshing feature's own extent (`INCIDENTS.md`,
  2026-08-19). Add `"multi_region_ok": true` on the contact entry only for a
  joint that genuinely touches in several places on purpose (a splined
  shaft, say) — but that only bounds the *count* of regions, not *where*
  they are. For a stronger "contact witness" authorizing only the specific
  location the declaration's own derivation describes, add
  `"expected_bounds"` (added 2026-08-21): an assembly-space bounding box
  every detected region must fall inside, regardless of `multi_region_ok`
  or how many regions there are — a region outside it fails as
  `UNAUTHORIZED CONTACT REGION` even for an otherwise-in-range pair. The
  negative complement is `"forbidden_regions"` (also added 2026-08-21): a
  list of assembly-space boxes a contact must *never* touch, for when the
  legitimate zone is awkward to bound tightly but a specific nearby feature
  must stay untouched regardless of the legitimate zone's shape — checked
  first, failing as `CONTACT IN FORBIDDEN REGION`. `expected_bounds` and
  `forbidden_regions` are independent and combinable. Also since 2026-08-21:
  **`"derivation"` is required whenever `expected_interference_mm` is
  declared** — a non-empty, human-written trace back to the source
  parameters/formula the range came from. A hand-typed range with no stated
  origin is exactly how a wrong declaration goes unnoticed (confirmed in
  this skill's own example project: an initial range was copied from an
  unrelated test fixture rather than derived from the actual gear
  geometry).

Exit codes: `0` pass, `2` degraded (a mesh wasn't watertight, or a declared
interference couldn't be measured — treat as *not checked*, not as pass), `3`
fail, `4` usage error. The non-watertight case previously printed a warning and
carried on while claiming otherwise in its own docstring; FCL results on a
non-watertight mesh aren't trustworthy, so it now changes the verdict. Use
`--strict` to make it a hard fail.

This is **one static pose**. For anything that moves, sweep it:

```bash
python3 scripts/motion_sweep.py --joints joints.json build/*.stl
```

Add a `motion` block to the same `joints.json` (see `templates/joints.json`):
each driver gets an axis, an origin, and a `ratio` — its motion per unit of the
sweep parameter. **Meshing external gears turn opposite ways, so one ratio is
negative**; getting that sign wrong produces a sweep that proves nothing.
Checked automatically since 2026-09-04: for a declared `gear_mesh` contact
whose both parts are also drivers in the same motion block, `motion_sweep.py`
refuses to sweep at all unless the ratios have opposite, nonzero signs —
opt out a genuine same-direction (internal/planetary) mesh with
`"joint_type": "internal_gear_mesh"`.

Give `teeth` on every revolute driver and the sweep collapses to one tooth
pitch — 18° instead of 360° for a 20-tooth gear, a 20× saving — applied only
when every driver agrees on the period, which happens exactly when the gears
really mesh. Declared contacts stay exempt: a press fit is meant to touch.

A coarse pass is followed by fine re-sampling around the tightest position,
because that is where a clash narrower than the step hides. In testing this
mattered: on a swinging arm the worst clearance was not at the obvious 0° but
at 354.5°, where the arm's *corner* passes nearer than its flat end, and only
the refinement pass found it.

**This is sampling, not proof.** A clash narrower than the step and far from the
global minimum can still be missed. Lower `--step-deg` before concluding a
design is clear, and never widen `min_clearance_mm` to make a failure go away.

**None of the above proves a bore is actually reachable from outside the
part.** `body_count==1`/`is_watertight==True` both report clean for a
bearing/shaft bore that is a fully enclosed internal cavity — a sealed
tunnel with no path to any exterior surface — because an enclosed void is
still one connected, perfectly valid watertight shell.
`check_features.py` also reports clean, since it correctly measures the
bore's diameter wherever it's told to probe, regardless of whether that
location can be reached from outside. This is a real, confirmed failure
mode, not a hypothetical: a gearbox frame with three bearing towers built
as a cylinder with a bore drilled perpendicular through its own center
axis passed every check above while every one of those three bores was
sealed behind ~8mm of solid, un-bored material — the part was completely
unassemblable and nothing in this chain said so (`INCIDENTS.md`,
2026-08-19, "bearing bores never reached the tower's true exterior
surface").

For any bore/pocket meant to receive a bearing, shaft, or fastener
**from outside the part after printing**, verify the path is actually
open — a point-containment scan along the bore's own axis, from well
outside the part to the seat position, checking that every sampled point
is NOT inside the solid. `scripts/check_bore_reachability.py` does this:
declare each bore's axis segment (a far-outside start point, the real
seat position as `end`) in a project-root `bores.json`, and
`validate_scad.sh --all` picks it up automatically once that file
exists, checking every rendered part STL. Manually:

```bash
python3 scripts/check_bore_reachability.py --bores bores.json build/*.stl
```

A wall centered exactly on a perpendicular tower's own axis is the
specific geometry that hides this: reaching the tower's true (curved)
exterior takes the tower's *full radius*, not a small fixed buffer, and a
bore that stops short leaves an enclosed cavity that every check above
calls clean. Do this for every bearing/shaft entry point declared in
§4.5, not just the ones that look tight in a render.

**Also not checked by anything above: overlap BETWEEN sub-features
inside the same single part.** `check_collisions.py` only ever compares
separately-exported STLs against each other — by the time two named
sub-modules (a tower, a wall, a boss) are `union()`-ed together and
exported as one part, they no longer exist as distinguishable objects, so
an overlap between them, however large, cannot be flagged: `union()` of
two overlapping solids is still one valid, watertight, single-body shell.
Confirmed: a bearing tower overlapped an unrelated motor-mounting cradle
in the same part by 419mm³, invisible through several rounds of "all
green" validation because both were part of one part's `union()`
(`INCIDENTS.md`, 2026-08-19).

For any part assembled from more than one named sub-module (a tower next
to a wall, a boss next to a cradle, ribs near a boss), export each
sub-module as its own solo STL (same local coordinate system, pre-union)
and check every pair with `scripts/check_subfeature_overlap.py`:

```bash
python3 scripts/check_subfeature_overlap.py sub_features/*.stl
```

Skip a pair only when the overlap is an intentional fusion (e.g. a boss
meant to blend into the tower it mounts on) — declare that explicitly with
`--exempt fusions.json`, the same way `joints.json` declares intentional
contact between separate parts in `check_collisions.py`, rather than
silently excluding it. This needs a mesh boolean engine (`pip install
manifold3d`) to measure overlap volume; without one it reports degraded,
not passed. Not wired into `validate_scad.sh` — solo sub-feature export is
an extra step the part file's author adds deliberately, the same way
assembly-positioned exports are a prerequisite for `check_collisions.py`,
not something the normal per-part render produces on its own.

Still not checked at all: load or strength (needs a datasheet and
material properties this chain has no way to derive from geometry
alone). FDM printability specifically — minimum wall thickness,
unsupported overhang — now has a standalone check (added 2026-08-22,
after independent research confirmed real precedent for both as
pre-slicing, mesh-based checks: face-normal-vs-build-axis for overhang,
ray-cast local thickness for walls):

```bash
python3 scripts/check_printability.py --stl build/part.stl
```

Not wired into `validate_scad.sh --all` — new and not yet battle-tested
at scale, and its wall-thickness measurement has a confirmed, documented
edge case (a thin-wall reading near a sharp edge on a solid, tapered
feature — e.g. a flat cap's rim meeting a steeply sloped side — can be a
measurement artifact of that specific edge geometry rather than a real
thin wall; confirmed reliable on genuine shell/enclosure geometry, where
it measured a real 2mm wall exactly). Minimum FEATURE size (as opposed to
wall thickness) is deliberately NOT checked — the same research found no
real precedent for a pre-slicing algorithm for that specific case; most
real tools defer it to the slicer itself.

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

**After any geometry fix, re-run the whole cycle, not just the check you were
fixing.** A fix for one failure can silently break something else that was
previously fine and that nothing was watching — that's exactly how the
connectivity bug above happened: a leg radius was widened until
`check_collisions.py` said OK, and the session stopped there instead of
re-running `validate_scad.sh --all`, which would have caught the new
disconnection immediately. Stopping at the first green result for the thing
you were looking at is not the same as the part being right.

## Exit codes are NOT uniform across checkers — read this before writing a fixture

A trap worth stating plainly: **half the checkers use exit 1 for a failure, half
use exit 3.** This was found the hard way — two fixtures written in one session
both assumed 3 and both failed, for no reason other than the assumption.

| Exit code | Checkers |
|---|---|
| **1** on failure | `check_assumptions`, `check_connectivity`, `check_dimensions`, `check_features`, `check_plan`, `check_service_envelope` |
| **3** on failure | `check_attachment`, `check_bore_reachability`, `check_collisions`, `check_intake`, `check_rules`, `check_subfeature_overlap` |
| 4 on usage/runtime error | most checkers |
| 2 = degraded | `check_collisions` only — **treat as not checked, not as pass** |

`motion_sweep.py`, `check_margin_provenance.py`, `check_param_context.py`,
`check_printability.py` and `check_dependencies.py` compute their own codes —
read the docstring of the one you are testing rather than guessing.

**Do not "fix" this by changing the codes.** `validate_scad.sh` and any
user-side script branch on these values; a silent renumbering would break them.
The correct move when adding a checker is to document its code and add a fixture
that pins it.

When writing a fixture, do not assume — derive the expected code by running the
checker once and reading what it actually returns. That is what caught both
mistakes above.

---

## Attachment points (`check_attachment.py`, added 2026-09-11)

Every other check in this chain asks whether a part is **correct** — one solid,
the right size, free of collisions, bores that reach. None of them asks the
previous question: **does this part have anything on it to attach with at all?**

Confirmed failure, not hypothetical: a side panel shipped as a bare
3 × 229.7 × 200 mm rectangle with zero attachment features. It passed
connectivity (one solid), dimensions (exactly the declared size) and collision
(a separate finding) while being physically impossible to fasten to anything.
The author had removed the bosses earlier "to make the assembly fit" and never
restored them, and nothing noticed — because connectivity checks whether a part
is one body, never whether that body carries attachment features
(`INCIDENTS.md` 2026-09-11, "side panels: (a) no fastening at all, (b) collided
with the posts"; server_rack_modular_v4 v8).

Declare each fastener's point in a project-root `attachments.json`:

```json
[
  {"name": "side_panel_to_post_front",
   "part": "side_panel",
   "at": [4.5, 20, 15],
   "feature": "m3_boss",
   "min_material_mm": 6.0}
]
```

`at` is in the part's **own local coordinates** (the system the part file is
modelled in and its STL exported from) — this checks the part, not the
assembly. `part` is matched case-insensitively as a substring against each
input STL's basename, the same convention `check_collisions.py` and
`check_bore_reachability.py` use.

`min_material_mm` is optional. With it, a ring of points at half that radius
around `at` is also sampled, which separates a real boss from a sliver that
happens to cross one point. Fewer than half the ring solid reports "likely a
sliver" — advisory wording, because it is not certain.

`validate_scad.sh --all` picks the check up automatically once the file exists,
the same convention `bores.json` uses. A declared point with no material fails
closed: a fastener cannot go through air. Getting the point wrong (declaring it
in assembly coordinates, say) produces a failure, not a false pass — the safe
direction.

Requires `trimesh`, `numpy`, `rtree` (`pip install trimesh numpy rtree`).
Regression fixtures: `tests/fixtures/attachment_missing_fail` (real incident
shape) and `attachment_present_pass` — a true A/B pair on the same declared
point.
