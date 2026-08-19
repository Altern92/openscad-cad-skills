# Validation decision tree

Quick-reference for "which check applies to my situation right now" — the
skill has accumulated ~10 scripts with different triggers (mandatory,
opt-in by file/comment, manual-only), and that decision logic is otherwise
scattered across §0.5, §0.6, and §7's prose. This diagram is a navigation
aid, not the authoritative source: the prose in SKILL.md (with its incident
citations) is what to trust if this ever drifts out of sync with it — check
this file's date against the section headers it maps if in doubt, since
nothing regenerates it automatically when a check's trigger condition
changes (2026-08-19).

Stress-tested against a Perplexity review before being adopted. Two real
gaps that review found are already fixed into the diagram below: the three
"situational" checks (§7 collisions/motion/sub-feature-overlap) are
independent obligations, not a single exclusive choice — a real assembly
commonly needs two or all three at once (a moving, multi-part assembly
built from unioned sub-features needs all three) — and they're ordered
deliberately (sub-feature overlap, then static collision, then motion
sweep) because each downstream check assumes the upstream one is already
clean: an internally-overlapping part makes an assembly-level collision
result meaningless, and a motion sweep is meaningless over static geometry
that already collides. The "new machine" trigger for `doctor.py`/
`selftest.py` was also broadened to "toolchain/environment possibly
changed" (OpenSCAD version, library updates), not literally a new machine.

The rest of that review's suggestions (structural/load validation,
manufacturing/printability checks, coordinate-frame/units audits, a formal
release-approval gate) were **not** incorporated — they're real concerns
for a certified engineering V&V pipeline, but this skill already documents
them as deliberately out of scope: "Still not checked at all: load,
strength, or manufacturability... Both need judgment, a datasheet, or a
physical test — this chain has no way to derive them from geometry alone"
(§7). Scope creep into that territory needs an explicit decision, not a
diagram exercise.

```mermaid
flowchart TD
    Start([Starting or changing work in scad-modeler]) --> EnvNew{Toolchain/environment possibly\nchanged -- new machine, updated\nOpenSCAD, updated libraries,\nor never run here before?}
    EnvNew -- yes --> Doctor[doctor.py once\nreports confidence tier]
    Doctor --> Selftest[selftest.py once\nverifies the toolchain itself]
    Selftest --> Design
    EnvNew -- no --> Design{Starting a NEW\nassembly design?}

    Design -- yes --> Arch{3+ parts, or\narchitecture genuinely\nuncertain?}
    Arch -- yes --> Plan["Section 0.5 Planning\nwrite plan.md -> check_plan.py"]
    Arch -- no --> Calc[Section 1 calculation table]
    Plan --> Calc

    Design -- no, editing\nexisting geometry --> Feature{Does the feature you're\ntouching interface with a\nbearing/shaft/fastener/purchased\npart, OR share a union() with\nanother named feature?}

    Feature -- yes --> Narrative["Section 0.6 narrative\nwrite the 4 answers\n(insertion path, neighbors,\nretention, purchased-part fit)"]
    Feature -- no --> Geometry[Write/edit the geometry]
    Narrative --> Geometry

    Geometry --> Validate["bash validate_scad.sh --all\n(always run after ANY change,\nnot just the thing you touched)"]

    Validate --> Auto[Runs automatically, no\ndeclaration needed]
    Auto --> Connectivity[check_connectivity.py\non every part]

    Validate --> OptIn{Opt-in gates -- run\nONLY IF the file/comment\nexists}
    OptIn -->|calculations.md has\na decisions-log table| Assumptions[check_assumptions.py]
    OptIn -->|service_envelope.md\nexists| Envelope[check_service_envelope.py]
    OptIn -->|part has\n// EXPECTED_BBOX| Dimensions[check_dimensions.py]
    OptIn -->|part has\n// EXPECTED_HOLE| Features[check_features.py]
    OptIn -->|project has\nbores.json| BoreCheck[check_bore_reachability.py]

    Validate --> AllPass{All of the above pass?}
    AllPass -- no --> FixSource[Fix at the source,\nre-run validate_scad.sh --all\nfrom the top -- not just\nthe one check that failed]
    FixSource --> Validate

    AllPass -- yes --> Situational["Situational manual checks -- validate_scad.sh\ndoes NOT run these. NOT exclusive: check EVERY\ncondition below independently, run ALL that\napply, in this order (each downstream check\nassumes the upstream one is already clean --\nan internally-overlapping part makes an\nassembly-level collision result meaningless,\nand a motion sweep is meaningless over\nstatic geometry that already collides)"]

    Situational -->|1. part has 2+ named\nsub-modules sharing\none union()?| Subfeature["check_subfeature_overlap.py\n(export sub-modules solo first,\ndeclare fusions with --exempt)"]
    Situational -->|2. assembly has\n3+ positioned parts?| Collisions["check_collisions.py\n(declare press fits etc.\nin joints.json)"]
    Situational -->|3. anything moves\n(gears, hinge, slider)?| Motion["motion_sweep.py\n(motion block in joints.json)"]

    Subfeature --> Report
    Collisions --> Report
    Motion --> Report
    Situational -- none apply --> Report([Section 8 Final report])
```
