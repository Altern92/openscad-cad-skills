<!-- RAG-passport: file=templates/README.md | skill=scad-modeler | applies_to=[templates, copy-into-project, joints, layout, part, plan, service-envelope] | version=2026-09-11 | source=06_RAG_taisykles (T2). Carries applies_to for the JSON template, which cannot hold a comment. -->
# Templates — what to copy, and when

Every file here is a **template to copy into a project**, not to edit in place.
The JSON one carries no comment header (JSON has no comments), so its passport
lives here.

| Template | Copy to | Use when | Passport |
|---|---|---|---|
| `plan.md` | project root `plan.md` | Any assembly with 3+ parts or genuinely uncertain architecture. Gate: `check_plan.py` — fails without 2+ architecture options and a confirmed `Decision` row. | `applies_to=[plan, architecture-options, decision]` |
| `layout.scad` | project `scad/layout.scad` | Every multi-part assembly. Holds each part's position in assembly coordinates via `at()`. | `applies_to=[layout, positions, assembly-coordinates]` `units=mm` |
| `part_template.scad` | `scad/parts/<part>.scad` | Every printed part. Local coordinates, ends in an unconditional top-level call (what makes it render standalone — and why `assembly.scad` must `use` it, never `include` it). | `applies_to=[part-file, local-coordinates, EXPECTED_BBOX, EXPECTED_HOLE, trailing-call]` |
| `joints.json` | project root `joints.json` | Declared contacts between separately-exported parts (press fits, snap fits, gear meshes), plus the `motion` block for anything that moves. Consumed by `check_collisions.py` and `motion_sweep.py`. | `applies_to=[declared-contact, press-fit, gear-mesh, motion, derivation, expected_bounds]` |
| `bores.json` | project root `bores.json` | Any part with a hole that must be open along its whole path (bearing, shaft, fastener). Gate: `check_bore_reachability.py` — a sealed bore is one connected watertight shell and passes every other check. No file = SKIP. | `applies_to=[bore, reachability, sealed-bore, axis-segment]` `units=mm` |
| `attachments.json` | project root `attachments.json` | Any part fastened to another. Gate: `check_attachment.py` — a bare panel with no bosses passes connectivity and dimensions while being impossible to fasten. No file = SKIP. | `applies_to=[attachment, fastening, boss, min-material]` `units=mm` |
| `service_envelope.md` | project root `service_envelope.md` | Parts that need maintenance access, cable routing, or air flow. Gate: `check_service_envelope.py` — fails on a blank field. | `applies_to=[service-envelope, maintenance-access]` |

## Field semantics

The full field set for `joints.json` (`expected_interference_mm`, `derivation`,
`expected_bounds`, `forbidden_regions`, `multi_region_ok`, `joint_type`) is
documented in `../references/validation.md`. `derivation` is **required** whenever
`expected_interference_mm` is declared — a hand-typed range with no stated origin
is how a wrong declaration goes unnoticed.

**Every declaration above is the difference between a check that runs and a check
that reports SKIP.** Measured across 11 real projects on 2026-09-12: `attachment`,
`bore_reachability` and `intake` were SKIP in **all 11**, because no project
had the file. The checkers were written and tested; nothing ever fed them.
