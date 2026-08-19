# openscad-cad-skills

Claude Code skills for parametric OpenSCAD design — from a single part to a
multi-part mechanical assembly, with automated geometry verification before
export.

![Example: single-stage spur gear reduction](scad-modeler/examples/gear_reduction/preview.png)

*A working example — see [`scad-modeler/examples/gear_reduction/`](scad-modeler/examples/gear_reduction/).*

## Why this exists

An LLM can write OpenSCAD code that renders cleanly and still be wrong in
ways a render never shows: a bore sealed behind unbored material, two
sub-features overlapping inside one part's `union()` (invisible, since
`union()` of two overlapping solids is still one valid watertight shell), a
gear pair that's fine at rest but collides 40° into its rotation. Every one
of those is a real, logged incident in [`INCIDENTS.md`](INCIDENTS.md), not a
hypothetical.

**The differentiator: this is the only agent skill setup we know of that
machine-verifies a *moving* assembly** — not just "does this part look
right," but "do these gears/hinge/slider actually clear each other through
the full range of motion," sampled and checked automatically, with the
static-collision precondition, the declared-contact range, and the sweep
itself all wired into one command.

## Skills

| Skill | For |
|-------|-----|
| `openscad-cad` | A single part: an insert, bracket, cover, enclosure, Gridfinity bin. Writing, rendering, exporting, dimensional checks. |
| `scad-modeler` | Multi-part assemblies: gears, bearings, shafts. Adds mandatory calculations before geometry, centralized parameters and positions, collision/clearance/motion checking. |

`scad-modeler` builds on `openscad-cad` — render/export commands and
tolerance data live there. For a single part, use `openscad-cad` directly;
its validation scripts live in `scad-modeler/scripts/` but work fine
against a single part too.

## Quickstart

```bash
git clone https://github.com/Altern92/openscad-cad-skills.git
cd openscad-cad-skills
pip install -r requirements.txt
python3 scad-modeler/scripts/doctor.py     # what this machine can actually do
python3 scad-modeler/scripts/selftest.py   # does the whole chain really work

cd scad-modeler/examples/gear_reduction
bash ../../scripts/validate_scad.sh --all  # render + validate a real 2-gear assembly
```

Then, to use the skills from Claude Code (run this from the repo root):

```bash
cd openscad-cad-skills   # back to the repo root, if you're still in the example dir
ln -s "$PWD/openscad-cad"  ~/.claude/skills/openscad-cad
ln -s "$PWD/scad-modeler"  ~/.claude/skills/scad-modeler
```

DeepSeek Harness (DSH):

```bash
mkdir -p ~/.dsh/skills
ln -s "$PWD/openscad-cad"  ~/.dsh/skills/openscad-cad
ln -s "$PWD/scad-modeler"  ~/.dsh/skills/scad-modeler
ln -s "$PWD/INCIDENTS.md"  ~/.dsh/skills/INCIDENTS.md
ln -s "$PWD/requirements.txt" ~/.dsh/skills/requirements.txt
```

Install both together: `openscad-cad` is referenced by `scad-modeler`'s
scripts, and those in turn use `openscad-cad/references/patterns.scad`. The
DSH frontmatter format is nearly identical (same `name`/`description`
fields); `scad-modeler`'s description can't contain `: ` (colon+space) — DSH
parses that as a YAML key-value pair and rejects the skill.

### Dependencies

OpenSCAD (macOS: `brew install --cask openscad@snapshot` — not the plain
`openscad` cask, which is too old to have the `--backend=Manifold` flag
this skill depends on), plus `xvfb` on headless Linux.

Python, for the validation scripts:

```bash
pip install -r requirements.txt
```

Not all of these are required for every check: `trimesh` is needed for
everything, `shapely` for bore measurement, `python-fcl`/`scipy` for
collisions, `manifold3d` for measuring a declared interference exactly,
`rtree` for bore-reachability scans, `pyyaml`/`jsonschema` for the intake
and rules-enforcement gates. Whatever's missing, the corresponding check is
simply unavailable, and the tools say so (`doctor.py` reports exactly which
checks each missing package unlocks).

## Verify before trusting it

```bash
python3 scad-modeler/scripts/doctor.py      # what this machine can do at all
python3 scad-modeler/scripts/selftest.py    # does the whole chain actually work
```

`doctor.py` detects OpenSCAD, libraries (by their real entry-point file, not
by folder name — a folder with the right name isn't evidence of a working
install), Python packages, and a calibration profile, and reports the
highest confidence tier this environment can support.

`selftest.py` builds a part with answers known in advance, runs the whole
chain, and checks that every tool reaches the right verdict — including that
the bore check **must fail** on a deliberately uncompensated bore. A check
that never fails proves nothing.

## What these skills actually verify

`scad-modeler`'s validation chain, in the order it runs (see
`scad-modeler/references/validation_decision_tree.md` for the full decision
tree — which check applies to which situation):

| Tool | Catches |
|---|---|
| `assert()` in `params.scad` | design invariants — stops the render |
| `check_connectivity.py` | a part silently splitting into disconnected islands (mandatory, no declaration needed) |
| `check_dimensions.py` | overall envelope vs. a declared `EXPECTED_BBOX`, tolerance derived from `$fa`/`$fs`, not a flat percentage |
| `check_features.py` | a bore's actual flat-to-flat size — what a shaft binds on, which a bounding box can't see |
| `check_bore_reachability.py` | a bore that measures correctly at its seat but is sealed behind unbored material somewhere between the seat and the outside |
| `check_subfeature_overlap.py` | two sub-features overlapping inside one part's own `union()` — invisible to every other check |
| `check_collisions.py` | unintended interference, insufficient clearance, and declared contacts checked against real penetration depth (not volume — see below) and against touching in more than one disjoint region |
| `motion_sweep.py` | interference and clearance **through a full motion cycle**, not one static pose, with gear-tooth periodicity collapse and adaptive refinement near the tightest clearance |
| `check_intake.py` / `check_plan.py` / `check_assumptions.py` / `check_service_envelope.py` | the requirements spec, the architecture decision, unresolved critical assumptions, and service-envelope completeness — the failure categories that don't show up in geometry at all |
| `check_dependencies.py` | which downstream parameters/parts a given edit actually affects, so a one-parameter change doesn't require blind faith in a full re-render |
| `check_rules.py` | runs the whole rules manifest and requires its output be cited before a final report — see `references/rules_enforcement.md` for why prompts alone don't hold up under context load |

A declared contact (a press fit, a gear mesh) is checked by **penetration
depth in mm** — the standard quantity for this in contact mechanics and
robotics — not by boolean-intersection volume, which can't be compared to a
linear mm spec without knowing contact area. A pair within its declared
depth range is *also* required to touch in exactly one contiguous region by
default, since a max-over-all-contact-points depth can't otherwise
distinguish one legitimate contact zone from that zone plus a separate,
unrelated structural collision hiding behind the same range — both were
real, confirmed gaps, not hypothetical (`INCIDENTS.md`, 2026-08-19).

## Limits

Confidence tiers are documented in
`openscad-cad/references/confidence-tiers.md`. These skills aim for **Tier
5** — a motion-verified assembly.

Motion checking is **sampling, not proof**: nothing is checked between two
sampled positions. Adaptive refinement catches narrow clashes near the
tightest point, but a narrow clash far from that minimum can still slip
through. State the tier you're relying on.

Not implemented at all:

- **assembly-sequence verification** — a mechanism can pass every check here
  and still be physically un-buildable (see `SKILL.md` §0.6's belt-drive
  incident);
- **load/strength calculations** — without material data, that would be
  arithmetic dressed up as engineering, and printed parts are anisotropic
  in a way generic values don't capture;
- **slicer printability gates** — no mainstream slicer documents
  thin-wall/non-manifold warnings as reachable through a CLI.

Tier 3 and above need a calibration profile: your printer and material's
actual measured deviation. Without one, geometry can be promised, but fit
cannot.

## License

MIT — see [`LICENSE`](LICENSE).
