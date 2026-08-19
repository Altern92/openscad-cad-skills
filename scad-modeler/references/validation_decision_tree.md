# Validation decision tree — v2 (2026-08-19)

Quick-reference for "which check applies to my situation right now" — the
skill has ~12 scripts with different triggers (mandatory, opt-in by
file/comment, manual-only), plus two new process stages (intake/analysis and
rules-enforcement). This diagram is a **navigation aid, not the authoritative
source**: the prose in SKILL.md (with its incident citations) and the
referenced documents below are what to trust if this ever drifts out of sync —
check this file's date against the section headers it maps if in doubt, since
nothing regenerates it automatically (2026-08-19).

v2 changes (this revision): added **Stage 0 intake** (brief → requirements
spec) and **Stage 0.5 analysis** (printed-vs-purchased classification +
similar-variant retrieval), added the **change-propagation step** (dependency
DAG — `check_dependencies.py`, see `change_propagation.md`), added the
**rules-enforcement gate** (`check_rules.py` mandatory before the final
report, see `rules_enforcement.md`), and wired the **mechanics stage** to
trigger automatically from `design_manifest.json.motion` (see
`mechanics_and_motion_planning.md`). The validated v1 core (env check,
planning, narrative, `validate_scad.sh --all`, check ordering) is unchanged.

```mermaid
flowchart TD
    Start([Brief: user's detailed description\n+ info from other AIs]) --> Intake[Stage 0 INTAKE\nwrite requirements.json /\ndesign_manifest.json\n→ check_intake.py gate]
    Intake --> Analysis[Stage 0.5 ANALYSIS\n1. classify each component:\nPRINTED vs PURCHASED\n2. retrieve 2-3 SIMILAR\npast variants to adapt\n(embeddings + templates)]
    Analysis --> EnvNew{Toolchain/environment possibly\nchanged -- new machine, updated\nOpenSCAD, updated libraries,\nor never run here before?}
    EnvNew -- yes --> Doctor[doctor.py once\nreports confidence tier]
    Doctor --> Selftest[selftest.py once\nverifies the toolchain itself]
    Selftest --> Design
    EnvNew -- no --> Design{Starting a NEW\nassembly design?}

    Design -- yes --> Arch{3+ parts, or\narchitecture genuinely\nuncertain?}
    Arch -- yes --> Plan["Section 0.5 Planning\nwrite plan.md → check_plan.py"]
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

    Validate --> Motion{design_manifest.json\nhas a motion block?\n(something moves)}
    Motion -- yes --> Mechanics[MECHANICS stage:\nstatic collisions first,\nthen motion_sweep.py\n(see mechanics_and_motion_planning.md)]
    Mechanics --> AllPass
    Motion -- no --> AllPass

    AllPass{All of the above pass?}
    AllPass -- no --> FixSource[Fix at the source,\nre-run validate_scad.sh --all\nfrom the top -- not just\nthe one check that failed]
    FixSource --> Validate

    AllPass -- yes --> Situational["Situational manual checks -- validate_scad.sh\ndoes NOT run these. NOT exclusive: check EVERY\ncondition below independently, run ALL that\napply, in this order (each downstream check\nassumes the upstream one is already clean)"]
    Situational -->|1. part has 2+ named\nsub-modules sharing\none union()?| Subfeature["check_subfeature_overlap.py\n(export sub-modules solo first,\ndeclare fusions with --exempt)"]
    Situational -->|2. assembly has\n3+ positioned parts?| Collisions["check_collisions.py\n(declare press fits etc.\nin joints.json)"]
    Situational -->|3. anything moves\n(gears, hinge, slider)?| Motion2["motion_sweep.py\n(motion block in design_manifest.json)"]

    Subfeature --> ChangeTree
    Collisions --> ChangeTree
    Motion2 --> ChangeTree
    Situational -- none apply --> ChangeTree

    ChangeTree[CHANGE-PROPAGATION:\ncheck_dependencies.py records the\nparam->part dependency DAG;\non ANY edit, dirty-root from the\nchanged variable, recompute only\nthe affected chain in topo order\n(see change_propagation.md)\n-- fallback: full --all re-run]
    ChangeTree --> RulesGate[Rules-enforcement gate:\ncheck_rules.py -- the model MUST\nrun the rules manifest and cite\nits output before reporting\n(see rules_enforcement.md)]
    RulesGate --> Report([Section 8 Final report:\ncheck results + confidence tier +\nwhat is still estimated])
```

## Notes on the new stages

- **Stage 0 / 0.5 are model work, not script work**: the requirement spec and
  the printed-vs-purchased classification are produced by the model, but they
  are *gated* — `check_intake.py` verifies the spec file exists and matches the
  JSON schema before modeling may start. Detail:
  `scad-modeler/references/intake_and_analysis.md`.
- **Mechanics triggers automatically** from `design_manifest.json.motion`;
  static collision check is always a precondition of the motion sweep (sweep
  over already-colliding static geometry is meaningless).
- **Change-propagation does not replace the blanket re-run**: it makes the
  usual case (one parameter edited) cheap and targeted, and escalates to the
  full `validate_scad.sh --all` on any parse uncertainty or when a file `mtime`
  changed. Param-only edits skip rendering entirely.
- **The rules gate is the last thing before the report**: no report without a
  `check_rules.py` run cited in it. This is the enforcement loop that makes
  rule-following independent of model memory.

## Reference files

- `intake_and_analysis.md` — Stage 0/0.5: requirements schema, printed-vs-purchased criteria, variant retrieval.
- `mechanics_and_motion_planning.md` — motion taxonomy, fit tables, design manifest schema.
- `change_propagation.md` — dependency DAG, dirty-root algorithm, user-facing choice-tree output.
- `rules_enforcement.md` — why agents drift, layered enforcement (prompt/gates/self-check/manifest), failure handling.
- `../INCIDENTS.md` — append-only log of real bugs found and fixed.
