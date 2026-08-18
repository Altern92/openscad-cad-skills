# Service envelope — <part/assembly name>

Why this file exists: "service-environment load mismatch" (vibration,
thermal cycling, wear, creep, duty cycle) is, per real failure-analysis
literature, one of the two most evidence-backed root causes of real
mechanical failures — and nothing else in this skill's validation chain
checks it, because it's not a geometry question. This file can't verify any
of these fields are *correct*, only force them to be explicitly stated
instead of silently never considered. Fields adapted from NASA's
"life-cycle environment profile" and standard mechanical "design
conditions" practice (2026-08-19 Perplexity research) — not a full
aerospace-grade profile, a minimal version sized for a hobby/solo project.

Fill in every field with a real value, or `TBD` if genuinely unknown —
never silently omit one. `TBD` on something safety-relevant should also be a
`Critical`/`Open` row in the decisions log (`references/planning.md` §1).

| Field | Value |
|---|---|
| Operating mode(s) (normal / startup / abuse / transient) | |
| Load type (static / cyclic / impact / mixed) | |
| Load magnitude / spectrum (force, torque, expected peak vs. typical) | |
| Duty cycle (on-time %, cycles expected over lifetime, rest periods) | |
| Temperature range (operating min/max, storage min/max) | |
| Vibration / shock (source, axis, expected severity) | |
| Environment (humidity, dust, water, chemicals, UV, altitude) | |
| Mounting / boundary conditions (how it's constrained, preload, lubrication) | |
| Assumed lifetime (hours/cycles/years before expected replacement) | |

`scripts/check_service_envelope.py` only checks that this file exists and no
field was left blank (a filled-in `TBD` still counts, silence doesn't) — it
cannot and does not check whether the declared conditions are correct.
