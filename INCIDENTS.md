# Incidents log

Append-only. One entry per real bug found and fixed -- a validation check
catching something wrong, a failure found by actually running or measuring
something, or an inaccuracy found by cross-checking a claim against its
source. This is raw data for a future review pass (Phase 2: periodically read
this log and look for patterns worth promoting into a permanent SKILL.md/
references rule), not curated advice on its own. Don't edit past entries --
if a fix needs revising later, add a new entry that supersedes it and say so.

Not every skill file edit belongs here -- only things that were actually
*wrong* (a bug, a bad test, an inaccurate claim), not routine additions.

## Index

Every incident here is real and was fixed. **Read the entry you need, not the
file.** This list is ~130 lines; the file is 1 500. `grep -n <term> INCIDENTS.md`
works too. Numbers point at each entry's `###` heading.

**2026-09-12** (24)
- file count is not a cost proxy: the optimisation cycle raised cost ~70%  [L272]
- maintainer files were symlinked into the runtime skills dir and agents read them (eval, 40 pa...  [L1348]
- check_connectivity.py reported 2 bodies while printing 3122, and suggested the wrong EXPECTED...  [L1357]
- 6 is ~14 patikru tyliai nepaleidziamos: exit 0 atrodo kaip 'viskas patikrinta'  [L1366]
- ADDENDUM prie tyliu patikru iraso: tikslus skaicius -- 4 checker'iai NEKVIECIAMI IS VISO  [L1379]
- PADENGIMAS SUTVARKYTAS: 8 -> 17 CHECK_RESULT; islindo 3 nematomi dimensions FAIL  [L1395]
- Patikrinti FAIL'ai: 3 skirtingi atsakymai, ir vienas ju pakeicia checker'io kalba  [L1405]
- PREVIEW_FILE: 4 perziuros failai kure klaidingus FAIL'us kiekviena paleidima  [L1419]
- Ertmes, ne kunai: check_connectivity skaite 5 tikras dalis kaip sudužusias  [L1430]
- KLAIDINGAS PASS: dalis, kuri visai nesirenderino, gavo connectivity=PASS  [L1444]
- 8 failai parts/ kataloge yra moduliu bibliotekos, ne dalys  [L1453]
- Vištos ir kiausinio problema: patikra, kuri butu sukūrusi pirma deklaracija, reikalavo deklar...  [L1462]
- bbox tolerancija klydo su minkowski() filletais: 0.0214 mm laikyta defektu  [L1473]
- 8 checker'iai neturejo nė vieno testo; rasdamas juos radau vakuumini PASS  [L1483]
- SKIP be instrukcijos: 8-10 patikru neivyksta ir niekas nesako, ka daryti  [L1493]
- SAKNIS: skill'o darbo eiga niekada neliepe parasyti deklaraciju  [L1503]
- Degeneruota geometrija: 28 nanometru briauna sugadina spinduliu matavimus  [L1512]
- check_subfeature_overlap buvo parasytas, istestuotas ir NIEKADA nepaleistas  [L1522]
- End-to-end testas: ar defektas praeina per VISA grandine, ne per checkeri atskirai  [L1532]
- Nepriklausomas recenzentas: 10 radiniu, visi tikri, visi pataisyti  [L1541]
- Tylus false negative mano pačiame tripwire: inline parseris krito i `// echo 0`  [L1559]
- Penki verdiktai vietoj dvieju: printability buvo PAVADINTAS SKIP, nors IVYKO  [L1569]
- Cover ataskaita, neigiami irodymai ir pervasiveness (isleista is tyrimo)  [L1583]
- INCONCLUSIVE per platus: tuscias motion masyvas duoda klaidinga teigiama  [L1594]

**2026-09-11** (5)
- FULL plan: stash landing + retrieval.md + organic passports + SCAD golden seed + T8 research  [L138]
- golden set was too easy to measure anything (eval, N=10)  [L293]
- RAG hardening: references without metadata passports + modeler description over 1024 chars  [L321]
- sonines plokstes: (a) be jokio tvirtinimo, (b) kirtosi su stulpais (server_rack_modular_v4/v8)  [L1304]
- static PNG render is not a sufficient evaluation channel (server_rack_modular_v4 v8)  [L1340]

**2026-09-10** (7)
- v4 darytas be pilno skill-loading: organic tik skaitytas, ne krautas (salmas_romenu)  [L1283]
- v6/v7 sokinejo prie geometrijos be uzsaldyto speco (server_rack_modular_v4)  [L1290]
- top projekcija melavo apie flansu kolizija (server_rack_modular_v4 v7)  [L1297]
- 45deg flanges appeared in geometry with no requirement behind them (server_rack_modular_v4 v7)  [L1312]
- unexplained circle ("kas tas ratas random") visible in render (server_rack_modular_v4 v7)  [L1319]
- user had to ask whether the skill was actually loaded; procedure ran from read files (server_...  [L1326]
- tiered validation available but only partially used (server_rack_modular_v4 v7/v8)  [L1333]

**2026-09-09** (3)
- BOSL2 overrides translate(), breaks pts[i] indexing in shared templates (openscad-organic)  [L1262]
- helmet modeled from imagination, no research, wrong proportions (salmas_romenu)  [L1269]
- v2/v3 vis dar ne galea: brezinys sako viena, kodas skaiciuoja kita (salmas_romenu)  [L1276]

**2026-09-08** (15)
- used openscad-cad alone for 14-part assembly, ignored dual-skill rule (cnc_control_enclosure v2)  [L1157]
- never read canonical INCIDENTS.md before modelling (cnc_control_enclosure v2)  [L1164]
- wrote 11 entries to wrong INCIDENTS.md, duplicated log (cnc_control_enclosure v2)  [L1171]
- wall_side louver slots merged into one opening (cnc_control_enclosure v2)  [L1178]
- wall_side() ignored -D side override, L/R identical (cnc_control_enclosure v2)  [L1185]
- wall_side outer length poked past front/rear walls (cnc_control_enclosure v2)  [L1192]
- corner brackets poked through walls in assembly (cnc_control_enclosure v2)  [L1199]
- assembly walls had zero fastening, butt-placed only (cnc_control_enclosure v2)  [L1206]
- lid gravity-held, bosses referenced deleted posts (cnc_control_enclosure v2)  [L1213]
- hardware.scad single trailing call, siblings unexportable (cnc_control_enclosure v2)  [L1220]
- STLs in wrong dir, bbox glob silently empty (cnc_control_enclosure v2)  [L1227]
- binary STL parser on ASCII STLs, silent empty (cnc_control_enclosure v2)  [L1234]
- -D via is_undef ignored, snapshot is_undef broken (cnc_control_enclosure v2)  [L1241]
- SUPERCEDES: prior-day review corrections (cnc v2 entries)  [L1248]
- coupon series instead of single version, plastic wasted (cnc_control_enclosure)  [L1255]

**2026-09-04** (8)
- check_margin_provenance.py gained a second detection mode after re-reading INCIDENTS.md turne...  [L328]
- 13 tracked skill files found silently emptied to 0 bytes (not caused this session), restored ...  [L379]
- motion_sweep.py gained a gear-ratio sign sanity check (Muse skill-analysis recommendation)  [L419]
- beam default len 211 vs computed 216.5/191 (server_rack, part4)  [L1122]
- top_panel magnet walls inverted 0.6/0.8, D21 (server_rack, part4)  [L1129]
- Task 4 ternary-offset countersink outside solid (server_rack, part4)  [L1136]
- glue-in pocket only -Y, +Y panel had nothing (server_rack, part4)  [L1143]
- assembly not fully watertight, 5 of 53 shells at corners (server_rack, part4)  [L1150]

**2026-08-30** (1)
- dovetail bowtie, impossible 50deg angle (server_rack, part3)  [L1115]

**2026-08-26** (6)
- dovetail tail/socket offset 6mm, 5 separate bodies, D25/D27 class (server_rack, part3)  [L1073]
- magnet pocket coincident faces, negative-volume fragments (server_rack, part3)  [L1080]
- top dovetail socket covered top EIA hole (server_rack, part3)  [L1087]
- NAS as one welded body, top plate bridge in air (server_rack, part3)  [L1094]
- NAS posts welded with glue-in magnets, wrong system (server_rack, part3)  [L1101]
- nas_side_panel pocket open to inner face, D33 (server_rack, part3)  [L1108]

**2026-08-23** (3)
- 1U 44.5 vs EIA-310 44.45, error propagated, D17 (server_rack, part2)  [L1052]
- 2U meant outer height, interior only 1.37U, D18 (server_rack, part2)  [L1059]
- NAS bay interior 194 to 170, bottom ring 14 to 5, D19-D20 (server_rack, part2)  [L1066]

**2026-08-22** (10)
- persisted a regression suite for this skill's own checker scripts (tests/run_all.sh)  [L456]
- added FDM printability checks (check_printability.py, R-17), grounded in an independent deep-...  [L490]
- named a recurring gap shape found across the day's fixes: passive correctness without an acti...  [L559]
- added a parameter context manifest (use_param() + check_param_context.py, Phase-2 Pattern 3)  [L587]
- check_collisions.py gained clash classification and auto-suggested joints.json stubs (Phase-2...  [L633]
- EIA holes bored through wrong axis, D12 (server_rack, part2)  [L1017]
- EIA wall only 0.29mm, unprintable, D13 (server_rack, part2)  [L1024]
- socket bore 3.4mm instead of 8.38mm, D14 (server_rack, part2)  [L1031]
- flush recess on every module made 3.15mm gaps, D15 (server_rack, part2)  [L1038]
- intermediate ring closed on 4 sides, 28mm band at seam, D16 (server_rack, part2)  [L1045]

**2026-08-21** (10)
- check_dependencies.py gained requirement-influence cross-referencing (P1 decision-tree optimi...  [L677]
- added an analytic pre-flight gate, a provenance requirement, and a spatial "contact witness" ...  [L710]
- edit classification (C1-C5) and forbidden_regions added (P2 decision-tree optimization)  [L768]
- added a validation-run log (scripts/validation_log.py) after a real reconstruction attempt lo...  [L816]
- added calibration_coupon() and a proactive-proposal rule (R-14) after the model only offered ...  [L858]
- P1S bed limit, 250mm too close to 256mm (server_rack, part1)  [L982]
- hidden screw channel crossed EIA holes (server_rack, part1)  [L989]
- shelf_plate stayed square after module went rectangular, D8 (server_rack, part1)  [L996]
- EIA slot extension merged with magnet pocket, D11 (server_rack, part1)  [L1003]
- flush recess detached spigots from posts (server_rack, part1)  [L1010]

**2026-08-19** (2)
- a BOSL2 gear positioned through layout.scad's at() failed under --hardwarnings; a plain guess...  [L901]
- check_collisions.py's declared-contact verdict has no spatial awareness: a legitimate contact...  [L956]

### 2026-09-11 -- FULL plan: stash landing + retrieval.md + organic passports + SCAD golden seed + T8 research
- **Where:** PLAN-2026-09-11-VISI-tobulinimai.md (5 fazės A–E).
- **Fix:** A) 7 stash įrašai append-only (+50, jokių trynimų); B) references/retrieval.md rodyklė; C) organic 2 pasai + 4 CHUNK; D) golden_scad_10.json + EVAL_SKETCH.md; E) DESIGN_T8.md verdict (CSG-eksportas, ne kompiliatorius). Testai 13/13.
- **Already promoted to a rule?** yes — retrieval.md yra rodyklė (T3).

## Pattern analysis (Phase 2, 2026-08-19)

First real pass over the accumulated log (9 entries, 2026-08-16 to
2026-08-19) -- three recurring patterns, not just isolated incidents. For
each: the concrete mechanism Perplexity research turned up, honestly ranked
by precedent strength. **None of this is implemented yet** -- research and
write-up only, per explicit instruction; do not build from this section
without a separate go-ahead.

### Pattern 1 -- a declared/documented value drifts from what the live code
actually computes, after the live computation is upgraded

**Status (2026-08-22): implemented**, though as the "solo-scale guard"
variant described below, not the full shared-helper-function convention
-- see the 2026-08-22 entry in Entries for what was actually built and
tested (`scripts/check_margin_provenance.py`, R-15).

Instances: CD1/CD2 vs `gear_dist()` (below), `EXPECTED_BBOX` Z rounding
(below), `jackshaft_bearing_wall_at_diff` assert omitting real clearance
terms (below). Three of nine entries -- the strongest cluster in the log.

**Proposed mechanism** (moderate precedent -- fits "contract programming" /
dependency-integrity thinking, not a single named standard): stop writing
safety margins as separate handwritten numbers. Make the margin a function
that *calls the same helper function* the real geometry-cutting code calls
for its clearance terms, so there is no parallel arithmetic to drift apart
in the first place:

```scad
function shaft_clearance(d_nom, fit_class, printer_bias) =
    d_nom + fit_delta(fit_class) + printer_bias;
function shaft_safety_limit(...) =
    shaft_clearance(...) - safety_subtraction(...);
assert(shaft_safety_limit(...) > min_wall,
       str("shaft_safety_limit=", shaft_safety_limit(...)));
```

Solo-scale guard version (no full parser needed): a small script that scans
`.scad` files for `assert(`/`EXPECTED_*` and checks whether the formula it
references shares a helper-function name with the "live" formula used
elsewhere for the same quantity -- a lightweight dependency map, not full
static analysis.

### Pattern 2 -- a correctly-reasoned intentional contact (e.g. a clamshell
split line) never gets formalized into the declaration file meant to check
for exactly it

**Status (2026-08-22): implemented**, except the stability sub-check
(re-render with a jittered parameter to see if a verdict flips) --
explicitly out of scope, needs a real re-render per candidate pair. See
the 2026-08-22 entry in Entries (`check_collisions.py`
CANDIDATE INTENTIONAL TOUCH / NEAR MISS).

Instance: `check_collisions.py` failing on `gearbox_case_bottom`/`top`
(below) despite the touch being correctly identified as benign during the
original design session.

**Proposed mechanism** (most bespoke of the three -- no single standard
pattern, but aligned with BIM/CAD clash-tolerance practice): don't just
report "collision" -- classify the event (interference / contact / near
miss) and auto-suggest a declaration stub for human confirmation instead of
relying on someone remembering to write one by hand:
- overlap volume > 0 → real interference, flag as before.
- overlap volume == 0 and separation ≤ a touch tolerance (~0.02-0.05mm for
  printed parts) → candidate intentional touch, auto-generate a
  `joints.json` stub (part pair, `intentional_touch`, evidence, tolerance
  used) for the human/agent to confirm rather than hand-write from scratch.
- small positive gap below a separate, larger near-miss tolerance
  (~0.1-0.2mm) → flag as a near-miss, do NOT auto-declare (this is likely a
  real design sensitivity, not a benign touch).
- stability check: if a tiny parameter jitter flips the verdict between
  touch and overlap, treat it as a real problem, not benign -- don't
  auto-suggest in that case.

### Pattern 3 -- one shared params.scad variable is referenced by multiple
parts that each have a DIFFERENT real hard constraint, and only one
context's constraint gets checked

**Status (2026-08-22): implemented**, matching the proposed mechanism
closely (`use_param()` + a checker scanning for a matching assert() per
declared context). See the 2026-08-22 entry in Entries
(`scripts/check_param_context.py`, R-16). All three patterns from this
2026-08-19 pass are now implemented as of the same day.

Instance: `axle_d=6mm` shared across the diff-side stub (photo-measured,
~6mm) and the wheel_hub end (MR105 bearing, fixed 5mm ID) (below) -- only
the diff-side context was ever actually verified against.

**Proposed mechanism** (strongest precedent of the three -- directly maps to
established CAD constraint-dependency-graph research and to dependency
tracking in systems like PostgreSQL, which won't let you break an object
with unresolved dependents): a parameter provenance/context manifest. Each
part file that consumes a shared parameter for a hardware-fit purpose
declares which context and which constraint it's satisfying:

```scad
use_param("axle_d", "diff_stub_end", "photo_measured_~6mm");
use_param("axle_d", "wheel_hub_bearing_end", "press_fit_MR105_bore5mm");
```

A small checker scans for every parameter referenced by ≥2 `use_param()`
contexts and fails if any context's declared constraint was never actually
exercised by a matching `assert()` nearby -- catching exactly the failure
mode where one end of a shared dimension was checked and the other was
silently assumed compatible. Doesn't require a full requirements-
traceability system -- "no shared parameter may fan out into multiple hard
constraints without a manifest entry (and a real assert) for each fan-out."

### If/when this gets built

Perplexity's own suggested build order, if these get implemented later:
(1) the shared-helper-function convention for Pattern 1 (cheapest, closes
the strongest cluster), (2) the clash classifier + auto-suggest for Pattern
2, (3) the parameter context manifest for Pattern 3 (most novel tooling,
build last). Not scheduled -- logged here for when there's a go-ahead.

## Entry format

```
### YYYY-MM-DD -- <one-line what broke>
- **Where:** <file/project>
- **Symptom:** <what was observed>
- **Root cause:** <why, once diagnosed>
- **Fix:** <what changed>
- **Already promoted to a rule?** <yes, in <file> / not yet>
```

## Entries

### 2026-09-12 -- file count is not a cost proxy: the optimisation cycle raised cost ~70%

- **Where:** this skill library, measured on the golden_scad eval (10 cases x 3 runs x 2 library versions).
- **Symptom:** an earlier report claimed the RAG-hardening cycle cut search cost by 52%
  (8.0 -> 3.8 files read). Re-measuring with real token counts from the DSH session
  `usage` records showed the opposite: **+70% tokens** (median +68%, 6 clean matched
  pairs), **+67% steps**, **+67% tool calls**. Every component rose: fresh input +17%,
  cache read +68%, output +299%.
- **Root cause:** the "files read" figure came from the agents' own self-reported file
  lists, not from the harness. Fewer files were named, but those files are bigger --
  `references/validation.md` (397 lines, added this cycle), 12 new INCIDENTS entries
  (file now 1173 lines), `NEXT.md`, `templates/README.md`, 22 passports. Fewer, larger
  files: file count went down while context volume went up.
- **Fix:** never use a self-reported count as a cost metric. Read token usage from the
  session records (`assistant/chunk` -> `chunk.type == "usage"`). This matches the
  literature: arXiv 2602.11988 found context files raise inference cost >20% with no
  task-success gain.
- **Open question:** which change caused it. Needs one-at-a-time ablation (drop
  NEXT.md / truncate INCIDENTS.md / remove passports) before the cost can be reduced.
- **Already promoted to a rule?** yes -- this entry, plus `golden_scad/KOSTAI_2026-09-12.md`.

### 2026-09-11 -- golden set was too easy to measure anything (eval, N=10)

- **Where:** `golden_scad/golden_scad_10.json`, pre/post comparison of the
  RAG-hardening cycle (`golden_scad/PRES_PO_2026-09-11.md`).
- **Symptom:** the same 10 questions were run against the library BEFORE and AFTER
  a whole cycle of changes (passports, SKILL.md section split, retrieval.md, new
  rules, new checker). Both arms scored **100% on answer correctness**. The metric
  that was supposed to show improvement showed nothing.
- **Root cause:** the questions were answerable from general OpenSCAD knowledge and
  a single obvious file. A discriminating eval needs cases where the "before"
  library genuinely cannot produce the right answer -- a question requiring the
  right one of two similar references, a chunk found by `applies_to` rather than
  by filename, or a trap where a plausible-but-wrong answer exists.
- **What DID move:** source attribution (83% -> 100% evidence recall) and search
  cost (8.0 -> 3.8 files read per answer, -52%). So the cycle made answers cheaper
  and better-grounded, not more correct -- a real but different gain.
- **Also found:** one case (SCAD-05) was not a valid control at all: the
  `openscad-organic` skill was untracked in git, so the `git worktree` "before"
  version lacked a file that existed on disk. The eval measured the worktree
  setup, not the library. And two rubric wordings of mine (Lithuanian diacritics:
  `kalibracij` vs `kalibravimas`) under-scored the "before" arm by 15pp until
  fixed -- an evaluator's own wording is a source of measurement error.
- **Fix:** before trusting a golden set, check it discriminates -- run both arms and
  confirm the score actually differs. If both are 100%, the set measures nothing.
  Needs ~30 cases and deliberately hard ones.
- **Already promoted to a rule?** no -- this entry is the rule.


### 2026-09-11 -- RAG hardening: references without metadata passports + modeler description over 1024 chars
- **Where:** `openscad-cad/references/*` (4 files), `scad-modeler/references/*` (8 files), `scad-modeler/SKILL.md` frontmatter.
- **Symptom:** no chunk carried its own retrieval identity (file/section/applies_to/version) — model had to read whole files to find one table (R-002 distraction); `scad-modeler` description 1311 chars exceeded Anthropic 1024 limit (R-020).
- **Root cause:** references written as human docs, not retrievable chunks; description grew by accretion without limit check.
- **Fix:** RAG-passport headers on 12 files; CHUNK markers on patterns.scad P0–P5 (comments only, parse verified); abstention rule in confidence-tiers.md; description trimmed 1311→865 chars (meaning preserved). Plan: PLAN-2026-09-11-RAG-taisykles.md; synthesis: 06_RAG_taisykles (reviewer R01 6/6).
- **Already promoted to a rule?** yes — passports + abstention are the rule (T2/T4).

### 2026-09-04 -- check_margin_provenance.py gained a second detection mode after re-reading INCIDENTS.md turned up a matching, independent real incident
- **Where:** `scad-modeler/scripts/check_margin_provenance.py`, `SKILL.md`,
  `scad-modeler/tests/fixtures/margin_wrong_variable_fail`/`_pass`.
- **Motivation:** asked to re-read this log for anything new, found an
  entry appended by a different session on 2026-09-02 (`nas_deck_v3`,
  `server_rack_modular_v3` -- a project this repo has no other connection
  to) that its own author had already flagged as matching this same
  file's 2026-08-18 `jackshaft_bearing_wall_at_diff` pattern, but noted
  "not yet promoted to a rule." Confirmed against the real (already
  human-fixed) file: `_deck_socket_depth` (new, deck-specific, actually
  used by the socket-cutting geometry) was introduced, but the assert
  meant to guard it kept referencing the older, same-family
  `_socket_depth`/`post_socket_depth` -- a "passing" assert that proved
  nothing about the value actually cut. This is TWO independent real
  incidents in the same defect family now (different projects, different
  sessions), which is the same "2+ instances = a real pattern" bar the
  2026-08-19 Phase-2 analysis originally used -- stronger evidence than
  anything from the separate `research_2026_scad_llm/` literature pass,
  and found simply by re-reading this log with fresh eyes as asked.
- **Fix:** `check_margin_provenance.py`'s existing clearance-omission
  check (cross-file: params.scad assert vs parts/*.scad geometry) doesn't
  cover this shape -- the `nas_deck_v3` bug is intra-file (assert,
  shadowed local variable, and geometry all in one part file) and the
  variable names involved (`_socket_depth`) don't end in any of the
  existing `_clearance`/`_fit`/`_bias`/`_offset`/`_backlash` suffixes. A
  new, independent detection mode was added: for every geometry-consumed,
  dimensionally-named local variable (`_depth`/`_thickness`/`_clearance`/
  `_fit`/`_bias`/`_offset`/`_backlash`/`_gap`/`_pitch`/`_margin`/`_wall`-
  suffixed) with no assert() of its own, check whether a "same-family"
  sibling variable -- same name core after stripping one leading
  qualifier segment (`post_socket_depth` and `_deck_socket_depth` both
  normalize to `socket_depth`) -- DOES have one; if so, flag it. Runs
  across `--scad` and every file under `--parts-dir` independently (the
  bug is local to one file's own variable shadowing). Same
  `// MARGIN_EXCLUDES_OK: <var>` opt-out as the first mode.
- **Tested:** a direct synthetic reproduction of the real `nas_deck_v3`
  bug shape (assert on `_socket_depth`, geometry uses `_deck_socket_depth`,
  no assert on the latter) correctly fails, naming the exact variable and
  citing this incident; the same fixture with the real fix applied
  (matching the actual current file's own two asserts) correctly passes.
  Full existing regression suite (the other 11 fixtures, unrelated to
  this mode) stays clean -- no regression in the first detection mode.
  Full `validate_scad.sh --all` against the real `gear_reduction` example
  (now scanning both `params.scad` and every `parts/*.scad` file for this
  mode too) stays a clean pass -- no false positive on real, unrelated
  code.
- **Already promoted to a rule?** Yes -- fixed directly in
  `check_margin_provenance.py`; already covered by the existing R-15
  (same script, same `CHECK_RESULT margin_provenance` gate) -- no new
  rule number needed.

### 2026-09-04 -- 13 tracked skill files found silently emptied to 0 bytes (not caused this session), restored from git HEAD
- **Where:** `scad-modeler/examples/gear_reduction/params.scad` and
  `parts/spur.scad`, `scad-modeler/references/mechanics_and_motion_planning.md`,
  `scad-modeler/references/validation_decision_tree.md`,
  `scad-modeler/templates/part_template.scad`, `scad-modeler/tests/README.md`
  and 8 of its fixture files.
- **Symptom:** running `validate_scad.sh --all` against the real
  `gear_reduction` example failed at the mechanics stage with `WARNING:
  Ignoring unknown variable "center_distance" in file layout.scad` --
  tracing it back, `params.scad` (which defines `center_distance`) was 0
  bytes on disk. `git status` then showed 13 tracked files across this
  skill modified relative to HEAD, ALL of them 0-byte on disk while HEAD
  held correct, already-pushed content; mtimes clustered around
  2026-08-19 21:07-22:43 and 2026-08-22 13:06 -- not a single event, and
  not something this session did (motion_sweep.py and INCIDENTS.md, the
  only files actually being edited this session, were untouched and
  correct).
- **Root cause:** not conclusively diagnosed (out of scope to root-cause
  from inside this skill), but circumstantially consistent with the
  iCloud file-eviction risk already flagged elsewhere in this repo's own
  git history (a separate commit this same day: "iCloud eviction rizikos
  irasas i HANDOFF") -- a subset of tracked files silently losing their
  local content while git's own index/objects (and the GitHub remote)
  stayed correct is exactly that failure shape, not a deliberate edit or
  a git operation (git itself never produces a 0-byte file from a
  non-empty commit without an explicit write).
- **Fix:** `git checkout -- <13 files>` restored all of them from HEAD
  (safe: every one was either pre-existing committed project content or
  this session's own already-committed-and-pushed work, not uncommitted
  work that could be lost). Re-verified: the persisted regression suite
  (`tests/run_all.sh`) and a full `validate_scad.sh --all` run against
  `gear_reduction` both pass clean after the restore.
- **Already promoted to a rule?** Not yet -- this is an environment/
  storage-layer risk, not something `check_rules.py` can gate from
  inside a single project's validation run. Worth a periodic `git status`
  --  or a checksum manifest -- sanity check on this skill repo
  specifically, given it's the one most actively edited across sessions;
  logged here as a concrete, dated instance of the already-tracked risk,
  not a new one.

### 2026-09-04 -- motion_sweep.py gained a gear-ratio sign sanity check (Muse skill-analysis recommendation)
- **Where:** `scad-modeler/scripts/motion_sweep.py`, `SKILL.md`,
  `scad-modeler/tests/fixtures/motion_sign_fail`/`_pass`/`_internal_optout`.
- **Motivation:** an independent literature-and-skill-analysis research
  pass (`research_2026_scad_llm/`, using Muse Spark 1.3 Contributor to
  read the full `scad-modeler` `SKILL.md`) flagged that this script's own
  docstring had warned "getting the sign wrong is the easy mistake --
  meshing external gears turn opposite ways" since it was first written,
  but nothing ever actually checked it: a same-sign ratio on a declared
  `gear_mesh` pair produces a sweep that "passes" without the two gears'
  relative motion ever meaning what real meshing teeth would -- a
  misleadingly clean result on a mechanism that may not work at all.
- **Fix:** `check_gear_mesh_signs()` runs before any mesh is loaded or
  swept: for every declared `gear_mesh` contact whose both members are
  also drivers in the same `motion` block, requires opposite-sign,
  nonzero ratios. Deliberately scoped to `joint_type == "gear_mesh"` only
  -- a `worm_mesh`'s ratio relationship isn't a simple sign rule (large
  reduction across non-parallel axes), and a genuine internal/planetary
  mesh legitimately turns same-direction; declaring
  `"joint_type": "internal_gear_mesh"` opts a pair out of this check
  without disabling anything else about it.
- **Tested:** three fixtures added to the persisted regression suite --
  a same-sign reproduction of the real `pinion`/`spur` pair's shape
  (correctly fails, before any STL is even loaded, since fake STL paths
  were used deliberately to prove the check runs first); the same pair
  with the correct opposite signs (correctly passes the sign check,
  fails later only for the expected fake-STL reason); and an
  `internal_gear_mesh`-declared same-sign pair (correctly opts out).
  Full `validate_scad.sh --all` against the real `gear_reduction`
  example (whose `joints.json` already used the correct signs) stays a
  clean pass.
- **Already promoted to a rule?** Yes -- folded into the existing R-09
  (motion sweep, already auto-triggered via `validate_scad.sh --all`'s
  `mechanics` `CHECK_RESULT`); no new rule number needed since this
  strengthens what R-09 already gates rather than adding an independent
  check.

### 2026-08-22 -- persisted a regression suite for this skill's own checker scripts (tests/run_all.sh)
- **Where:** `scad-modeler/tests/` (new: `run_all.sh`, `README.md`, 8
  fixtures), `SKILL.md`.
- **Motivation:** the same deep-research pass that produced R-17 (see
  entry above) was also asked to critique this skill's own architecture
  independently. It named, among a few redundant/already-satisfied
  suggestions, one concrete and correct gap: every new checker this
  session (`check_margin_provenance.py`, `check_param_context.py`,
  `check_printability.py`, the `check_collisions.py` clash classifier)
  had been tested exactly once against a synthetic fixture built in a
  scratch directory, then deleted right after the commit -- real
  verification at the time, but nothing to catch a future regression.
- **Fix:** `tests/run_all.sh` iterates `fixtures/*/run_test.sh`, each a
  self-contained reproduction (mostly of REAL incidents already in this
  log) that renders whatever it needs and asserts a specific checker's
  exit code (and, where useful, a specific string in its output). Seeded
  with 8 fixtures covering everything built today: `margin_provenance_
  fail`/`_pass` (the real `jackshaft_bearing_wall_at_diff` incident,
  2026-08-18, both broken and fixed), `param_context_fail`/`_pass` (the
  real `axle_d` incident, 2026-08-18, both broken and fixed),
  `printability_overhang_fail`, `printability_wall_fail`,
  `collisions_candidate_touch`, `collisions_near_miss`. Deliberately not
  backfilled for every pre-existing checker at once (`check_connectivity.py`,
  `check_bore_reachability.py`, `expected_bounds`/`forbidden_regions`,
  etc.) -- documented in `tests/README.md` as "add one the next time you
  touch that script," the same anti-speculative-build discipline already
  applied elsewhere in this project.
- **Tested:** the suite itself -- all 8 fixtures pass (`8 passed, 0
  failed`), confirming both directions of each `_fail`/`_pass` pair
  actually distinguish "the check works" from "the check always
  fails"/"always passes."
- **Already promoted to a rule?** Yes -- fixed directly; `tests/` is now
  the standing convention for any future checker change.

### 2026-08-22 -- added FDM printability checks (check_printability.py, R-17), grounded in an independent deep-research pass rather than a caught incident
- **Where:** `scad-modeler/scripts/check_printability.py` (new),
  `scad-modeler/rules_manifest.yaml` (R-17), `scad-modeler/SKILL.md` §7,
  `openscad-cad/SKILL.md` §4.5.
- **Motivation:** unlike every other entry in this log, not a caught bug
  -- a genuinely new capability, added after a deep-research pass was
  explicitly asked to find real, citable precedent (not just restate this
  project's own design) for pre-slicing FDM printability checks. The
  research graded its own findings honestly: overhang-angle and
  wall-thickness both "Strongest Precedent" (direct geometric techniques
  used in real tools -- face-normal-vs-build-axis for overhang, as
  Autodesk Meshmixer's "Overhangs" tool does; ray-casting for local wall
  thickness, a simpler alternative to full medial-axis-transform
  skeletonization); minimum feature size explicitly "No Strong Precedent
  Found" for a pre-slicing algorithm and NOT implemented as a result --
  most real tools defer that specific check to the slicer itself.
- **Fix:** `check_printability.py`, using only `trimesh` (already a
  dependency, via its ray-triangle intersector -- confirmed working
  without `pyembree` installed, using the pure-Python fallback). Two
  checks: (1) overhang -- flags downward-facing triangle area steeper
  than `--overhang-deg` (default 45) from vertical, EXCLUDING faces
  resting on the build plate itself (see bug below); (2) wall thickness
  -- samples up to `--wall-samples` face centroids, casts a ray inward
  along each face's own normal, flags any measured thickness below
  `--min-wall` (default 2x `--nozzle-d`, 0.8mm at the 0.4mm default).
  Standalone, not wired into `validate_scad.sh --all` -- new, not yet
  battle-tested at scale, and R-17 (manual) requires a human/agent read
  of the result rather than a bare pass/fail given the limitation below.
- **Bug found and fixed during testing (before this ever shipped):** the
  first version flagged a plain 20mm cube's own flat BOTTOM face as an
  "unsupported overhang" -- its normal points straight down, which the
  naive check correctly measured as "facing down" but wrongly treated as
  floating, when it's actually resting directly on the build plate and
  needs no support by definition. Fixed by excluding any downward face
  whose height along the build axis is within `--baseplate-eps` (default
  0.05mm) of the mesh's own minimum height. Re-tested: the same cube now
  correctly reports zero overhang area.
- **Confirmed limitation (not fixed, documented instead):** wall-thickness
  ray-casting can report a spuriously short distance near an EDGE where
  two non-parallel surfaces meet -- confirmed directly on a solid,
  non-hollow cone: its flat top cap measured a 0.13mm "thickness" near
  its rim, purely because the ray (cast along the cap's own straight-up/
  down normal) grazed the adjacent steeply-sloped side surface a short
  distance below, not because the part is actually thin there. Confirmed
  the technique IS reliable on genuine shell/enclosure geometry: a real
  2mm-wall box measured exactly 2.000mm with no artifacts at its own
  corners. Documented in the script's own docstring and both SKILL.md
  cross-references rather than engineering around it (would need a more
  sophisticated technique -- dual-direction ray averaging or true
  medial-axis analysis -- explicitly out of scope for this pass).
- **Tested:** a plain cube (clean pass after the baseplate-exclusion
  fix); a uniform 0.3mm-wall shell (correctly fails, measuring exactly
  0.300mm); a uniform 2mm-wall shell (correctly passes, measuring
  exactly 2.000mm, confirming no false positives at box corners); a
  gently-tapered cone at 33° from vertical (correctly does NOT flag
  overhang -- within the printable range, confirming the angle math
  isn't just "any downward slope fails"); a steeply-tapered cone at 77°
  from vertical (correctly DOES flag overhang, with the reported angle
  matching a hand calculation from the cone's actual dimensions exactly).
  Also run against the real `gear_reduction` example's `pinion.stl` and
  `spur.stl`: `spur.stl` passes clean; `pinion.stl` reports a borderline
  0.796mm minimum wall (just under the 0.8mm default threshold) at the
  small pinion's tooth root -- plausible, not obviously wrong, for an
  11-tooth module-1 gear, a known-marginal case for FDM in practice; not
  treated as a defect in the example, since this is a new, non-mandatory
  check and the example was never scoped against it.
- **Already promoted to a rule?** Yes -- fixed directly in all listed
  files.

### 2026-08-22 -- named a recurring gap shape found across the day's fixes: passive correctness without an active connecting step (rules_enforcement.md §5)
- **Where:** `scad-modeler/references/rules_enforcement.md` (new §5),
  `SKILL.md` (reference-files entry cross-linked).
- **Motivation:** asked to analyze the 2026-08-21/22 INCIDENTS.md entries
  for patterns (not a checker finding -- a cross-reading of several
  already-logged entries side by side). Three separately-built fixes that
  day turned out to share one shape: `doctor.py`'s `find_calibration()` +
  `confidence-tiers.md` were both already correct, but nothing connected
  "no calibration profile" to "propose printing a coupon" until the user
  reported having to ask every time; `INCIDENTS.md`'s own header correctly
  states its purpose but nothing captured the raw data live, losing 24 of
  26 exact values in a real reconstruction attempt; `check_dependencies.py`
  correctly named affected FILES but not affected DECLARED requirements
  until the P1 fix. Not a bug in any one of these -- a pattern only
  visible across all three at once.
- **Fix:** not a script (the underlying gap in each instance was already
  fixed separately, see the R-14/telemetry/P1 entries). `rules_enforcement.md`
  §5 names the pattern explicitly as a design question to apply going
  forward: when adding a check or reference fact, does it only
  REPORT/GATE, or does it also PROPOSE the specific next action its own
  finding implies? Cross-linked from `SKILL.md`'s reference-files list so
  it surfaces when writing the next check, not just during a future
  audit.
- **Already promoted to a rule?** Yes, as prose guidance -- not a
  `rules_manifest.yaml` entry, since "did the model propose the action"
  is about a specific response's content, not a file's state, so no
  script can gate it the way R-01..R-16 do.

### 2026-08-22 -- added a parameter context manifest (use_param() + check_param_context.py, Phase-2 Pattern 3)
- **Where:** `scad-modeler/scripts/check_param_context.py` (new),
  `scad-modeler/scripts/validate_scad.sh`, `scad-modeler/rules_manifest.yaml`
  (R-16), `SKILL.md` §2.
- **Motivation:** third and final pattern from the 2026-08-19 pattern-
  analysis pass, implemented after the user asked for a "better skill"
  built from the accumulated cases. Real precedent: a single `axle_d`
  value fed both a diff-side output stub (photo-measured, fine at 6mm)
  and a wheel-hub bearing bore (fixed 5mm-ID MR105 bearing, incompatible
  with 6mm) -- only the diff-side context was ever actually verified
  against; nothing checked the wheel-hub context, and the incompatibility
  went unnoticed until someone traced both ends of the half-shaft by hand
  (INCIDENTS.md, 2026-08-18). This is the most novel of the three
  mechanisms (closest analogy: PostgreSQL refusing to drop an object with
  unresolved dependents), built last per the pattern write-up's own
  suggested order.
- **Fix:** `use_param(name, context, constraint)` is a no-op OpenSCAD
  module (defined once in params.scad, confirmed to compile and render
  cleanly as a statement with no children) that marks, at the point a
  shared parameter is consumed for a hardware-fit purpose, which context
  and which constraint it's satisfying. `check_param_context.py` scans
  every `.scad` file in the project for these declarations; for any
  parameter name declared in ≥2 distinct (file, context) pairs -- the
  only case with cross-context risk -- it requires the SAME FILE to also
  contain an `assert()` textually referencing that parameter name. A
  context with no matching assert() in its own file fails, naming exactly
  which context was never verified. Opt-in and a no-op when a project
  never declares `use_param()` at all. Wired into `validate_scad.sh`
  (auto, unconditional -- the script itself handles the nothing-to-check
  case) and `rules_manifest.yaml` as R-16.
- **Tested:** a direct synthetic reproduction of the axle_d incident
  shape (diff_stub.scad has its own assert, wheel_hub.scad declares the
  context but has none) correctly fails, naming the exact missing
  context; adding the missing assert to wheel_hub.scad correctly flips it
  to PASS; a single-context use_param() (no cross-context risk) correctly
  passes without requiring anything; a project with no use_param() calls
  at all (the real gear_reduction example) correctly passes as opt-in-skip.
  `use_param()` itself was rendered through real OpenSCAD twice --
  once inside a failing assert (confirmed the no-op module itself caused
  no parse/render error, only the assert on the following line failed, as
  intended) and once end-to-end with a passing assert (clean render,
  correct geometry, non-empty STL).
- **Already promoted to a rule?** Yes -- fixed directly in all listed
  files. All three 2026-08-19 Phase-2 patterns are now implemented as of
  this same day.

### 2026-08-22 -- check_collisions.py gained clash classification and auto-suggested joints.json stubs (Phase-2 Pattern 2)
- **Where:** `scad-modeler/scripts/check_collisions.py`, `SKILL.md`.
- **Motivation:** second of the three patterns from the 2026-08-19
  pattern-analysis pass, implemented after the user asked for a "better
  skill" built from the accumulated cases. Real precedent this targets:
  `gearbox_case_bottom`/`top`'s clamshell split-line touch (INCIDENTS.md,
  2026-08-18) was correctly reasoned about as benign during the original
  design session, but was never formalized into `joints.json` -- so the
  validation pipeline as documented couldn't actually be run to a clean
  pass, and the "fix" would have meant a human hand-writing a declaration
  from scratch after already having done the reasoning once.
- **Fix:** for an UNDECLARED pair, a gap or penetration depth at or below
  `--touch-tolerance` (default 0.05mm) is now classified CANDIDATE
  INTENTIONAL TOUCH -- still a FAIL (nothing auto-authorized), but printed
  with a ready-to-paste `joints.json` contact stub (pair names,
  `joint_type: "touching"`, a deliberately obvious placeholder derivation
  requiring a human to replace it) instead of a bare "UNINTENDED
  INTERFERENCE". A gap just past that, up to `--near-miss-tolerance`
  (default 0.2mm), is reported as a non-fatal NEAR MISS note instead --
  the pattern write-up's own reasoning that this band is more often a
  real design sensitivity than a benign touch, so it is surfaced but NOT
  auto-suggested as intentional. Both checks now run unconditionally for
  every undeclared, non-overlapping pair, not only when `--min-clearance`
  is passed (previously the whole distance-query path was skipped
  without it). NOT implemented: the pattern write-up's own "stability
  check" (re-render with a jittered parameter to see if a touch/overlap
  verdict flips near a boundary) -- that needs an actual re-render per
  candidate pair, explicitly out of scope for a static post-hoc
  classifier built from already-rendered STLs.
- **Tested:** four synthetic two-box fixtures -- genuinely touching
  (0.000mm gap, undeclared) correctly classified CANDIDATE INTENTIONAL
  TOUCH with a valid stub printed; a real 5mm overlap correctly still
  reports UNINTENDED INTERFERENCE unchanged; a 0.15mm gap correctly
  reported as a non-fatal NEAR MISS note with exit 0; parts 5mm apart
  correctly produce a clean OK with no notes. A fifth case (0.15mm gap
  with `--min-clearance 0.3` passed) correctly prioritizes INSUFFICIENT
  CLEARANCE over the near-miss note, confirming the two mechanisms don't
  conflict. Full `validate_scad.sh --all` re-run against the real
  `gear_reduction` example (a genuine declared gear-mesh contact) stays a
  clean pass, confirming the new unconditional distance query didn't
  regress the existing declared-contact path.
- **Already promoted to a rule?** Yes -- fixed directly in
  `check_collisions.py`, documented in `SKILL.md` §7.

### 2026-08-21 -- check_dependencies.py gained requirement-influence cross-referencing (P1 decision-tree optimization)
- **Where:** `scad-modeler/scripts/check_dependencies.py`,
  `scad-modeler/references/change_propagation.md`, `SKILL.md`.
- **Motivation:** follow-up P1 item from the same 2026-08-21 Perplexity
  research pass -- the same-day P0 fixes (analytic pre-flight, provenance,
  contact witness) close the *validation* side of the 12-round defect
  class; this closes the *change-propagation* side: `check_dependencies.py`
  already told an agent which part FILES a parameter change reaches, but
  not which DECLARED requirements (a joints.json contact, a motion driver,
  a bores.json bore) on those parts might now be invalid -- exactly the gap
  that let a real `worm_wheel_teeth` parameter change (20->40 teeth) go
  unnoticed across multiple validation rounds before a declared contact
  quietly stopped meaning what it used to.
- **Fix:** `--change VAR` now accepts `--joints joints.json` and `--bores
  bores.json` (both default to those filenames in the current directory,
  silently skipped if absent) and cross-references the affected part
  basenames against every declared contact pair, motion driver, and bore
  declaration, printing which ones are affected using the same
  case-insensitive substring matching convention `check_collisions.py`/
  `check_bore_reachability.py` already use. Explicitly advisory, not an
  automated skip mechanism -- the existing fallback-to-full-`--all` policy
  is unchanged and remains the safety net. Tested: a synthetic reproduction
  of the real incident shape (a teeth-count parameter feeding a gear radius
  that's also named in a declared contact, a motion driver, and a bore)
  correctly flags all three; an unrelated parameter change correctly flags
  none; a project with neither joints.json nor bores.json degrades cleanly
  with no error; `--all` JSON-dump mode is unaffected.
- **Already promoted to a rule?** Yes -- fixed directly in the script;
  `change_propagation.md` also corrected to distinguish what's actually
  implemented (the tokenizer DAG + this cross-reference) from the file's
  own aspirational full design (a JSON schema and boxed-tree output format
  that were never built).

### 2026-08-21 -- added an analytic pre-flight gate, a provenance requirement, and a spatial "contact witness" to close the 12-round investigation class of defect
- **Where:** `scad-modeler/scripts/validate_scad.sh`, `scad-modeler/scripts/check_collisions.py`,
  `scad-modeler/rules_manifest.yaml`, `scad-modeler/templates/joints.json`,
  `scad-modeler/examples/gear_reduction/joints.json`.
- **Motivation:** a Perplexity deep-research pass (grounded in NASA/INCOSE
  V&V taxonomy, sequential-fault-diagnosis literature, and FreeCAD's
  dependency-DAG recompute model) was asked to optimize this skill's
  decision tree for fewer, cheaper validation rounds without sacrificing
  correctness. Its highest-priority finding: the single most expensive
  defect class found across every real project this skill has been used on
  (a 12-round investigation into a hidden collision, ending with a real
  `esp32_rc_modelis` incident where `big_gear`/`output_gear` radii summed to
  more than their actual center distance) was **purely algebraic** --
  discoverable from confirmed `params.scad` values alone, with zero need to
  ever render geometry.
- **Fix, three parts (all P0, "low cost / very high benefit" per the
  research's own priority ranking):**
  1. **Analytic pre-flight gate** in `validate_scad.sh`, running FIRST,
     before any part is rendered: every `assert()` in `params.scad` is
     evaluated via a trivial placeholder-solid wrapper (needed because a
     bare definitions-only file trips OpenSCAD's "empty top level object"
     hard-warning under `--hardwarnings` regardless of whether its asserts
     pass -- confirmed directly, and also confirmed that `assert()` failure
     alone does NOT change OpenSCAD's process exit code without
     `--hardwarnings` converting the resulting empty-object warning into a
     hard failure, a previously-unverified assumption this whole skill had
     relied on). Tested: a failing `r1+r2+clearance > center_distance`
     assert correctly fails with the real error message surfaced; a
     passing one correctly passes; no `params.scad` correctly skips; the
     existing `gear_reduction` example (real asserts, all passing) is
     unaffected.
  2. **Provenance requirement** in `check_collisions.py`: any contact
     declaring `expected_interference_mm` must also declare a non-empty
     `"derivation"` string. Doesn't machine-verify the derivation is
     arithmetically correct (deferred, larger "influence graph" work) --
     makes a hand-typed guess with no stated origin impossible to declare
     silently. Confirmed as a real gap in this skill's OWN example project:
     the `pinion`/`spur` contact's range was initially copied from an
     unrelated press-fit fixture, not derived, and only corrected after
     measuring the real depth post-hoc.
  3. **Contact witness (`expected_bounds`)** in `check_collisions.py`: an
     assembly-space bounding box every detected contact region must fall
     inside, checked independently of `multi_region_ok` (which only bounds
     the *count* of regions, not *where* they are -- a real remaining gap
     the research specifically called out). Tested against a direct
     reproduction of the real defect shape (two bars overlapping at both
     a declared-legitimate edge and an undeclared, unrelated edge): the
     unauthorized region is correctly caught and reported with its exact
     location, even with `multi_region_ok: true` set; declaring bounds
     that cover both zones correctly passes.
  Applying (2) and (3) to `templates/joints.json` and the real
  `gear_reduction` example required actually re-measuring the real contact
  region bounds rather than guessing them -- a first guessed
  `expected_bounds` was itself wrong and correctly caught by the new check,
  confirming the mechanism works against a real, not synthetic, case.
- **Already promoted to a rule?** Yes -- fixed directly in all listed
  files; `rules_manifest.yaml` R-13 added for the pre-flight gate.

### 2026-08-21 -- edit classification (C1-C5) and forbidden_regions added (P2 decision-tree optimization)
- **Where:** `scad-modeler/scripts/check_dependencies.py`,
  `scad-modeler/scripts/check_collisions.py`, `scad-modeler/templates/joints.json`,
  `SKILL.md`.
- **Motivation:** third-tier (P2) follow-up from the same 2026-08-21
  Perplexity research pass. P0 closed the validation side and P1 the
  change-propagation side of the 12-round defect class; P2 targets two
  smaller, still-justified gaps the research flagged as "moderate benefit,
  low-to-moderate cost": (a) `check_dependencies.py --change` told an agent
  WHICH declared requirements a change reaches (P1) but not HOW MUCH
  re-validation that minimally requires -- an agent still had to guess
  whether a part-local change needs the full `validate_scad.sh --all`; (b)
  `expected_bounds` (P0) is a positive allow-list (the contact must stay
  INSIDE one box) with no way to instead name a specific nearby feature
  that must NEVER be touched when the legitimate contact zone itself is
  awkward to bound tightly.
- **Fix, two parts:**
  1. **Edit classification (C1-C5)** in `check_dependencies.py`: a
     `classify_edit()` function maps the signals `--change` already computes
     (affected part basenames, affected declared contacts/motion/bores from
     the P1 cross-reference) to the cheapest class of re-validation actually
     needed -- C1 (nothing tracked reached) through C5 (reaches a declared
     motion driver -> full `validate_scad.sh --all`, since a motion/ratio
     change invalidates both the static collision precondition and the
     sweep). Advisory only, same fallback-to-full-`--all` discipline as
     every other advisory mechanism this skill has. Tested against all 5
     classes via synthetic fixtures, including one case where a variable fed
     a part that was ALSO a declared-contact member -- correctly returned
     C4 (contact) not C3 (bore), confirming the priority ordering
     (C5>C4>C3>C2>C1) matches the actual wiring rather than naive intent.
  2. **`forbidden_regions`** in `check_collisions.py`: the negative
     complement of `expected_bounds` -- a list of assembly-space boxes a
     declared contact must never touch, checked via AABB overlap against
     every detected contact region, failing as `CONTACT IN FORBIDDEN
     REGION` before the `expected_bounds` check runs. Tested with a
     synthetic two-bar fixture (one legitimate edge-clip contact, one
     illegitimate edge-clip contact inside a declared forbidden box): the
     illegitimate region is correctly caught and reported with its exact
     overlap location and volume; a second run with the illegitimate
     geometry removed (only the legitimate contact present) correctly
     passes with no false positive.
- **Already promoted to a rule?** Yes -- fixed directly in all listed files.
  P3-tier items from the same research pass (Bayesian/POMDP adaptive
  sequencing, a general symbolic geometry solver) were deliberately NOT
  built -- the research itself flagged them "uncertain until data exists" /
  "unnecessary initially," requiring 20-50 accumulated real validation
  rounds of telemetry before they'd be justified, which doesn't exist yet.

### 2026-08-21 -- added a validation-run log (scripts/validation_log.py) after a real reconstruction attempt lost almost all exit codes/commands/timestamps
- **Where:** `scad-modeler/scripts/validation_log.py` (new),
  `scad-modeler/scripts/validate_scad.sh`, `check_collisions.py`,
  `motion_sweep.py`, `check_bore_reachability.py`,
  `check_subfeature_overlap.py`, `check_dependencies.py`, `check_rules.py`,
  `SKILL.md`, and (outside this repo) `~/.zshrc`
  (`SCAD_MODELER_LOG_DIR`).
- **Motivation:** asked to reconstruct the steering_reduction_gearbox
  project's ~26-round validation history from `calculations.md` prose and
  this file alone (no live logging existed), the result had 24 of 26
  entries with an unknown exit code, unknown exact command, and unknown
  timestamp -- only the qualitative outcome (OK/FAIL + a described defect)
  survived. This is a real, demonstrated gap: `INCIDENTS.md`'s own stated
  purpose is "raw data for a later pattern-review pass," but the raw data
  was never actually being captured, only written up from memory
  afterward, lossily.
- **Fix:** `validation_log.py` is a small shared module (`log_run()` +
  CLI) that appends one JSON line -- timestamp, project dir, checker name,
  exit code, full command, short summary -- to
  `$SCAD_MODELER_LOG_DIR/validation_log.jsonl` (defaults to
  `~/.claude/scad_modeler/validation_log/` if that env var is unset;
  deliberately not a hardcoded personal path, since this script ships in a
  public repo). Wired into every `validate_scad.sh` `CHECK_RESULT` line
  and into the standalone entry point of every checker SKILL.md documents
  as commonly run directly (not just through `validate_scad.sh`).
  Best-effort: any logging failure is silently swallowed and never affects
  a check's own exit code. On this machine, `SCAD_MODELER_LOG_DIR` is set
  in `~/.zshrc` to `04_Kita/SCAD_Validacijos_Zurnalas/` (user's explicit
  request -- accumulate outside any one project folder, in its own
  folder). Tested end-to-end against the real `gear_reduction` example: a
  full `validate_scad.sh --all` run produced 9 correctly-populated log
  lines (including the aggregate `validate_scad_all` rollup); a standalone
  `check_collisions.py` call against deliberately unpositioned STLs
  correctly logged `exit_code: 3` / `FAIL`; a standalone
  `check_dependencies.py --change` call correctly logged `exit_code: 0`.
- **Explicit scope note:** this does not make any tool "learn" by itself
  -- there is no training loop or automated process reading this file.
  It is raw material for a human/agent to review later, same purpose as
  `INCIDENTS.md`, just captured live instead of reconstructed afterward.
- **Already promoted to a rule?** Yes -- fixed directly in all listed
  files.

### 2026-08-21 -- added calibration_coupon() and a proactive-proposal rule (R-14) after the model only offered a fit-test print when explicitly asked, every time
- **Where:** `openscad-cad/references/patterns.scad` (Pattern 5, new
  `calibration_coupon()` module), `openscad-cad/SKILL.md` §4.5,
  `scad-modeler/rules_manifest.yaml` (R-14), `scad-modeler/SKILL.md` §0.6.
- **Symptom (user-reported, not a checker finding):** in a separate
  real-project conversation (`20260821_serverrack`), the user had to
  personally ask, each time, for a part to be printed and checked for
  hole fit, and to be offered an incremental-diameter test rather than a
  single guessed dimension. `references/confidence-tiers.md` already
  names a calibration profile as a Tier 3 hard gate and
  `references/tolerances.md` already says "print a coupon ... and
  measure it" -- but nothing made the model actually PROPOSE that step
  on its own before finalizing a fit-critical dimension; the existing
  behavior was to silently note "uncalibrated, capped at Tier 2" rather
  than surface the concrete next action.
- **Root cause:** the gap was between two already-correct pieces --
  `doctor.py`'s `find_calibration()` correctly detects a missing
  calibration profile, and `confidence-tiers.md` correctly says what
  that caps -- but no rule connected "profile missing" to "propose
  printing one," and no reusable coupon-generator existed, so proposing
  it meant hand-deriving hole-comb geometry from scratch each time (or,
  in practice, not proposing it at all until asked).
- **Fix:** `calibration_coupon(target_d, step, n_below, n_above, ...)` in
  `patterns.scad` generates a single labelled plate with through-holes at
  incremental diameters straddling a target size (using `true_hole_d()`,
  Pattern 0, so the coupon is built the same way a real part's holes
  are). `openscad-cad/SKILL.md` §4.5 now instructs proactively proposing
  a coupon print before finalizing a load-bearing/precision-sensitive fit
  with no calibration profile found -- not for every hole, only where
  being off actually matters. `scad-modeler/rules_manifest.yaml` R-14
  (kind: manual, since no script can verify a physical print happened)
  makes this an explicit self-assessment item in every §8 report for a
  project declaring `bores.json`/`joints.json`, cross-referenced from
  `scad-modeler/SKILL.md` §0.6's existing purchased-part-fit bullet.
  Tested: `calibration_coupon(target_d=5.0, step=0.1, n_below=2,
  n_above=3)` rendered clean (manifold, non-empty, `--hardwarnings`
  clean) and visually confirmed via PNG render -- six holes, correctly
  incrementing 4.8/4.9/5.0/5.1/5.2/5.3mm, each legibly labelled;
  `check_rules.py` against the real `gear_reduction` example correctly
  lists R-14 among the manual rules requiring self-assessment.
- **Already promoted to a rule?** Yes -- fixed directly in all listed
  files.

### 2026-08-19 -- a BOSL2 gear positioned through layout.scad's at() failed under --hardwarnings; a plain guessed interference range was also wrong for real gear teeth
- **Where:** `scad-modeler/examples/gear_reduction/` (new example project,
  built for publication readiness -- see the "Publication prep" commits).
- **Symptom (1):** `validate_scad.sh --all` failed rendering `assembly.scad`
  with `WARNING: Ignoring unknown variable "$transform"` (from
  `BOSL2/transforms.scad`) and, after that was fixed, a second warning
  `"Ignoring unknown variable $parent_gear_pa"` (from `BOSL2/gears.scad`)
  -- both promoted to hard failures by `--hardwarnings`, which this
  skill's own `validate_scad.sh` deliberately uses.
- **Root cause:** two distinct BOSL2 scoping gotchas, both real and neither
  previously hit by this skill's own testing because no earlier test
  fixture combined a BOSL2 module (`spur_gear()`) with the skill's own
  `at()` positioning pattern.
  1. BOSL2 redefines the built-in `translate()`/`rotate()` to also track a
     `$transform` special variable, used internally by `spur_gear()`'s
     attachable machinery. `layout.scad`'s `at()` module used the PLAIN
     built-in `translate()`/`rotate()` because `layout.scad` itself never
     included BOSL2 -- a module's `translate()`/`rotate()` binding is
     fixed at the scope where the module is *defined*, not where it's
     *called* from, so `parts/pinion.scad` including BOSL2 did not help.
  2. `BOSL2/gears.scad` declares `$parent_gear_pa` (and four sibling
     `$parent_gear_*` variables) as `undef` at its own top level, which is
     what normally makes reading them elsewhere not trigger "unknown
     variable". `BOSL2/std.scad` does NOT itself include `gears.scad`
     (confirmed by reading it directly). `parts/pinion.scad`'s own
     `include <BOSL2/gears.scad>` did not propagate to `assembly.scad`
     either, because `assembly.scad` only `use`s the part files, and
     `use` never propagates a file's top-level variable assignments (the
     same `use`-vs-`include` distinction already documented in
     `references/setup-notes.md`, hit again in a new combination).
- **Symptom (2), a real geometry finding, not a bug:** once (1) was fixed,
  `check_collisions.py` correctly measured the declared `pinion`/`spur`
  gear-mesh contact at 1.383mm penetration depth, split into 2-3 disjoint
  regions -- both far outside a guessed `expected_interference_mm: [0.0,
  0.5]` range copied from earlier press-fit test fixtures, and enough
  disjoint regions to fail the new multi-region check without an
  exemption. Root cause: real involute gear teeth interpenetrate more
  deeply than a bearing/shaft press fit (module-1-scale addendum, not
  press-fit-scale), and a standard involute pair's contact ratio (>1 by
  design) means more than one tooth pair is legitimately in contact at
  once at any static pose -- this is normal, correct gear behavior, not a
  design defect.
- **Fix:** (1) `layout.scad` now includes `BOSL2/std.scad` then
  `BOSL2/gears.scad` itself, even though it never calls a gear function
  directly -- fixes both warnings, since a module's `translate`/`rotate`
  and special-variable visibility come from its own definition scope. (2)
  `joints.json`'s declared range widened to `[0.5, 2.0]mm` and
  `"multi_region_ok": true` added, both set from the actual measured
  values for this specific gear pair (documented inline in the file's
  `_comment`), not guessed. Full chain re-run after both fixes: `exit=0`,
  `check_rules.py` reports every applicable automated rule PASS.
- **Already promoted to a rule?** Yes -- fixed directly in the example;
  documented in the example's own README and inline comments so a future
  BOSL2-gear-plus-`at()` combination doesn't rediscover this from scratch.

### 2026-08-19 -- check_collisions.py's declared-contact verdict has no spatial awareness: a legitimate contact zone and a separate, illegitimate one can hide behind the same MAX-depth number
- **Where:** `scad-modeler/scripts/check_collisions.py` (the 2026-08-19
  penetration-depth upgrade, see the earlier entry below) --
  `esp32_rc_modelis/mechanical/steering_reduction_gearbox/`
  (`jackshaft.stl` [worm + big_gear on one printed part] vs
  `output_gear.stl` [worm wheel]), found live during a parallel Claude Code
  session's re-validation of that project. Logged first without fixing
  (explicit user instruction, since a different session was expected to
  implement it); fixed directly in this session shortly after, once the
  user asked for it here instead.
- **Symptom:** the render looked visibly wrong to the user (parts appearing
  fused where they shouldn't be) despite the other session's own
  `check_collisions.py` initially reporting the declared `jackshaft`/
  `output_gear` "gear_mesh" contact as fine. Pushed to verify more deeply
  (not accept "that's just normal tooth backlash"), the other session used
  `trimesh.intersection()` + `.split(only_watertight=False)` on the raw
  boolean intersection between the two positioned STLs and found the total
  157.97mm³ overlap is NOT one contact zone -- it splits into 7 disjoint
  connected components. One of them (109.5mm³, the largest) has bounds
  X=[23.0, 31.0], entirely outside the worm thread's own physical extent
  (the worm section of `jackshaft` starts at X=34; X=23-31 is where
  `big_gear`/the shaft-transition region of the same printed part sits).
  That investigation was still in progress (not yet resolved to a definite
  root geometric cause) when relayed to this session.
- **Root cause:** the current declared-contact check takes the MAX
  penetration depth across ALL FCL contact points for a pair and compares
### 2026-08-21 -- P1S bed limit, 250mm too close to 256mm (server_rack, part1)
- **Where:** module width decision (pre-D).
- **Symptom:** 250mm width leaves ~3mm for skirt/brim on P1S bed — risky.
- **Root cause:** designing to nominal bed size without slicer margins.
- **Fix:** user chose diagonal print; later refined to 250.5mm for EIA-310.
- **Already promoted to a rule?** not yet.

### 2026-08-21 -- hidden screw channel crossed EIA holes (server_rack, part1)
- **Where:** vertical screw channel vs horizontal EIA holes.
- **Symptom:** channel geometry intersected hole bores.
- **Root cause:** two systems routed without collision check.
- **Fix:** channel shortened to joint zones only.
- **Already promoted to a rule?** not yet.

### 2026-08-21 -- shelf_plate stayed square after module went rectangular, D8 (server_rack, part1)
- **Where:** shelf_plate after D8 rectangle change.
- **Symptom:** auto-checks missed it; found by manual STL re-measure.
- **Root cause:** no parametric link between module shape and shelf shape; checks verified presence, not dimensions.
- **Fix:** fixed, logged in INCIDENTS.md (v1 project).
- **Already promoted to a rule?** not yet — candidate: dimension-cross-check after shape change.

### 2026-08-21 -- EIA slot extension merged with magnet pocket, D11 (server_rack, part1)
- **Where:** D11 slot lengthening vs lower magnet pocket.
- **Symptom:** slot void merged with pocket void.
- **Root cause:** adjacent voids grown without clearance check.
- **Fix:** inset bump correction, all STLs regenerated.
- **Already promoted to a rule?** not yet.

### 2026-08-21 -- flush recess detached spigots from posts (server_rack, part1)
- **Where:** flush recess geometry.
- **Symptom:** spigots disconnected (separate shells).
- **Root cause:** recess cut removed spigot base material.
- **Fix:** recess geometry fixed, re-validated.
- **Already promoted to a rule?** not yet.

### 2026-08-22 -- EIA holes bored through wrong axis, D12 (server_rack, part2)
- **Where:** EIA holes through post width (X); screwdriver blocked by side magnetic panel.
- **Symptom:** user measured 211mm between holes, interior 7.87in instead of 10in; assistant defended geometry for rounds before conceding.
- **Root cause:** axes swapped (EIA on Y needed for open front); overconfidence in STL scans vs user caliper.
- **Fix:** EIA to Y, ladder slots inward; full process analysis to INCIDENTS.md + memory rule "don't argue with user".
- **Already promoted to a rule?** Yes — user-measurement-wins rule.

### 2026-08-22 -- EIA wall only 0.29mm, unprintable, D13 (server_rack, part2)
- **Where:** post wall at EIA hole.
- **Symptom:** 0.29mm wall — fails in print.
- **Root cause:** post too thin (14mm) for 7.1 hole + magnets.
- **Fix:** post widened X 14→18mm (wall 2.29mm); Y kept 14 for P1S limit.
- **Already promoted to a rule?** not yet — candidate: min-wall check at holes.

### 2026-08-22 -- socket bore 3.4mm instead of 8.38mm, D14 (server_rack, part2)
- **Where:** lower socket (M3 channel) vs spigot.
- **Symptom:** spigot doesn't fit, modules don't join.
- **Root cause:** socket cut as screw channel, not joint bore.
- **Fix:** cut_socket perimeter_ring, 8.383mm void; joint_test coupons for physical print.
- **Already promoted to a rule?** not yet.

### 2026-08-22 -- flush recess on every module made 3.15mm gaps, D15 (server_rack, part2)
- **Where:** stacked frames with recess each.
- **Symptom:** 3.15mm gap between stacked frames.
- **Root cause:** recess applied per-module instead of topmost-only.
- **Fix:** split intermediate (flat) / topmost (recess) STL variants.
- **Already promoted to a rule?** not yet.

### 2026-08-22 -- intermediate ring closed on 4 sides, 28mm band at seam, D16 (server_rack, part2)
- **Where:** intermediate module ring.
- **Symptom:** 28mm solid band at seam.
- **Root cause:** ring not opened front/back for stacking.
- **Fix:** front/back cuts in intermediate rings; single 14.004mm ring at seam, one body confirmed.
- **Already promoted to a rule?** not yet.

### 2026-08-23 -- 1U 44.5 vs EIA-310 44.45, error propagated, D17 (server_rack, part2)
- **Where:** unit_1U constant.
- **Symptom:** 0.05mm per U error across every module.
- **Root cause:** rounded constant instead of exact 44.45.
- **Fix:** changed to 44.45, all STLs rebuilt, tower height recomputed.
- **Already promoted to a rule?** not yet — candidate: exact-standards-no-rounding.

### 2026-08-23 -- 2U meant outer height, interior only 1.37U, D18 (server_rack, part2)
- **Where:** 2U module convention.
- **Symptom:** interior 60.9mm with one hole group instead of two.
- **Root cause:** U counted with rings instead of interior clear span.
- **Fix:** module_h = interior + rings; 2U interior exactly 88.9mm with 2 hole groups; +84mm tower.
- **Already promoted to a rule?** not yet.

### 2026-08-23 -- NAS bay interior 194 to 170, bottom ring 14 to 5, D19-D20 (server_rack, part2)
- **Where:** NAS bay dims.
- **Symptom:** oversize bay, heavy bottom ring.
- **Root cause:** initial guess without NAS measurements.
- **Fix:** interior 170, ring 5; assembly_full rebuilt (~601mm, 53 parts).
- **Already promoted to a rule?** not yet.

### 2026-08-26 -- dovetail tail/socket offset 6mm, 5 separate bodies, D25/D27 class (server_rack, part3)
- **Where:** post.scad / node.scad vertical dovetail (+h/2 after rotate vs -h/2).
- **Symptom:** tail and socket missed by ~6mm; post_v2_final 5 disconnected bodies.
- **Root cause:** asymmetric y=0..h trapezoid + rotate sign bug class (the exact class peg later eliminated).
- **Fix:** one-line offset sign fix, re-rendered and verified.
- **Already promoted to a rule?** Yes — peg centering eliminated the class (D37/D48 rationale).

### 2026-08-26 -- magnet pocket coincident faces, negative-volume fragments (server_rack, part3)
- **Where:** post.scad pockets, 0.6 wall at body edge.
- **Symptom:** 4 degenerate negative-volume fragments.
- **Root cause:** pocket wall too thin at filleted edge.
- **Fix:** post.scad rewritten with through-tunnel + plugs.
- **Already promoted to a rule?** not yet.

### 2026-08-26 -- top dovetail socket covered top EIA hole (server_rack, part3)
- **Where:** 8mm socket vs top EIA-310 hole.
- **Symptom:** socket void covered the hole.
- **Root cause:** socket too deep at post top.
- **Fix:** shortened to 2.8mm per user choice, ray-cast verified.
- **Already promoted to a rule?** not yet.

### 2026-08-26 -- NAS as one welded body, top plate bridge in air (server_rack, part3)
- **Where:** NAS floor+posts+deck welded.
- **Symptom:** 245mm unsupported bridge on 4 thin posts — unprintable without massive support.
- **Root cause:** welded instead of jointed; inconsistent with every other joint.
- **Fix:** split nas_floor + nas_deck, deck rests on posts.
- **Already promoted to a rule?** not yet — candidate: no-welded-tiers.

### 2026-08-26 -- NAS posts welded with glue-in magnets, wrong system (server_rack, part3)
- **Where:** NAS posts.
- **Symptom:** welded + glue-in pockets vs dovetail + pause-print convention everywhere else.
- **Root cause:** built separately without following project conventions.
- **Fix:** nas_post.scad with tails both ends + roofed embedded pockets, printed on side (D23).
- **Already promoted to a rule?** not yet.

### 2026-08-26 -- nas_side_panel pocket open to inner face, D33 (server_rack, part3)
- **Where:** nas_side_panel pocket at inner face.
- **Symptom:** visible open hole on post-touching face.
- **Root cause:** pocket centered at depth/2 from own inner face instead of mid-thickness.
- **Fix:** centered mid-thickness (0.7 walls both sides), ray-cast verified.
- **Already promoted to a rule?** not yet — candidate: pocket-centering-rule (later applied project-wide D48).

### 2026-08-30 -- dovetail bowtie, impossible 50deg angle (server_rack, part3)
- **Where:** dovetail.scad trapezoid (h*tan50=7.15 > w/2=5).
- **Symptom:** self-intersecting bowtie, non-watertight mesh, 10 vertices, pinch at y~4.2.
- **Root cause:** trapezoid formula geometrically impossible for all used w/h ratios; confirmed by 2 independent Muse audits.
- **Fix:** wedge-lock prototype as replacement; later full dovetail removal (D37).
- **Already promoted to a rule?** Yes — peg replacement (D37).

### 2026-09-04 -- beam default len 211 vs computed 216.5/191 (server_rack, part4)
- **Where:** beam.scad default.
- **Symptom:** beam shaft rammed ~10mm into node body.
- **Root cause:** default disconnected from assembly math (center-to-center vs face-to-face).
- **Fix:** removed default (mandatory arg now).
- **Already promoted to a rule?** not yet — candidate: no-default-for-computed-dims.

### 2026-09-04 -- top_panel magnet walls inverted 0.6/0.8, D21 (server_rack, part4)
- **Where:** top_panel pockets.
- **Symptom:** visible side 0.6, top 0.8 instead of reverse.
- **Root cause:** pocket depth measured from wrong face.
- **Fix:** documented; unfixed this part (later fixed in v54 wave).
- **Already promoted to a rule?** not yet.

### 2026-09-04 -- Task 4 ternary-offset countersink outside solid (server_rack, part4)
- **Where:** enclosure plan Task 4 literal code.
- **Symptom:** wide mouth outside solid body.
- **Root cause:** plan code assumed solid where chamfer removed it.
- **Fix:** used plan's own mirror() fallback, proven by render.
- **Already promoted to a rule?** not yet — candidate: plan-fallback-first.

### 2026-09-04 -- glue-in pocket only -Y, +Y panel had nothing (server_rack, part4)
- **Where:** post.scad Y pockets.
- **Symptom:** back panel magnets with no counterpart.
- **Root cause:** plan gap (one side only); one corner post serves both front AND back.
- **Fix:** reviewer caught; double ySign/mirror pockets, 8 probes confirmed.
- **Already promoted to a rule?** not yet.

### 2026-09-04 -- assembly not fully watertight, 5 of 53 shells at corners (server_rack, part4)
- **Where:** full assembly corners.
- **Symptom:** 5 shells open at corners.
- **Root cause:** harmless CSG-kernel artifact (D26 type), proven by control render + point-containment; accepted.
- **Fix:** accepted as artifact, documented.
- **Already promoted to a rule?** not yet.

### 2026-09-08 -- used openscad-cad alone for 14-part assembly, ignored dual-skill rule (cnc_control_enclosure v2)
- **Where:** session 2026-09-08 (~20:00), own memory rule `3d-abu-skill-kartu.md` + cross-refs in both SKILL.md (written previous evening, same project).
- **Symptom:** Loaded only openscad-cad for a 14-part enclosure; rule written 24h earlier says 2+ parts = both skills. No planning/calculation phase, no validation gates -- straight to write-render-fix loop.
- **Root cause:** Rule written but not applied -- same D44 pattern (documented, not applied), this time self-authored. Session started from prior context (params already existed) so skill-loading step was skipped entirely.
- **Fix:** No geometry harm (parts verified by render + STL measure). Process fix: 3D session start = load both skills + read INCIDENTS, no exception for continuations.
- **Already promoted to a rule?** Rule already exists (3d-abu-skill-kartu.md); this entry is evidence it needs a start-of-session trigger, not just a card on disk.

### 2026-09-08 -- never read canonical INCIDENTS.md before modelling (cnc_control_enclosure v2)
- **Where:** same session; scad-modeler \u00a70 requires INCIDENTS read before geometry; canonical log updated previous evening 20:15 (D39-D51).
- **Symptom:** Modelled 14 parts without opening the log. Missed directly relevant entries: D49 (stale STL -- same export step), D51 (never copy coords -- same hole-placement step), D40 (count-check marks).
- **Root cause:** Read the log previous evening only when told to, not as session-start habit. Continuation bias: felt "already oriented" from prior context.
- **Fix:** Same process fix as above -- INCIDENTS read is step 0 of every 3D session, continuations included. No geometry harm found retroactively.
- **Already promoted to a rule?** scad-modeler \u00a70 already requires it; this entry is evidence the requirement needs enforcing at session start.

### 2026-09-08 -- wrote 11 entries to wrong INCIDENTS.md, duplicated log (cnc_control_enclosure v2)
- **Where:** `~/.claude/skills/INCIDENTS.md` (foreign system file) vs canonical `Claude_Code_SCAD_Skill/claude_skills/INCIDENTS.md`.
- **Symptom:** 11 v2 entries + 1 supersede went to the wrong file. Canonical log missed a full day of work until user caught it ("CIA YRA INCIDENTS.md ... BLET").
- **Root cause:** Assumed the first INCIDENTS.md found was the right one; never asked which log the project uses though the skill folder was known since previous evening.
- **Fix:** 11 entries re-recorded in canonical log with corrected facts + promotion statuses (above). Wrong-file entries left untouched (foreign file, append-only) -- canonical entries note the correction. Rule: one project = one log; confirm path before first append.
- **Already promoted to a rule?** not yet -- candidate: confirm-log-path-first.

### 2026-09-08 -- wall_side louver slots merged into one opening (cnc_control_enclosure v2)
- **Where:** `cnc_control_enclosure/scad/v2/wall_side.scad`.
- **Symptom:** 6 louver slots rendered as one continuous opening; slot length 40 with pitch 15, neighbours geometrically overlap.
- **Root cause:** Pitch-vs-length not checked; copied v1 intent numbers. Same bug class as v1 panel_side.
- **Fix:** Slots 8 wide (Y) x 30 tall (Z), pitch 16 -- 8mm real gap. Verified discrete in render.
- **Already promoted to a rule?** yes -- openscad-cad patterns.scad PATTERN 2 (pitch > length).

### 2026-09-08 -- wall_side() ignored -D side override, L/R identical (cnc_control_enclosure v2)
- **Where:** `cnc_control_enclosure/scad/v2/wall_side.scad` trailing call.
- **Symptom:** `openscad -D side=-1` produced same R geometry; L/R preview PNGs identical shape.
- **Root cause:** File ended with hardcoded `wall_side(1)`, discarding the -D variable.
- **Fix:** Trailing call `wall_side(side=is_undef(side) ? 1 : side)`.
- **Already promoted to a rule?** partially -- value-args pattern in SKILL.md is_undef warning.

### 2026-09-08 -- wall_side outer length poked past front/rear walls (cnc_control_enclosure v2)
- **Where:** `cnc_control_enclosure/scad/v2/wall_side.scad`.
- **Symptom:** Side wall spanned outer_y (221) while front/rear sit at inner faces -- corners overlapped in assembly render.
- **Root cause:** Copied outer dims for all walls; side must be inner_y (fits BETWEEN), front/rear outer_x (cap ends).
- **Fix:** Side cube `[wall_t, inner_y, wall_h]`. Rule: perpendicular walls -- one caps (outer), one fits between (inner).
- **Already promoted to a rule?** not yet -- candidate: outer/inner wall pairing.

### 2026-09-08 -- corner brackets poked through walls in assembly (cnc_control_enclosure v2)
- **Where:** `cnc_control_enclosure/scad/v2/assembly_v2.scad`.
- **Symptom:** 24-wide brackets at +/-(inner/2-8) stuck through wall inner faces in render.
- **Root cause:** Half-width 12 > 8mm inset, unchecked against wall plane.
- **Fix:** Centers to +/-(inner/2-18). Verified clean.
- **Already promoted to a rule?** not yet -- single slip, render check caught it.

### 2026-09-08 -- assembly walls had zero fastening, butt-placed only (cnc_control_enclosure v2)
- **Where:** `cnc_control_enclosure/scad/v2/` (all walls + assembly).
- **Symptom:** User asked "kaip sienos susikabins" -- answer: никак. Zero holes, zero brackets-with-holes.
- **Root cause:** v2 dropped v1 post-socket system with no replacement; no checklist asked "how does each joint fasten".
- **Fix:** corner.scad L-brackets + 4 heat-set holes per wall (z=19/107) + top row for lid. 16 brackets.
- **Already promoted to a rule?** yes -- PATTERN 1 (joint-fastening checklist).

### 2026-09-08 -- lid gravity-held, bosses referenced deleted posts (cnc_control_enclosure v2)
- **Where:** `cnc_control_enclosure/scad/v2/lid_top.scad`.
- **Symptom:** User: "nieks jos netvirtins???" -- correct. Solid d=8 bosses "into wall posts" that don't exist in postless v2.
- **Root cause:** Copied v1 lid intent into postless design.
- **Fix:** 4x M3 clearance holes in lid + top heat-set row in walls. 4x M3x8 from top.
- **Already promoted to a rule?** yes -- same PATTERN 1.

### 2026-09-08 -- hardware.scad single trailing call, siblings unexportable (cnc_control_enclosure v2)
- **Where:** `cnc_control_enclosure/scad/v2/hardware.scad` + empty `duct.scad`.
- **Symptom:** bracket/foot/comb unrenderable alone; STL covered 10 of 14 parts.
- **Root cause:** Multi-module file, one trailing call; empty duct.scad from interrupted write.
- **Fix:** Split into corner/bracket/foot/comb.scad with own calls.
- **Already promoted to a rule?** yes -- PATTERN 3 (one-file-per-part).

### 2026-09-08 -- STLs in wrong dir, bbox glob silently empty (cnc_control_enclosure v2)
- **Where:** session workflow (scad/v2_preview vs nested path).
- **Symptom:** BBox script "passed" with zero output twice -- glob-miss, files elsewhere.
- **Root cause:** Relative-path confusion; empty glob iterates zero times, no error; no count assert.
- **Fix:** Moved to build/v2; re-measured (all <=250).
- **Already promoted to a rule?** yes -- PATTERN 4 (glob-count assert).

### 2026-09-08 -- binary STL parser on ASCII STLs, silent empty (cnc_control_enclosure v2)
- **Where:** session bbox script; snapshot exports ASCII by default.
- **Symptom:** struct parser no rows, exit ok.
- **Root cause:** Assumed binary; ASCII header misread as facet count.
- **Fix:** ASCII vertex grep. Rule: check file/magic before parsing.
- **Already promoted to a rule?** not yet -- candidate: file-magic-first.

### 2026-09-08 -- -D via is_undef ignored, snapshot is_undef broken (cnc_control_enclosure v2)
- **Where:** `assembly_v2.scad`, openscad 2026.06.12; `-D NO_WALLS=1` + is_undef guard left walls rendered.
- **Symptom:** Minimal tests: `-D F7=1` arrives (echo=1) but `is_undef(F7)` -> true regardless.
- **Root cause:** is_undef() broken for -D-defined vars in this snapshot; value-passed flags work, is_undef-gated don't. Not shell quoting.
- **Fix:** Separate guts_v2.scad, no -D. Never gate -D through is_undef() on this build.
- **Already promoted to a rule?** yes -- SKILL.md is_undef warning block.

### 2026-09-08 -- SUPERCEDES: prior-day review corrections (cnc v2 entries)
- **Where:** review of prior-day entries (were in wrong log).
- **Symptom:** (a) louver count said "8", code has 6; (b) -D entries inconsistent.
- **Root cause:** Sloppiness against own code; root cause unresolved at the time.
- **Fix:** (a) Correct count 6. (b) Value-args work, is_undef-gates don't. Canonical entries above carry corrected facts.
- **Already promoted to a rule?** n/a -- meta-entry.

### 2026-09-08 -- coupon series instead of single version, plastic wasted (cnc_control_enclosure)
- **Where:** v1 `din_clip_fit_coupon.scad` (`widths = [35.3, 35.4, 35.5, 35.6]`, 4 variants one print); v2 `coupon.scad` (clip + corner + M3 strip, 3 tests one print).
- **Symptom:** User: "DARAI TIK PO VIENA KUPONO VERSIJA, KAI REIKIA BENT KELIU PATIKRINIMUI" -- printing N variants at once wastes (N-1) prints of plastic and time; failures can't be diagnosed one at a time.
- **Root cause:** Batch thinking (test everything in one print) instead of sequential: print ONE variant, measure result, adjust ONE variable, print next. Same D41 incrementalism class, inverted -- overshooting instead of undershooting, same waste.
- **Fix:** Rule: ONE coupon version per print. Need 4 widths tested = 4 separate small prints, each informing the next. Exception: NONE -- a 15-min single print is cheaper than a 1-hour 4-variant print with 3 useless parts.
- **Already promoted to a rule?** yes -- this entry. Single-coupon rule.

### 2026-09-09 -- BOSL2 overrides translate(), breaks pts[i] indexing in shared templates (openscad-organic)
- **Where:** `openscad-organic/references/organic-patterns.scad` hull_chain(); selftest with `use <BOSL2/std.scad>` in same file.
- **Symptom:** TRACE errors from BOSL2 transforms.scad ($transform unknown); hull_chain balls misplaced; skin()/sweep untested same file.
- **Root cause:** BOSL2 redefines built-in translate(); pts[i] list indexing inside hull_chain resolves through BOSL2 wrapper, not builtin. Shared template file must NOT include BOSL2 itself.
- **Fix:** templates use plain builtins only; BOSL2 include lives in the USER file alongside. Selftest hull_chain/detail_on/base_round without BOSL2: NoError. skin()/limb() documented BOSL2-only, verified by wiki spec not render.
- **Already promoted to a rule?** yes -- NOTE comment in organic-patterns.scad + §0.3 (No BOSL2 = blobs only).

### 2026-09-09 -- helmet modeled from imagination, no research, wrong proportions (salmas_romenu)
- **Where:** `3D_Spausdinimas/salmas_romenu/salmas_romenu.scad` v1.
- **Symptom:** model reads as ball/egg with ring, not a Roman galea; proportions guessed (R100 sphere scaled blindly), no reference dimensions, no agent-reach research before modeling.
- **Root cause:** (a) skipped research — modeled from one artwork photo, never fetched real galea dimensions; (b) ignored two-skill rule (no scad-modeler calculations before geometry); (c) never used agent-reach to inspect real proportions.
- **Fix:** agent-reach research post-facto (Exa): real Imperial-Gallic H = 21.5x19cm inner, cap 17cm, total 28cm; market models split in parts (dome flat-down, crest separate). Workflow rule added to openscad-organic section 0: research-first for replicas BEFORE geometry; v1 archived as blockout.
- **Already promoted to a rule?** yes -- openscad-organic section 0.4 (research-first rule, this entry).

### 2026-09-09 -- v2/v3 vis dar ne galea: brezinys sako viena, kodas skaiciuoja kita (salmas_romenu)
- **Where:** `3D_Spausdinimas/salmas_romenu/salmas_romenu_v2+v3.scad`, `salmas_v3_brezinys.md`
- **Symptom:** front render: kiausinis su plysiu + pelekas sone, ne galea. Tiksliai: veido virsus kode Z=+25 (lentele: +45); kupolas kirstas -50 (lentele: -125); ziedas kybo 0.3mm ore (inner 111.8 > kupolo 111.5); skruostai po kupolu ore (kupolas iki -50, skruostai iki -100); kaklas() apibreztas, bet niekur nekvieciamas (dead code); ausies R18 iskerpa per daug, lieka plonas pelekas.
- **Root cause:** (a) Pattern-1 recidyvas: lenteles skaiciai i koda perkelti isgalvotom formulem ((top-170)/2-20 vietoj (top+bottom)/2) - niekas nepatikrino ar formule grazina lenteles skaiciu; (b) apacios -50 nukopijuota is v1 sferos-logikos, nepritaikyta elipsoidui su skruostais; (c) ziedas skaiciuotas nominaliai be 1mm ileidimo (unionui butinas overlap); (d) renderiai is vieno nepazymeto kampo - "taisymai" ejo ne i ta asi (Y sumaisyta); (e) STL patikros skaiciumi nebuvo - atskiri kunai ir kabantys ziedai nematomi is toli.
- **Fix:** v4: 18 parametru rasomi TIESIAI (centras=(top+bottom)/2, jokiu tarpiniu formuliu); apacia -125; ziedas inner=ax-1; skruosto X=cheek_x(z) seka pavirsiu; ausis = atviras krasto ipjovimas, ne uzdara skyle; 3 pazymetu kampu renderiai; STL bbox patikra. Kaklo liezuvis, V ornamentas, kniedes - v5.
- **Already promoted to a rule?** pasiulyta: "brezinio skaicius i koda tik tiesiogiai + assert; tarpine formule be patikros = draudziama".

### 2026-09-10 -- v4 darytas be pilno skill-loading: organic tik skaitytas, ne krautas (salmas_romenu)
- **Where:** `3D_Spausdinimas/salmas_romenu/` v4 sesija (si sesija).
- **Symptom:** openscad-cad krautas per skill-tool ir taikytas (render 3 kampai, Manifold, STL, INCIDENTS); openscad-organic tik perskaitytas failu (`read`), ne krautas per skill-tool — patikrinta: skill-registre tokio vardo NERA (skill-tool grazina "unknown"); BOSL2 skin/sweep nenaudoti (v4 = hull-blob, bet tai nepasakyta garsiai); scad-modeler tik dabar krautas (check_*.py nenaudoti, bbox tik rankinis python); projekto README.md neparasyta (openscad-cad §5 reikalauja).
- **Root cause:** skubejimas prie geometrijos + "faila perskaiciau = skill panaudojau" iliuzija. Skill-loading yra proceduros vartai (garantuoja visa konteksta), failo skaitymas ju neperjunge.
- **Fix:** scad-modeler pakrautas per skill-tool (siame zingsnyje); v5 daryti su pilnu load (cad+modeler), BOSL2 patikra pirma (doctor.py), check_dimensions.py vietoj rankinio bbox, README.md irasyti. openscad-organic registruoti arba pakeisti keliu i faila — kol kas krauti per read.
- **Already promoted to a rule?** ne — tik siuloma: "skaitytas failas != krautas skill; be skill-load geometrijos nepradeti".

### 2026-09-10 -- v6/v7 sokinejo prie geometrijos be uzsaldyto speco (server_rack_modular_v4)
- **Where:** v6 (tray-dugnas + deze-duct) ir v7 (bankas/gaubtas/fan pozicijos), 4 render iteracijos per vakara.
- **Symptom:** kiekvienas render rode vis kita defekta; vartotojas: vazineji ratais, nesukuri specifikacijos dokumento su vidu dydziais.
- **Root cause:** (a) vidiniu daliu erdvinis kontraktas neuzfiksuotas pries geometrija, tik bendras vokas; (b) layout pozicijos keistos pagal renderi, ne is matmenu grandines; (c) 11 saltiniu tyrimas darytas PO v6 geometrijos, ne Stage 0.
- **Fix:** SPEC su vidinemis grandinemis UZSALDYTAS pries geometrija; jokia layout pozicija neatsiranda is renderio, tik is grandines; tyrimas visada Stage 0.
- **Already promoted to a rule?** not yet, siulyti i scad-modeler planning.md kaip layout-poziciju-saltinio pastraipa.

### 2026-09-10 -- top projekcija melavo apie flansu kolizija (server_rack_modular_v4 v7)
- **Where:** exhaust_hood.scad, 2 flansai Z-offset 50.
- **Symptom:** top view rode ziedu persidengima, nors FCL kūnai atskiri (2 bodies, abu watertight).
- **Root cause:** ortho projekcija suglaudzia skirtingu Z objektus i viena plokstuma; sprendimas priimtas is Z grandines skaiciavimo (tarpas 26 oro), ne is renderio.
- **Fix:** pasitiketa skaiciumi (body count + watertight), ne akimi; front view patvirtino skirtingus auksius.
- **Already promoted to a rule?** not yet, susije su SKILL §1 ispėjimu (render = sanity layer, ne gate).

### 2026-09-11 -- sonines plokstes: (a) be jokio tvirtinimo, (b) kirtosi su stulpais (server_rack_modular_v4/v8)
- **Where:** `v8/scad/parts/side_panel.scad` + `v8/scad/layout.scad`.
- **Symptom:** (a) plokste buvo plikas 3x229.7x200 stačiakampis — nulis tvirtinimo elementu; (b) plokste Y -237.7..+237.7, stulpai ±229..±247 -> persidengimas 1499.6 mm3 (8.7 mm kiekviename gale).
- **Root cause:** (a) "nukertu smulkmenas, kad surinkimas susikompiuotu" — nuemiau kraigus ir insert boss'us ir NEGRAZINAU, nes niekas to nepagavo (connectivity'io patikra ziuri TIK atskira dali, ne ar ji turi tvirtinimo elementus); (b) formulėje `case_depth/2` (250) vietoj `post_y` (239) — tas pats klaidos tipas kaip D41/D42: matmuo paimtas nuo KORPUSO krašto, kai reikejo nuo STULPO centro.
- **Fix:** vienas saltinis `params.scad` (`post_y`, `side_span_half`) — layout ir detale naudoja ta pati kintamaji, nebe dvi atskiras formules; persidengimas 0, tarpas 0.31 mm (= shadow_gap). Tvirtinimas pridetas atskiru zingsniu.
- **Papildomai:** AESTHETIC_SPEC §9 panele orientacija buvo neteisinga ("vertikaliai" -> fasade 1000 sluoksniu liniju). Taisykle pataisyta: spausdinti GULSCIAS, isorine puse ant lovos. Pamoka: spec'e irasytas MECHANINIS teiginys nebuvo patikrintas render'iu ar skaiciavimu — teksto autoritetas != patikrintas faktas.
- **Already promoted to a rule?** Ne — siuloma: "detales tvirtinimo elementai tikrinami atskiru check'u, ne tik connectivity".

### 2026-09-10 -- 45deg flanges appeared in geometry with no requirement behind them (server_rack_modular_v4 v7)
- **Where:** `v7/scad/parts/exhaust_hood.scad` (flanges above the GPU bank).
- **Symptom:** user asked "kas tie 45 laipsniu kampu?" -- angular flanges materialised in the render that neither the SPEC nor the user ever requested.
- **Root cause:** geometry invented during render iteration to make a fit "work out", instead of deriving the shape from the frozen SPEC's internal dimension chain. Same class as the v7 layout churn: a render is not a requirements source.
- **Fix:** SPEC with internal chains frozen before geometry; any shape not traceable to a SPEC line must be named and justified in `calculations.md` or removed.
- **Already promoted to a rule?** Ne -- siuloma: "kiekviena geometrijos forma turi atsekama SPEC eilute; renderis nera reikalavimu saltinis".

### 2026-09-10 -- unexplained circle ("kas tas ratas random") visible in render (server_rack_modular_v4 v7)
- **Where:** `v7` assembly render, `assembly_a_iso.png`.
- **Symptom:** user saw a stray circular primitive in the assembly and could not tell what it belonged to; nothing in the report explained it.
- **Root cause:** a helper/leftover primitive (or an ungrouped cut leftover) made it into the assembly render without being part of any named part. No check compares "shapes visible in the render" against "parts declared in layout.scad" -- so an orphan solid renders happily.
- **Fix:** before delivering a render, account for every visible solid: each must map to a named part in `layout.scad` or be removed. Candidate automated check: rendered body count vs declared part count.
- **Already promoted to a rule?** Ne -- siuloma: "render'yje matomas kunas turi tureti varda layout.scad; orfanai salinami".

### 2026-09-10 -- user had to ask whether the skill was actually loaded; procedure ran from read files (server_rack_modular_v4)
- **Where:** session-level process, `scad-modeler` + `openscad-cad`.
- **Symptom:** user asked "kuriuos tu skills naudoji? is kurios lokacijos?" and "kokia lokacija scad-modeler?" -- i.e. had to audit the agent's own tooling mid-session because the output looked like the discipline was not applied.
- **Root cause:** "read the SKILL.md file" was treated as equivalent to "loaded the skill through the skill mechanism". Reading gives the text; loading is the procedural gate (the invocation is what the harness records and what guarantees the full procedure, not the presence of text in context).
- **Fix:** state at the start of any geometry work which skills are loaded and from which path; if the skill tool cannot resolve a name, say so explicitly instead of silently substituting a file read.
- **Already promoted to a rule?** Ne -- siuloma: "skaitytas failas != krautas skill; pries geometrija deklaruoti pakrautus skill'us ir kelius".

### 2026-09-10 -- tiered validation available but only partially used (server_rack_modular_v4 v7/v8)
- **Where:** `scad-modeler` tier system vs what actually ran in the session.
- **Symptom:** user: "kodel tu neini per tuos scad-modeler irankius ir netikrini skirtingu tier???" -- confidence tiers existed and were not walked through systematically.
- **Root cause:** `validate_scad.sh --all` was run (14 times) but the tier ladder was never used as the ordering discipline: the same 3 unique gate-result signatures repeated across the session, i.e. re-running the same bundle instead of climbing Tier 1 -> 5 and naming which tier the part actually reached.
- **Fix:** name the achieved tier in the final response (Tier 1..5 per `confidence-tiers.md`), and when a gate fails, fix the cause or drop a tier -- do not re-run the same bundle hoping for a different signature.
- **Already promoted to a rule?** Ne -- siuloma: "kiekvieno etapo gale ivardinti pasiekta tier; pakartotinis tas pats vartu rinkinys be priezasties = kvapas".

### 2026-09-11 -- static PNG render is not a sufficient evaluation channel (server_rack_modular_v4 v8)
- **Where:** `v8/renders/asm_iso.png` + `asm_side.png` + `asm_front.png` delivered as the review artefact.
- **Symptom:** user: "as nelabai galiu efektyviai vertinti is paveiksliuko... man reikia sugebeti sukioti 3d!" -- every visual judgement so far had been made through still images, and the user could not actually inspect the model.
- **Root cause:** the skill's review loop assumes a human/model can judge correctness from a few fixed-angle PNGs. For a 3D object this is a genuinely weaker channel: hidden geometry, interpenetration behind a wall, and orientation errors are invisible from chosen angles (confirmed again by the top-view flange false alarm, INCIDENTS 2026-09-10).
- **Fix:** deliver an interactive path alongside the render -- export STL/3MF and state the viewer/command, so the user rotates the real model instead of trusting selected angles. Candidate: ship an assembly STL by default in the final report, not only on request.
- **Already promoted to a rule?** Ne -- siuloma: "galutiniame pristatyme VISADA interaktyvus perziuros kelias (STL + viewer), ne vien PNG kampus".


### 2026-09-12 -- maintainer files were symlinked into the runtime skills dir and agents read them (eval, 40 paleidimu)
- **Where:** `~/.dsh/skills/INCIDENTS.md` ir `~/.dsh/skills/requirements.txt` -- abu symlink'ai i skill repo, salia tikru skill katalogu.
- **Symptom:** POST rankos agentai atidarinejo `INCIDENTS.md` 7/20 paleidimu, `NEXT.md` 3/20, `templates/` 4/20. PRE rankoje -- 0/20 visuose trijuose.
- **Root cause:** `INCIDENTS.md` (1222 eil., ~22k tokenu) buvo INSTALIUOTAS kaip runtime failas (README.md:116 dokumentuoja `ln -s`). Jis skirtas zmogui-priziuretojui, bet atsidures greta skill'u jis patenka i agento pasiekiamuma. Perskaicius jis lieka cached prefikse ir perskaitomas KIEKVIENA tolesni zingsni.
- **Kaina:** ne vienas failas, o svertas. Mato 40 paleidimu (20 poru, tas pats atvejis + tas pats run): zingsniai 3.40 -> 4.95 (+46%), cacheRead 166k -> 304k (+83%), VISKO 178 648 -> 338 452 (**+89.5%**, poromis +106%). Skaidymas: **+55% nuo zingsniu, +45% nuo konteksto-per-zingsni** (dydis x zingsniai, todel dauginasi). Koreliacija(zingsniu %, kainos %) = **+0.92**.
- **Fix:** pašalinti `INCIDENTS.md` ir `requirements.txt` symlink'us is `~/.dsh/skills` ir `~/.claude/skills`. Failai lieka repo; atkūrimas (jei prireikia) -- `ln -s <repo>/claude_skills/INCIDENTS.md ~/.dsh/skills/INCIDENTS.md`. Priziuretojo failai (INCIDENTS, NEXT, tests/, golden_scad/) neturi buti runtime skill kataloge.
- **Pamoka:** "failu skaitymas" NERA kainos matas (jie gali buti dideli). Kaina = zingsniai x kontekstas-per-zingsni; abu skaitomi is `usage` irasu. Matavimo irankis: `golden_scad/measure.py`.
- **Already promoted to a rule?** Ne -- siuloma: "runtime skill kataloge tik tai, ka agentas TURI skaityti; priziuretojo artefaktai -- i `research/` ar `_dev/`".

### 2026-09-12 -- check_connectivity.py reported 2 bodies while printing 3122, and suggested the wrong EXPECTED_BODIES
- **Where:** `scad-modeler/scripts/check_connectivity.py`, lines 101 vs 106.
- **Symptom:** naujas testavimo bazės modelis (CADAM `02-knurled-control-knob.scad`) renderinasi i 155 920 trikampių, kurie skyla i **3 122** atskirus komponentus. Checker'is atsakė `has 2 disconnected bodies`, ištisė **3 124 eilutes** sąrašo ir pasiūlė `// EXPECTED_BODIES: 2`.
- **Root cause:** checker'is **skaičiavo vienu metodu, o spausdino kitu** -- `actual = mesh.body_count` (101 eil.) vs `mesh.split(only_watertight=False)` (106 eil.). Ant degeneruotų sliver'ių (volume n/a) `body_count` skaičiuoja tik validžius kūnus: 3122 komponentai, bet tik **48** turi tūrį, todėl `body_count` = 2. Pasiūlymas `EXPECTED_BODIES: 2` būtų buvęs **neteisingas** -- jis būtų įteisinęs sudužusį modelį kaip '2 kūnus'.
- **Poveikis:** vartotojas, kuris būtų paklausęs checker'io, būtų gavęs skaičių, kuriuo negalima tikėti, ir 3 000+ eilučių konteksto triukšmo vietoj verdikto.
- **Fix:** vienas tiesos šaltinis -- `parts = mesh.split(only_watertight=False); actual = len(parts)` naudojamas IR skaičiavimui, IR sąrašui. Sąrašas ribojamas iki `MAX_BODIES_SHOWN = 20` su `"... and N more components (S/N are valid solids)`. Ant tikro modelio: 3124 -> **23 eilutės**, ir pasiūlymas dabar `EXPECTED_BODIES: 3122`.
- **Naujas fixture:** `tests/fixtures/connectivity_shattered_fail` -- 241 salos, tikrina, kad (a) skaičius sutampa su sąrašu, (b) pasiūlymas atitinka skaičių, (c) ribojimas pasako, kiek paslėpta. Suite: **26 passed, 0 failed** (buvo 25).
- **Kaip rasta:** ne bandymu, o tuo, kad atsirado **testavimo bazė su tikrais, dideliais modeliais**. 10 lengvų golden atvejų šito niekada nebūtų parodę -- jie neturi nei tūkstančių komponentų, nei degeneruotų sliver'ių.
- **Already promoted to a rule?** Ne -- siuloma: "checker'is privalo skaičiuoti ir spausdinti iš TO PAČIO šaltinio; verdiktas niekada nesprendžiamas iš kito kintamojo nei sąrašas".
### 2026-09-12 -- 6 is ~14 patikru tyliai nepaleidziamos: exit 0 atrodo kaip 'viskas patikrinta'
- **Where:** `scad-modeler/scripts/validate_scad.sh` -- opt-in patikros (bore_reachability, collisions, attachment, subfeature_overlap, printability, features).
- **Symptom:** paleidus `--all` ant 11 tikru projektu, `server_rack_modular` grazina **exit 0** su 6 PASS + 2 SKIP. Bet `bore_reachability`
`collisions`
`attachment`
`subfeature_overlap`
`printability` ir `features` **neisveda ne vienos** `CHECK_RESULT` eilutes -- ju net nera sarase.
- **Root cause:** sios patikros reikalauja deklaraciju failu (`bores.json`, `joints.json`, `attachments.json`). Nera failo -> patikra tyli. Tai **ne SKIP** (SKIP bent matomas), o visiska tyla: kvieciantis kodas (`check_rules.py`) negali atskirti 'nepaleista' nuo 'neegzistuoja'.
- **Kodel tai incidentas, o ne dizainas:** pacio `validate_scad.sh` komentaras (2026-08-19) sako, kad butent si aklaviete jau buvo fiksuota: "there was no way to tell 'this check failed' from 'this check never ran' from the exit code alone". Ji buvo sutvarkyta `CHECK_RESULT` eilutemis -- bet tik toms patikroms, kurios VISADA paleidziamos. Opt-in patikroms ta pati problema liko.
- **Praktinis poveikis:** `server_rack_modular`, `server_rack_modular_v3/muse_redesign` ir `cnc_control_enclosure/archive/v1` praejo su exit 0, turedami 5-6 veikiancias patikras is ~14. Vartotojas, pamates 'validacija praejo', neturi kaip suzinoti, kad giliausios patikros nepaleistos.
- **Ka rado tos patikros, kurios VISADA paleidziamos:** `connectivity=FAIL` **5 is 11 projektu** (chassis, rack_v2, rack_v4, rack_v4/v5, rack_v4/v8) -- patvirtinta nuosekliai, po viena, ne lygiagreciai. Tai pirmas kartas, kai patikros paleistos ant tikro projektu korpuso, o ne ant sintetiniu fixture'u.
- **Siulomas fix:** kiekviena opt-in patikra privalo isvesti `CHECK_RESULT <name>=SKIP` su priezastimi ('no bores.json'), kai deklaracijos nera. Tada 'validuota' tampa audituojama: skaicius paleistu patikru yra zinomass, o ne spejamas.
- **Already promoted to a rule?** Ne -- siuloma: "patikra, kurios nepaleidai, turi buti matoma kaip SKIP su priezastimi; tyla nera PASS".
### 2026-09-12 -- ADDENDUM prie tyliu patikru iraso: tikslus skaicius -- 4 checker'iai NEKVIECIAMI IS VISO
- **Where:** `scad-modeler/scripts/validate_scad.sh` -- kvieciami 12 is 16 checker'iu.
- **Tikslus radinys:** `validate_scad.sh` **nekviecia** `check_dependencies.py`, `check_intake.py`, `check_printability.py`, `check_subfeature_overlap.py`. Ju niekada nepaleidzia jokia projekto validacija.
- **Ir tai, kas kvieciama, bet tyli:** ant `server_rack_modular` (exit 0) log'e yra **0 paminejimu** zodziu collision, printability, subfeature, feature, intake. `check_collisions.py` ir `check_features.py` yra skripte (po 3 ir 1 kvietima), bet siame projekte neisvede nieko -- ne OK, ne SKIP, ne FAIL.
- **Is ko sudarytas 'validacija praejo':** 6 `CHECK_RESULT`=PASS + 2 SKIP. `check_dimensions.py` **suveike** (mato 'OK: base.stl bbox ... within'), bet **neisveda** `CHECK_RESULT` eilutes -- tad kvieciantis kodas jo verdikto nemato.
- **Skripto `CHECK_RESULT` zodynas is viso 10 vardu:** analytic_bounds, assumptions, attachment, bore_reachability, connectivity, margin_provenance, mechanics, param_context, plan, service_envelope. `dimensions`
`collisions`
`printability`
`subfeature_overlap`
`features`
`intake`
`dependencies` -- ne vieno is ju.
- **Kodel tai svarbu:** `SKILL.md` ir `rules_manifest.yaml` apraso 18 taisykliu. Jei 4 checker'iai nekvieciami, o 3 tyli, tai '18 taisykliu laikomasi' negali buti tikrinama kodu -- tik teigiama.
- **Fix (tas pats kaip pries tai):** kiekvienas checker'is privalo isvesti `CHECK_RESULT <name>=SKIP <priezastis>`, kai jo ivesties nera. Nepaleistas checker'is turi buti matomas kaip SKIP, o ne tiketis, kad niekas nepastebes.
- **Ka tai reiskia testavimo bazei:** matuoti reikia ne 'pass/fail', o **kiek patikru paleista**. Be to 'validuota' nera audituojamas teiginys. Siuo metu `measure.py` matuotų kaina, bet ne patikru padengima -- tai antras matas, kuri reikia prideti.
- **Already promoted to a rule?** Ne -- siuloma: "validacijos ataskaita privalo isvardinti VISUS checker'ius su jų statusu (PASS/FAIL/SKIP+priezastis); tylejimas = neatitikimas".
### 2026-09-12 -- PADENGIMAS SUTVARKYTAS: 8 -> 17 CHECK_RESULT; islindo 3 nematomi dimensions FAIL
- **Where:** `scad-modeler/scripts/validate_scad.sh`.
- **Ka padariau:** (a) pridejau SKIP sakas `bore_reachability` ir `attachment`, kai deklaracijos failo nera; (b) `dimensions` ir `features` dabar skaiciuoja kiek daliu deklaravo ir isveda agreguota `CHECK_RESULT`; (c) `collisions` isvedamas atskirai, net kai mechanika nepasileidzia; (d) keturi checker'iai, kurie NERA vartai, isvardinti kaip SKIP su priezastimi.
- **Rezultatas ant 11 tikru projektu:** padengimas **8 -> 17** patikru. Anksciau matydavosi 6 PASS + 2 SKIP; dabar visi 17 su statusu ir priezastimi.
- **Islindo trys anksciau NEMATOMI gedimai:** `dimensions=FAIL` projektuose `server_rack_modular_v4`, `v4/v5`, `v4/v8` -- konkreciai `nas_post.stl`, `post.stl`, `side_panel.stl` bbox mismatch. Patikra veike ir krito visus tuos kartus; niekas to negalejo pamatyti, nes ji neisvesdavo `CHECK_RESULT`.
- **Kodel 4 checker'iai NEPRIJUNGTI kaip vartai (patikrinta, ne speliota):** `check_printability.py` ant `server_rack_modular` **FAIL 4/4** realiu daliu -- 149057 mm^2 overhang ant assembly, 0.014 mm 'sienos' ant frame_module (tai degeneruotas sliver'is, ne siena). Kaip vartai jis zlugdytu kiekviena projekta. `check_subfeature_overlap.py` reikalauja **solo** sub-moduliu STL (pries `union()`); padavus vientisas dalis jis palygino dvi dalis, kurios tik bendrai turi koordinasciu pradzia, ir pranese 196779 mm^3 'overlap' tarp `base.stl` ir `frame_module.stl`.
- **Skaicius, kuris lieka:** is 186 patikru-paleidimu (11 projektu x 17) -- **PASS=73, SKIP=102, FAIL=11**. T.y. 55% patikru vis dar neivyksta. `attachment`, `intake`, `printability`, `subfeature_overlap`, `dependencies` -- SKIP=11/11, t.y. **ne viename projekte**.
- **Ir tai, kas blogai projektuose:** `connectivity=FAIL` 5/11 (rack_v4 seimose 8+ dalys su atskirais kunais: back_panel 5, beam_node_test_v53 6, front_panel 5, nas_joint_test_v53 6 ...). Dalis ju -- testiniai kuponai, kurie GALBUT daugiadaliai tycia, bet niekur nedeklaruota, tad kodo negalima atskirti nuo defekto.
- **Likusi spraga:** 16 is 17 patikru turi `CHECK_RESULT` eilute, bet `steering_reduction_gearbox` vis tiek rodo 16, ne 17 -- viena eilute dingsta, nes script'as iseina anksciau. Neisspresta.
- **Already promoted to a rule?** Ne -- siuloma: "patikra, kurios nepaleidai, privalo isvesti SKIP su priezastimi; tyla nera PASS, o 'viskas praejo' be padengimo skaiciaus nera teiginys".
### 2026-09-12 -- Patikrinti FAIL'ai: 3 skirtingi atsakymai, ir vienas ju pakeicia checker'io kalba
- **Where:** 11 tikru projektu FAIL'ai, patikrinti po viena iki šaltinio.

- **1. KLAIDINGAS TEIGIAMAS -- `post.scad` (v8), du FAIL'ai is vieno dalyko.** `connectivity` + `bbox` abu krito, nes failo pabaigoje yra **perziuros kodas, renderinantis DU variantus**: `post_segment(2, gy=1, gx=-1); translate([post_w + 12, 0, 0]) post_segment(1);`. Realiai renderinasi 47.979 x 17.979 x 96.389 (du stulpai greta), o deklaracija `EXPECTED_BBOX: [18, 18, 88.9] (2U) / [18, 18, 44.45] (1U)` apraso VIENA. Checker'is teisus, bet kaltas ne modelis -- kaltas **failo tipas**: tai perziuros failas, o `validate_scad.sh --all` kiekviena `parts/*.scad` laiko viena spausdinama dalimi.
- **Kiek tokiu failu:** `server_rack_modular_v4` -- 4 is 17: `beam_node_test_v53` (3 kvietimai), `joint_test_v4` (4), `nas_bay` (2), `nas_joint_test_v53` (3). Visi 4 ju connectivity FAIL'ai -- laukti, ne defektai.

- **2. TIKRAS, BET TRIVIALUS -- `node.scad` (v8) bbox.** `minkowski()` su `sphere(r = fillet_post/2, $fn = 24)`. $fn=24 rutulio briauna nepasiekia tikrojo spindulio: santykis cos(pi/24) = 0.99144. `node_s = 26` * 0.99144 * (pakoreguota) -> **25.9786**, t.y. truksta **0.0214 mm**. Formule: 2*r*(1 - cos(pi/$fn)). Checker'is teisus, geometrija tikrai 0.02 mm mazesne uz deklaracija; tai fillet'o facetskumo artefaktas, ne projektavimo klaida.

- **3. TIKRAS, IR PASIRODO VISOSE PANELESE -- magnetu kisenes.** `front_panel`, `back_panel`, `nas_side_panel` po 5 kunus; `nas_post` -- 3. Ismatavus: kiekvienas turi **1 dideli kuna + 4 (arba 2) vienodus 4.6 x 1.7 x 4.6** su `vol=n/a`. Tai **tiksliai magnetu kiseniu matmenys is kodo** (`cube([4.6, 1.7, 4.6], center = true); // H 4.6x1.7 (D45 standartas)`), kurios yra `difference()` viduje. Atimtis palieka **nulinio turio apvalkalus** -- ne atskiros spausdinamos dalys.
- **Kodel tai pakeicia checker'io kalba:** iki siol jis sakydavo tik 'has 5 disconnected bodies', ir vienintelis pasiulymas buvo `// EXPECTED_BODIES: 5` -- t.y. iteisinti suduzusi modeli. Dabar jis prideda: `'NOTE: only 1 of 5 component(s) are valid solids; the other 4 are zero-volume/non-manifold shells (a coincident-face or unbounded-pattern boolean artifact, not separate printable pieces -- prefer fixing the boolean over declaring EXPECTED_BODIES)'`.
- **Pamoka:** 'N kunu' nera tas pats kaip 'N kietu kunu'. Vienas skaicius be isskaidymo vertė klaidinti du kartus: CADAM knob (2 is 3122) ir sios 4 paneles (1 is 5).
- **Suite:** 26 passed, 0 failed.
- **Kas dar neisspresta:** `nas_bay.scad` (2 kvietimai -- perziuros failas, laukta) ir klausimas, ar magnetu apvalkalu artefaktas kenkia spausdinimui, ar tik STL eksportui. Tam reikia perpjauti STL per slicer'i.
- **Already promoted to a rule?** Ne -- siuloma: "kiekvienas strukturos skaicius (kunai, dalys, komponentai) privalo buti isskaidytas i validzius ir degeneruotus; vienas skaicius be isskaidymo yra klaidinantis".
### 2026-09-12 -- PREVIEW_FILE: 4 perziuros failai kure klaidingus FAIL'us kiekviena paleidima
- **Where:** `scad-modeler/scripts/validate_scad.sh`, `parts/*.scad` ciklas.
- **Symptom:** `validate_scad.sh --all` kiekviena `parts/*.scad` laiko viena spausdinama dalimi. `server_rack_modular_v4`: 4 is 17 failu yra **variantu perziuros** (renderina 2-4 variantus greta). Kiekvienas jų duodavo FAIL kiekviena paleidima.
- **Konkretus atvejis (istirtas iki šaltinio):** `post.scad` (v8) pabaigoje yra `post_segment(2, gy=1, gx=-1); translate([post_w + 12, 0, 0]) post_segment(1);`, o 38 eiluteje parasyta `// perziura: 2U su grioveliu, 1U be`. Renderinasi 47.979 x 17.979 x 96.389 pries deklaruota 18 x 18 x 88.9, ir 2 atskiri kunai. Du FAIL'ai -- `connectivity` ir `dimensions` -- abu is vieno dalyko.
- **Kodel tai buvo svarbu:** klaidingas teigiamas kiekviena paleidima yra tai, kaip validacija numiršta. Po keliu 'FAIL, bet cia viskas gerai' FAIL'as nustoja reikšti ka nors, ir tikras defektas praeina. Tai brangesne klaida uz praleista patikra.
- **Fix:** ketvirtas opt-in žymeklis, tos pačios formos kaip trys esantys (`EXPECTED_BBOX`, `EXPECTED_HOLE`, `EXPECTED_BODIES`): `// PREVIEW_FILE: <priezastis>`. Su juo praleidziami `connectivity`, `EXPECTED_BBOX` ir `EXPECTED_HOLE`; render'is VIS TIEK paleidziamas (perziura, kuri nustojo kompiliuotis, vis dar klaida), ir paleidimo pabaigoje spausdinama `INFO: N file(s) declared PREVIEW_FILE`.
- **Ismatuota:** v4 -- **16 FAIL eiluciu -> 13**; v8 -- **5 -> 3**. Visi likusieji FAIL'ai tikri (`front_door.stl` 2 kunai, `node.stl` bbox). Klaidingi dingo, tikri liko -- tai ir yra norimas rezultatas.
- **Ko NEPAZYMEJAU:** `nas_bay.scad` renderina `nas_floor()` ir `nas_deck()`, o jo antrašte sako 'THREE kinds of printed pieces'. Tai **dvi tikros spausdinamos dalys**, ne perziura. Pazymejimas butu paslepes struktūrine problema. Teisingas sprendimas -- isskirti i du failus arba deklaruoti `EXPECTED_BODIES`, ir tai yra projektavimo sprendimas, ne checker'io.
- **Riba, kuri laikyta:** checker'is gali pasakyti 'sitas failas nera viena dalis'. Jis negali nuspresti, KURIOS dalys turi buti spausdinamos -- tai zmogaus sprendimas. Todėl pazymejau tik tuos 4, kuriu šaltinis pats sako 'perziura' arba 'testai', ir palikau `nas_bay`.
- **Testas:** atskiras projektas `/tmp/prevtest` -- be žymeklio `FAIL`, su žymekliu `SKIP` + `connectivity=PASS` + `INFO`. Suite: 26 passed, 0 failed.
- **Already promoted to a rule?** Ne -- siuloma: "failas, kuris renderina daugiau nei viena dali, privalo apsibrežti; validatorius neturi spelioti, ar tai viena dalis, ar perziura".
### 2026-09-12 -- Ertmes, ne kunai: check_connectivity skaite 5 tikras dalis kaip sudužusias
- **Where:** `scad-modeler/scripts/check_connectivity.py`.
- **Symptom:** `server_rack_modular_v4` -- 5 paneles (`back_panel`, `front_panel`, `nas_side_panel`, `side_panel`, `top_panel`) po 5 kunus, `nas_post` -- 3, `post` -- 7. Kiekvienas FAIL.
- **Mano pirmas paaiskinimas buvo NETEISINGAS.** Parasiau, kad tai 'zero-volume/non-manifold shells, boolean artifact'. Patikrinęs paaiskinima radau priesingai.
- **Tikrasis dalykas (ismatuota ant `back_panel.stl`):** didelis kunas 253.9 x 3 x 108.9, vol 81402, watertight. Kiekvienas mazasis: **`watertight=True`**, 4.6 x 1.7 x 4.6, centroidas **didelio kuno viduje**, ir **signed volume = -35.972** (neigiamas!). |-35.972| = 4.6 x 1.7 x 4.6 -- tiksliai magneto kisenes turis.
- **Root cause:** trimesh grazina komponento turi **su apvijos zenklu**, o uždara ertme yra watertight apvalkalas su **neigiamu** turiu. Checker'is skaite `len(parts)`, t.y. medžiaga + ertmes kartu. Panelė yra **vienas validus kietas kunas** su 4 vidinemis ertmemis; jos nera atskira medžiaga.
- **Poveikis buvo dvigubas:** (a) 5 klaidingi FAIL'ai kiekviena paleidima -- tas pats 'klaidingas teigiamas = mirtis validacijai' pattern'as; (b) mano paties klaidingas paaiskinimas butu nukreipes vartotoja 'taisyti boolean', kai boolean'as teisingas.
- **Fix:** komponentai skaidomi i `material (volume > 0)`, `voids (volume < 0)` ir `degenerate (0 arba NaN)`. Skaičiuojami tik `material`. Ertmes pranesamos atskirai -- ir prie PASS: `'note: 4 enclosed internal cavity/cavities (size(s) [(4.6, 1.7, 4.6)]) -- verify these are intended (magnet or nut pocket, air gap); they cannot be seen from outside.'`
- **Kodel ertmes vis tiek pranesamos:** ertme, kurios niekas nenorejo, yra nematoma visuose kituose patikrose ir render'yje -- dalis is isores atrodo kieta.
- **Ismatuota:** `server_rack_modular_v4` -- **16 FAIL -> 13 (PREVIEW_FILE) -> 4**. 8 ertmes pranestos kaip informacija. CADAM `02-knurled-control-knob` **vis tiek FAIL** -- 48 tikri medžiagos kunai, 3022 degeneruoti. Tikri gedimai nelieciami.
- **Sulaužiau savo fixture'a ir tai gerai:** `connectivity_shattered_fail` tikrino tikslią formuluote `"... and N more components"`; pakeitus i 'more material components' jis nukrito. Suite tai pagavo; fixture atnaujintas. 26 passed, 0 failed.
- **Likę 3 bbox neatitikimai (ismatuota):** `nas_post` X/Y 0.0288 mm, Z **1.400**; `post` X/Y 0.0214, Z **0.5107**; `side_panel` X **0.450**, Y **0.600**. Mazieji (0.02-0.03 mm) -- ta pati `minkowski` + `$fn` klase kaip `node.scad` (formule 2*r*(1 - cos(pi/$fn))). Didesnieji (0.45-1.4 mm) yra 15-30x didesni uz triuksmo lygi -- tikri deklaracijos/render neatitikimai.
- **Naujas klausimas, kurio neissprendziau:** `check_dimensions.py` tolerancija skaičiuojama is `$fn/$fa/$fs` kaip **apvalumo** riba. `minkowski` su facetuotu rutuliu prideda kita klaidos nari, kurio formulė nemato. Ar kelti grindis nuo 0.005 mm iki ismatuoto triuksmo lygio (~0.05 mm), ar palikti ir leisti dalei deklaruoti `--abs-tol` -- sprendimas nepriimtas.
- **Already promoted to a rule?** Ne -- siuloma: "mesh komponentas su neigiamu turiu yra ertme, ne kunas; nera atskiros medžiagos be zenklo patikros".
### 2026-09-12 -- KLAIDINGAS PASS: dalis, kuri visai nesirenderino, gavo connectivity=PASS
- **Where:** `scad-modeler/scripts/validate_scad.sh`, `validate_file()` ir `--all` agregatas.
- **Kaip rasta:** paleidus per 11 projektu, `front_swerve_module` grazino `exit=1` su 'FAIL: at least one check above failed', BET ne viena `CHECK_RESULT` nebuvo FAIL -- 7 PASS + 10 SKIP. Tai priesingas jausmas nei visi ankstesni radiniai: ne klaidingas FAIL, o **klaidingas PASS**.
- **Root cause:** `parts/a_arm.scad` renderinasi i tuscia top-level objekta. `openscad` apie tai pasako ('Current top level object is empty.') bet **grazina exit 0**; ji pagavo tik `[ ! -s \"$stl\" ]` patikra, kuri nustato `OVERALL_FAIL=1` ir grazina 1. Bet `validate_file` **neisveda jokios** `CHECK_RESULT` eilutes siai situacijai, o `PART_CONNECTIVITY_FAIL` lieka 0 -- nes `check_connectivity.py` niekada nebuvo paleistas. Todėl agregatas isveda `CHECK_RESULT connectivity=PASS`.
- **Kodel tai blogiau uz klaidinga FAIL'a:** klaidingas FAIL moko ignoruoti isvesti. Klaidingas PASS sako 'patikrinau ir viskas gerai' apie dali, kurios niekas nepatikrino. Tai ta pati klase, kuri `validate_scad.sh` komentare jau fiksuota 2026-08-19 ('no way to tell this check failed from this check never ran') -- ir ta pati, del kurios siandien darytas padengimo darbas. Pasirodo, render'io kelias irgi buvo tyli.
- **Fix:** `render` tampa pirma-klases patikra: `CHECK_RESULT render=PASS|FAIL`, su konkreciu failu sarasu. Ir `RENDER_FAIL -ne 0` **vetuoja** `connectivity=PASS` -- vietoj jo `connectivity=FAIL` su priezastimi 'X never rendered, so connectivity was never measured'.
- **Rezultatas:** `front_swerve_module` -- anksciau `connectivity=PASS` ir tik bendras 'FAIL', dabar: `CHECK_RESULT render=FAIL`, `'  - no STL produced for: parts/a_arm.scad'`, `CHECK_RESULT connectivity=FAIL`.
- **Pamoka:** 'nepaleista patikra' turi daugiau formu nei man atrode. Fiksavau SKIP'us, bet nerenderinantis failas buvo trecia forma -- ne SKIP, o **PASS**.
- **Already promoted to a rule?** Ne -- siuloma: "render'is yra kiekvienos geometrijos patikros priesalyga; jei failas nepastatytas, jo patikros negali buti PASS".
### 2026-09-12 -- 8 failai parts/ kataloge yra moduliu bibliotekos, ne dalys
- **Where:** `parts/` katalogai 5 projektuose.
- **Symptom:** po to, kai `render=FAIL` buvo pridetas (pries tai siame žurnale), jis suveikė 5 projektuose: `front_swerve_module/parts/a_arm.scad`, `rack_v2/parts/_joint_prototype_test.scad`, `rack_v2/parts/peg_joint.scad`, `rack_v4/parts/peg_joint.scad`, `rack_v4/parts/plate.scad`, `v4/v8/parts/plate_common.scad`.
- **Tikrasis dalykas:** visi 8 turi **2-5 `module` ir 0 top-level kvietimu**. Jie yra **bendros moduliu bibliotekos**, kurias `include`'ina kiti failai. Jos pagal konstrukcija nieko nesirenderina.
- **Kodel tai ne FAIL:** jei palikciau FAIL, 5 is 11 projektu turetu pastovu FAIL del failo, kuris yra **teisingas**. FAIL'as, kuris dega ant teisingo failo, yra kaip FAIL'as nustoja buti skaitomas. Tai ta pati klase kaip PREVIEW_FILE ir ertmes siandien.
- **Fix:** `openscad` pats pasako savo žodziais -- 'Current top level object is empty.' -- ir grazina non-zero, todel patikra turi buti PRIES bendra render klaida, ne po jos. Kai tas pranesimas yra IR failas turi `module`, jis praleidžiamas su priezastimi: `'SKIP: X defines module(s) but instantiates none, so it renders no geometry -- a shared library file, not a printable part. If it was meant to be printable, its top-level call is missing.'`.
- **Kodel SKIP, o ne tyla:** failas vis tiek ivardijamas paleidime. Jei jis TUREJO buti spausdinamas ir neteko top-level kvietimo, tai pamatysi kaip SKIP, o ne kaip nieka.
- **Pirma versija neveike ir tai verta užrasymo:** bibliotekos patikra is pradziu buvo ideta po `if ! openscad ...` sakos. Bet openscad grazina non-zero BUTENT siuo atveju, todel ta šaka pagaudavo pirma ir bibliotekos kodas nepasiekiamas. Reikejo perskaityti jo isvesti, ne tik exit koda. Suite: 26 passed, 0 failed.
- **Already promoted to a rule?** Ne -- siuloma: "parts/ kataloge gali buti trys failu tipai -- spausdinama dalis, perziura, bendra biblioteka; validatorius privalo atskirti, o ne spelioti".
### 2026-09-12 -- Vištos ir kiausinio problema: patikra, kuri butu sukūrusi pirma deklaracija, reikalavo deklaracijos
- **Where:** `scad-modeler/scripts/validate_scad.sh`, mechanikos blokas.
- **Symptom:** `collisions` buvo SKIP **10 is 11 projektu**. Tiksliai tuose, kuriuose butu ka rades.
- **Root cause:** visas blokas buvo uždarytas `if [ -f joints.json ] && [ -f assembly.scad ]`. Bet `check_collisions.py` turi `--expected-contacts` kaip **neprivaloma** (default=None) ir, be jo, ne tik randa nepageidaujama susidūrima -- jis **isspausdina paruosta `joints.json` stub'a**. Taigi patikra, kuri butu sukūrusi pirma deklaracija, nepasileisdavo, nes deklaracijos nebuvo. Pozicionuotam render'ui `joints.json` irgi nereikia -- tik `assembly.scad` su `layout.scad`.
- **Ir tai slėpė rimtesni dalyka.** Paleidęs `check_collisions.py` rankiniu būdu ant `server_rack_modular_v4` (17 pozicionuotu daliu), gavau **kiekvienai porai 'penetration depth 170.000 mm'** -- ta pati reikšmė visose 136 porose. Priežastis: visi 17 STL'u buvo ~12.5 MB, t.y. **kiekvienas buvo VISAS assembly**.
- **Kodel:** `rack_v4/scad/assembly.scad` 14 eiluteje turi `MODE = 1;` -- paprasta priskyrima. `SKILL.md` `§6` reikalauja `MODE = is_undef(MODE) ? \"assembly\" : MODE;`, nes tik taip `-D 'MODE=\"part\"'` veikia. Paprastas priskyrimas **perraso** kintamaji ir sunaikina `-D`. Klasikinis OpenSCAD spastas.
- **Poveikis:** `joints.json` vartai **netycia saugojo** nuo šiukšliu. Jei buciau tik nuemes vartus, `collisions` butu gave 136 prasmingai atrodanciu klaidingu susidūrimu. Klaidingi rezultatai blogiau uz jokiu rezultatu, nes atrodo kaip išvada.
- **Fix (du):** (1) `collisions` paleidziamas visada, kai yra `assembly.scad`, su `--expected-contacts` tik jei failas yra; `mechanics` liko tik dinaminis `motion_sweep.py`. (2) **Tripwire pries bet kuri checkeri:** STL dydis = 84 + 50*trikampiu, tad pozicionuota dalis, kuri yra >= 80% viso assembly dydžio, nera dalis. Ant `server_rack_modular_v4`: `'ERROR: 17 of 17 positioned part(s) are as large as the whole assembly -- assembly.scad's MODE/PART switch did not take effect... Collision checks are skipped: running them on N copies of the assembly produces N*(N-1)/2 meaningless overlaps.'`.
- **Patvirtinta ant ivairiu projektu:** `rack_v4` -- tripwire suveikia (17/17), `collisions=SKIP` + `mechanics=FAIL` su tiksliu paaiskinimu. `steering_reduction_gearbox` -- pozicionuotas render veikia, `collisions=FAIL` del tikros priezasties (truksta `derivation` lauko). Suite: 26 passed, 0 failed.
- **Pamoka:** 'patikra nepasileido' gali slepti ne tik praleista defekta, bet ir **sulauzyta kelia**. Vartai, kurie atrode kaip grynas praradimas, is tikruju izoliavo šiukšles.
- **Already promoted to a rule?** Ne -- siuloma: "pries paduodant duomenis checker'iui, patikrinti, kad jie yra TAI, ko checker'is tikisi; N vienodu kopiju nera N daliu".
### 2026-09-12 -- bbox tolerancija klydo su minkowski() filletais: 0.0214 mm laikyta defektu
- **Where:** `scad-modeler/scripts/scad_tessellation.py` + `check_dimensions.py`.
- **Symptom:** `node.stl` (v8), `post.stl`, `nas_post.stl` krito su 0.0214-0.0288 mm neatitikimais. Render'yje ir visose kitose patikrose -- tvarkingos dalys.
- **Root cause:** `bbox_error_bound()` skaičiuoja teisinga formule -- `2*r*(1 - cos(pi/n))` -- bet **neteisingais argumentais**. Ji ima **modelio** bbox dydi ir **failo** globalu `$fn`. O `minkowski()` su facetuotu rutuliu ekstenta nustato **rutulio** spindulys ir **rutulio** `$fn`: `sphere(r = fillet_post/2, $fn = 24)` su `fillet_post = 2.5`.
- **Skaiciai:** pries -- `bbox_error_bound(26)` su n=180 duoda 0.0040 mm, o floor 0.005 ji praryja; tikroji paklaida **0.0214** mm. Po -- `2 * 1.25 * (1 - cos(pi/24))` = **0.02139** mm, pries ismatuota **0.02141** mm (skirtumas -- float32 STL apvalinimas).
- **Antra klaida, rasta bandant:** pirmas fix'as ide termina i `max(bbox, mink, floor)` -- ir dalis **vis tiek krito**, nes `diff 0.0214 > tol 0.0214`. Priezastis: `max()` **numeta** float32 saugojimo rezerva, kai teseliacijos riba ja virsija. Paklaidos **dedasi**, ne imamas maksimumas. Galutinis: `max(bbox_error_bound, floor) + mink`.
- **Kodel atskiras narys, o ne didesnis floor:** pakelti floor iki 0.03 mm butu paliepusi ir dalims BE `minkowski()` -- o tos buvo validuotos su 0.005 mm ir tikrina 0.45-1.4 mm tikrus neatitikimus. Dabar `mink = 0` tokioms dalims ir tolerancija nepasikeitusi.
- **Patikrinta, kad neatsilaisvino:** `node` -- PASS su tol 0.0264; `post.stl` X -- vis tiek FAIL su 29.98 mm. Naujas fixture `dimensions_minkowski_sphere_pass` + senasis `dimensions_bbox_fail` -- abu praeina. Suite: **27 passed, 0 failed**.
- **Atvirumas:** `minkowski_sphere_deficit()` sprendžia tik tai, ka gali: `sphere(r = <skaicius>)`, `sphere(r = <ident>/<skaicius>)` ir `sphere(r = <ident>)`. Nespresiamo spindulio atveju terminas **praleidziamas**, ne spėjamas -- išgalvotas spindulys tyliai praplestu tolerancija, o butent to visas modulis ir saugosi.
- **Already promoted to a rule?** Ne -- siuloma: "teseliacijos paklaida turi buti skaičiuojama to objekto, kuris NUSTATO ekstenta, o ne to, kuri matuoji".
### 2026-09-12 -- 8 checker'iai neturejo nė vieno testo; rasdamas juos radau vakuumini PASS
- **Where:** `scad-modeler/tests/fixtures/` -- 27 fixture'ai dengė 8 is 16 checker'iu.
- **Be testu buvo:** `check_assumptions`, `check_dependencies`, `check_intake`, `check_plan`, `check_rules`, `check_service_envelope`, `doctor`, `scad_tessellation`. `scad_tessellation` buvo **ka tik pakeistas** siandien (minkowski narys) ir neturejo nė vieno testo.
- **Vakuuminis PASS, rastas rasydamas `check_rules` fixture'a:** `check_rules.py` tustame projekto kataloge grazino `exit 0` ir isspausdino `[PASS  ] R-04: Connectivity: every printed part renders as one connected body` -- projektui, kuriame nera nė vienos dalies.
- **Root cause:** `rules_manifest.yaml` R-04 turejo `applies: \"always\"` ir `success_pattern: \"CHECK_RESULT connectivity=(PASS|SKIP)\"`. Be daliu `validate_scad.sh` teisingai isveda `connectivity=SKIP` -- bet SKIP'as buvo skaitomas kaip sekme. Taisykle, kurios negalima ivykdyti, yra **N/A**, ne PASS.
- **Kodel tai blogiau uz FAIL'a:** FAIL'as sako 'nepavyko'. Vakuuminis PASS sako 'patikrinau' apie darba, kuris neivyko. Tai ta pati klase kaip klaidingas PASS su nerenderinancia dalimi, rastas siandien ryte.
- **Fix:** naujas `applies` detektorius `glob_exists:<pattern>` -- `file_exists` negali isreiksti 'yra ka tikrinti'. R-04 dabar `glob_exists:parts/*.scad,assembly.scad` su `success_pattern: \"CHECK_RESULT connectivity=PASS\"` (be SKIP). Patikrinta: tustas projektas -- `R-04 N/A`; `rack_v4` -- `R-04 FAIL` (jis tikrai turi atskiru kunu).
- **8 fixture'ai, visi praeina.** Vertingiausi ne 'laimingi keliai', o kontraktai: `check_intake` grazina **2** (manifesto nera) vs **3** (specas blogas) -- tas skirtumas nores validate_scad.sh kvieciantysis; `check_rules` -- **3** (taisyklė neivykdyta) vs **4** (checker'is paleistas blogai); `doctor` -- 0/2/3. `tessellation_minkowski_sphere` fiksuoja 0.021388 = 2*1.25*(1-cos(pi/24)), t.y. tikra ismatuota paklaida, ne isgalvota.
- **Suite:** 27 -> **35 passed, 0 failed**.
- **Already promoted to a rule?** Ne -- siuloma: "tureti testa kiekvienam checker'iui; o taisykle be ivykdomo vartu yra N/A, niekada PASS".
### 2026-09-12 -- SKIP be instrukcijos: 8-10 patikru neivyksta ir niekas nesako, ka daryti
- **Where:** `scad-modeler/scripts/validate_scad.sh` -- `attachment`, `bore_reachability`, `intake`, `printability` SKIP pranesimai.
- **Symptom:** `attachment` buvo SKIP **11/11** projektu, `intake` 11/11, `bore_reachability` 10/11. Pranesimas sakydavo tik ko truksta ('no bores.json in project root'), ne ka daryti.
- **Root cause:** sablonas `templates/bores.json` ir `templates/attachments.json` **neegzistavo isvis** -- buvo tik `joints.json`. Patikros buvo parašytos ir istestuotos, bet niekas negalejo žinoti, kaip paruosti jų įvesti.
- **Fix (du):** (1) abu sablonai sukurti ir iregistruoti `templates/README.md` su laukų paaiskinimais. (2) SKIP pranesimai dabar nurodo konkretu sablona ir pasekme: `'SKIP: no bores.json -- copy templates/bores.json to the project root and fill it in; until then no bore is checked for reachability'`.
- **Ir skaiciai isvestyje, ne tik log'e:** paleidimo pabaigoje dabar spausdinama `'COVERAGE: N passed, N failed, N skipped (N checks reported).'` ir, jei SKIP > 0, `'  N check(s) did NOT run -- each SKIP above names what it needs. A green run with a large SKIP count has verified less than it looks.'`.
- **Kodel tai svarbu:** `'All validations passed.'` ir `'COVERAGE: 8 passed, 0 failed, 10 skipped'` yra **skirtingi teiginiai**, ir dabar jie visada spausdinami kartu. Anksciau zalią paleidima galejai perskaityti kaip pilną patikra.
- **Technine detale:** skaiciuojama `log_check()` viduje -- tai vienintelė vieta, pro kurią eina kiekviena patikra. Alternatyva buvo keisti ~30 `echo` vietų ir rinkti masyva; vienas choke point yra ir maziau kodo, ir negali buti praleistas.
- **Patikrinta:** `server_rack_modular` -- '10 passed, 0 failed, 8 skipped'; `front_swerve_module` -- '8 passed, 0 failed, 10 skipped'. Suite: 35 passed, 0 failed.
- **Already promoted to a rule?** Ne -- siuloma: "zalias paleidimas su dideliu SKIP skaiciumi nera pilna patikra; abu skaiciai spausdinami kartu".
### 2026-09-12 -- SAKNIS: skill'o darbo eiga niekada neliepe parasyti deklaraciju
- **Where:** `scad-modeler/SKILL.md` -- zingsniai §0-§8.
- **Symptom:** `bores.json` ir `attachments.json` turejo **0 is 11** projektu. `attachment` SKIP 11/11, `bore_reachability` SKIP 10/11, sudėjus 95 SKIP is 198 patikru-paleidimu.
- **Root cause:** deklaracijos SKILL.md minimos **tik checker'iu lenteleje** -- kaip 'ko reikia patikrai'. Nė viename darbo eigos zingsnyje nera parasyti 'sukurk si faila'. Agentas, atidžiai skaitantis nuo §0 iki §8, niekada nesuzino, kad ju reikia.
- **Ir tai prieštaravimas skill'o savo tekste:** §0.6 126 eilute sako, kad §7 'closes two of the three with a real automated check (`check_bore_reachability.py`, `check_subfeature_overlap.py`)'. Bet tos patikros neturejo įvesties -- tad **niekada nebuvo paleistos ant tikro darbo**. Teiginys buvo neteisingas nuo parasymo dienos.
- **Fix:** §0.6 jau reikalauja būtent tu ziniu proza ('Insertion path', 'Shared-part neighbors', 'Retention', 'Purchased-part fit'). Prideta lentelė, kuri kiekviena atsakyma susieja su jo masinine forma: insertion path -> `bores.json`; neighbors -> `fusions.json` + `EXPECTED_BODIES`; retention -> `attachments.json`; purchased-part fit -> `joints.json`. Jokio naujo zingsnio -- tie patys atsakymai, uzrasyti taip, kad juos skaitytu patikra.
- **Pamoka:** 95 SKIP nebuvo vartotojo problema ir ne checker'iu problema. Buvo **darbo eigos** problema: patikros reikalavo įvesties, kurios niekas nepraše.
- **Nepakanka:** prideti lentele yra butina, ne pakankama. Reikia patikrinti, ar agentas ja vadovaujasi -- t.y. ar projektai po sito turi deklaracijas.
- **Already promoted to a rule?** Ne -- siuloma: "jei patikra reikalauja įvesties, darbo eiga privalo ta įvesti reikalauti; kitaip patikra egzistuoja tik popieriuje".
### 2026-09-12 -- Degeneruota geometrija: 28 nanometru briauna sugadina spinduliu matavimus
- **Where:** `scad-modeler/scripts/check_connectivity.py` -- pridetas degeneruotos geometrijos pranešimas.
- **Kaip rasta:** `check_printability.py` krito 4/4 realiu daliu. Pries taisydamas slenkscius patikrinau, ar jo skaiciai gali buti tikri. Ant svaraus modelio jis TIKSLUS: vientisas 30 mm kubas -> min 30.000 mm; tusciaviduris su tiksliai 3 mm sienom -> min 3.000 mm.
- **Tikroji priezastis:** `frame_module.stl` -- watertight, 1 sujungtas kunas, visos turio patikros svaros, ir trumpiausia briauna 0.000028 mm (28 nanometrai), 9 briaunos < 1 mikronas. Ant tokio sliverio spinduliu matavimas nuskaito 0.014 mm siena -- 30x maziau uz bet ka, ka modelis deklaruoja.
- **Kontroles atvejis:** `base.stl` -- trumpiausia briauna 0.296 mm, nuskaitoma siena 0.252 mm. Sutampa -- ten tikra geometrija, ir `check_printability.py` teisus.
- **Fix:** `check_connectivity.py` dabar praneša DEGENERATE GEOMETRY su trumpiausia briauna ir skaiciumi, ir pasako, KURIUOS matavimus tai gadina (printability wall/overhang) bei kad sliceris taip pat gali susipainioti. Tai ne verdiktas -- dalis vis tiek yra vienas kunas, ir PASS lieka.
- **Kodel ne naujas checkeris:** tai mesh vientisumo faktas, o `check_connectivity.py` jau skaido komponentus ir jau turi mesh rankoje. 17-as checkeris butu dar vienas failas, vienas SKIPas ir vienas fixture tam paciam dalykui.
- **Naujas fixture:** `connectivity_degenerate_edge_note` -- tangentinis cilindru boolean su 0.0005 mm poslinkiu duoda 250 nm briauna. Tikrina tris dalykus: pranešimas yra, jis cituoja briauna, ir SVARUS mesh lieka tylus (kitaip pranešimas tampa triukšmu ir nustoja buti skaitomas). Suite: 35 -> 36 passed, 0 failed.
- **Ka tai reiskia printability:** jis ne sugedes -- jis teisingas ant svaraus mesho ir bevertis ant sugadinto. Kol modeliai turi sliveriu, jo thin-wall verdiktas negali buti vartais. Irasyta i NEXT.md.
- **Already promoted to a rule?** Ne -- siuloma: pries tikint spinduliu matavimu, patikrink, ar mesh neturi sub-mikroniniu briaunu.
### 2026-09-12 -- check_subfeature_overlap buvo parasytas, istestuotas ir NIEKADA nepaleistas
- **Where:** `scad-modeler/templates/part_template.scad` + `validate_scad.sh`.
- **Symptom:** `subfeature_overlap` SKIP **11/11** projektu. `references/validation.md` ji dare 'manual, needs solo sub-feature STLs' -- t.y. pripazino, kad patikra egzistuoja, bet niekas jos nepaleidzia.
- **Root cause:** patikra reikalauja SOLO sub-moduliu STL (kiekvienas sub-feature atskirai, pries `union()`). Nė vienas projektas to negamina, ir **niekas skill'e to negamino** -- nera `MODE`/`PART` analogo sub-feature'ams. Padavus vientisas dalis jis pranesa beprasmius persidengimus (ismatuota: 196 779 mm3 tarp dvieju daliu, kurios tik bendrai turi koordinačiu pradzia).
- **Kodel tai buvo brangu:** tai vienintelė patikra, kuri gaudo persidengima **vienos dalies viduje**. `union()` dvieju persidengiančiu kunu yra vis dar vienas validus, watertight, vieno kuno apvalkalas -- tad `check_connectivity` ir `dimensions` lieka svarus. Tikras incidentas (INCIDENTS.md 2026-08-19): bearing tower persidengė su motor cradle **419 mm3** vienos dalies viduje ir praejo kelis 'all green' ratus.
- **Fix:** (1) `templates/part_template.scad` gauna `// SUBFEATURES: a, b, c` eilute, po viena moduli kiekvienam vardui, ir **apsaugota** `SUBFEATURE` switch (tokio pat kaip `assembly.scad` `MODE`/`PART` -- paprastas priskyrimas sunaikintu `-D`). (2) `validate_scad.sh` nuskaito eilute, renderina kiekviena sub-feature SOLO ir paleidzia patikra.
- **Atskirai KIEKVIENAI DALIAI, ne globaliai:** sub-feature'ai gyvena dalies LOKALIOSE koordinatese. Paleidus vienam rinkiniui per kelias dalis, lyginami du nesusije koordinačiu pradžiai -- butent tas klaidingas rezultatas, kuri ismatavau pries tai.
- **Patikrinta:** `// SUBFEATURES: tower_main, motor_cradle` su tyčiniu persidengimu -> `'UNINTENDED SUB-FEATURE OVERLAP: demo__tower_main.stl <-> demo__motor_cradle.stl, 180.00 mm3'` ir `CHECK_RESULT subfeature_overlap=FAIL`. Be deklaracijos -> SKIP **su priezastimi stdout'e** (ne tik log'e), nurodančia `templates/part_template.scad`.
- **Naujas fixture:** `subfeature_overlap_wired` -- paleidžia `validate_scad.sh`, o ne checkeri, nes truko butent sujungimo, ne patikros. Tikrina abi puses ir kad eilute butu **lygiai viena** (radau ir pasalinai dubli, likusi is seno 'ne vartai' bloko). Suite: 36 -> **37 passed, 0 failed**. Realus projektas vis dar 18 patikru.
- **Already promoted to a rule?** Ne -- siuloma: "patikra, kuriai reikia įvesties, kurią turi gaminti pats skill'as, privalo ta įvesti gaminti -- kitaip ji yra dekoracija".
### 2026-09-12 -- End-to-end testas: ar defektas praeina per VISA grandine, ne per checkeri atskirai
- **Kodel atsirado:** 'checker'is veikia' ir 'skill'as veikia' yra **skirtingi teiginiai**. Checker'is gali buti tobulas ir vis tiek nebuti iskviestas -- butent ta spraga siandien pagimde du tikrus bug'us: `check_subfeature_overlap.py` buvo parašytas, istestuotas ir **niekada nepaleistas**, o `check_dimensions.py` veike kiekviename projekte **neisvesdamas nieko, ka kas nors matytu**.
- **Naujas fixture `pipeline_catches_three_defects`:** trys tikri defektai, kiekvienas su savo incidentu INCIDENTS.md, paleisti per `validate_scad.sh --all`: (1) dalis, kuri renderinasi kaip du atskiri kunai (2026-08-19, koju radiuso fix'as); (2) dalis, kuri atrodo gerai, bet neteisingo dydzio; (3) du sub-feature'ai, persidengiantys **vienos dalies `union()` viduje** (419 mm3 bearing tower vs motor cradle).
- **Tikrina ne vartu koda, o tai, ka grandine PRANESA** -- ir tris `CHECK_RESULT` verdiktus, ne tik detaliu eilutes. Detali eilute be verdikto ir yra ta tyli spraga, del kurios sis fixture egzistuoja.
- **Rezultatas:** `connectivity=FAIL`, `dimensions=FAIL`, `subfeature_overlap=FAIL` -- visi trys pamatyti, ir `COVERAGE: 6 passed, 3 failed, 8 skipped`.
- **Papildomai patikrinta:** ar `rules_manifest.yaml` `success_pattern` šablonai **skiria** pass nuo fail. Visi 6 sutampa tik tada, kai patikra PASS arba SKIP, ir skaiciai sutampa tiksliai (pvz. R-04: 5/11 sutapimu, 5 PASS).
- **Ir sablonai:** taisyklingai užpildytas `plan.md` -> `exit 0` ('2 options listed; decision confirmed'); `service_envelope.md` su visais 9 laukais -> `exit 0`. Neužpildyti -> `exit 1`. Veikia kaip parašyta.
- **Suite:** 37 -> **38 passed, 0 failed**.
- **Ko tai NEIRODO:** kad skill'as **pagerina modelio sprendimus**. Tai rodo tik tai, kad grandine veikia ir nemeluoja. 'Ar geriau' klausimas lieka atviras (golden set'as 100%/100%).
### 2026-09-12 -- Nepriklausomas recenzentas: 10 radiniu, visi tikri, visi pataisyti
- **Kaip gauta:** paleistas **priesiskas** subagentas, kurio vienintelė užduotis buvo **sugriauti** skill'o teiginius. Ne patvirtinti -- paneigti. Jis gavo sąrašą konkrečiu klasiu ir įpareigojimą tikrinti **vykdant**, ne skaitant.
- **Rezultatas: 10 radiniu, visi patvirtinti matavimu.** Nė vienas nebuvo stilistikos pastaba.

- **F1 -- tripwire klaidingas teigiamas (PATAISYTA PRIES recenzija).** Skill'o paties pavyzdys `examples/gear_reduction` krito: `mechanics=FAIL`, 'spur.stl 1786110 B vs assembly 2157216 B = 0.828 >= 0.8'. 66-dantis krumpliaratis **teisėtai** sudaro 83% dvieju daliu assembly. Failo dydis netinka -- pakeista i **bounding box**. Dabar `exit 0`, `collisions=PASS`, `mechanics=PASS`.
- **F2 -- SKILL.md sake, kad `check_subfeature_overlap.py` NEPRIJUNGTAS.** Jis prijungtas (tai padariau šiandien), ir `references/validation.md` tai sako, ir fixture tai fiksuoja. Dokumentai prieštaravo vienas kitam; SKILL.md buvo neteisus.
- **F3 -- `fusions.json`: šablono NEBUVO, ir vartai jo niekada neskaitė.** `validate_scad.sh` nekviecia `--exempt`, tad deklaracija buvo no-op vieninteliame automatiniame kelyje. Sukurtas šablonas, `--exempt fusions.json` perduodamas. Patikrinta: be deklaracijos FAIL 640 mm3, su ja PASS.
- **F4 -- vienos dalies rezimas nespausdino nei `CHECK_RESULT`, nei `COVERAGE`.** `validate_scad.sh spur` grazindavo 'All validations passed' be nė vieno geometrijos verdikto. Dabar spausdina `connectivity`, `dimensions`, `features` ir `COVERAGE`.
- **F5 -- `intake=SKIP` priezastis melavo.** Sakydavo 'no design_manifest.json' net kai failas YRA. Dabar tikrina.
- **F6 -- VAKUUMINIS PASS: R-09.** `joints.json` deklaruoja judesi, `assembly.scad` nera, tad `motion_sweep.py` niekada nepaleidziamas -- o `check_rules.py` grazino **exit 0** ir '[PASS] R-09'. Ta pati klase, kuria R-04 buvo pataisyta ryte. Du fix'ai: `success_pattern: CHECK_RESULT mechanics=PASS` (be SKIP) ir teisinga SKIP priezastis.
- **F7 -- SKILL.md dokumentavo 0/2/3/4 `validate_scad.sh`, kuris grazina tik 0/1.** Pataisyta.
- **F8 -- `validation.md`: '2 = degraded, tik `check_collisions`'. Netiesa -- 2 grazina ir `check_intake`, `check_subfeature_overlap`, `check_printability`, `motion_sweep`, `doctor`. Pataisyta, ir tas pats failas sau prieštaravo 349 eiluteje.
- **F9 -- BLOGIAUSIAS: sekmė ant nepatikrinto projekto.** `templates/README.md` siunte failus i `scad/`, o vartai globina `parts/*.scad` nuo esamo katalogo. Rezultatas: 'no files found under parts/*.scad' -> **'All validations passed.', exit 0**, nulis renderintu daliu. Pataisyta abipus: README sako 'project root', o tuščias paleidimas dabar **krenta** su paaiškinimu ir nuoroda i `scad/parts/`.
- **F10 -- `templates/plan.md` sakė 'uncomment' `PLAN_EXEMPT` eilute, o `check_plan.py` priima tik `<!-- -->` forma.** Pataisyta; patikrinta, kad abi formos elgiasi kaip parašyta.

- **Ka recenzentas patvirtino kaip TEISINGA:** visi 6 `success_pattern` sutampa su realiai spausdinamomis eilutėmis (patikrino 44 galimas eilutes); '18 patikru' ir '8-10 SKIP' tikslus; `check_plan`/`motion_sweep`/`doctor`/`check_rules` exit kodai teisingi; R-04 N/A (ne PASS) veikia.
- **Dvi naujos fixtures:** `rules_no_vacuous_pass` ir `pipeline_empty_run_fails`. Suite: 38 -> **40 passed, 0 failed**.
- **Pamoka, kuri verte viska:** 'patikrinta' ir 'teisinga' nera tas pats. Radau ir pataisiau 10 dalyku, kuriu **pats neieškojau**, nes tikėjau savo pačio tekstu. Priesiškas recenzentas su įpareigojimu matuoti rado juos per viena paleidima.
### 2026-09-12 -- Tylus false negative mano pačiame tripwire: inline parseris krito i `|| echo 0`
- **Where:** `scad-modeler/scripts/validate_scad.sh` -- pozicionuotu daliu patikra; naujas `scripts/stl_extent.py`.
- **Kaip rasta:** po F1 pataisymo (failo dydis -> bounding box) perbėgau 11 projektu ir pastebejau **prieštaravimą**: `collisions` dabar krito 5 projektuose, o `server_rack_modular_v4` vel rode **136 poras su identišku 'penetration depth 170.000 mm'** -- 17 kopiju parašas.
- **Tikroji priezastis, dvi dalys:** (1) inline `python3 -c` spejo, kad STL yra **binarinis** (4 baitu trikampiu skaicius 80 offsete). OpenSCAD pagal nutylejima rašo **ASCII** ('solid OpenSCAD_Model'), tad parseris nuskaitė ASCII kaip skaiciu (943009847) ir krito. (2) Kvietimas buvo apvyniotas `2>/dev/null || echo 0` -- tad klaida virto **tyliu 'nieko itartino'**. Tripwire nustojo aptikti bet ka ir niekas nepranešė.
- **Kodel tai ta pati klase, kuria taisau visa diena:** tyliai praryta klaida, virtusi sekme. Tik si karta -- mano pačio kode, ir būtent tame pataisyme, kuris šalino klaidinga teigiama.
- **Fix:** atskiras `scripts/stl_extent.py` su testu. Skaito ABIU formatu (ASCII ir binary), o klaidos atveju **grazina ne-nuli** ir sako, ko nepavyko perskaityti -- jokio `|| echo 0`. Vartai dabar: jei matuoti nepavyksta, `collisions=SKIP` su priezastimi, o ne spėjimas.
- **Patikrinta abiem kryptim:** `server_rack_modular_v4` -- **17/17 pagauta** (`'have exactly the assembly's bounding box'`); `examples/gear_reduction` -- `collisions=PASS`, `mechanics=PASS`, nesuveikia.
- **Naujas fixture `stl_extent_both_formats`:** renderina ASCII, konvertuoja i binary per trimesh, ir reikalauja, kad **abi** duotu 10x20x30; be to, šiukšliu failas privalo grazinti klaida, o ne skaiciu.
- **Išmokta:** kai šalini klaidinga teigiama, patikrink, ar naujasis kodas dar **pagauna tikra atvejį**. Aš to nepadariau iškart -- padariau tik todėl, kad perbėgau visus projektus ir pastebejau, kad skaiciai nesueina.
- **Suite:** 40 -> **41 passed, 0 failed**.
### 2026-09-12 -- Penki verdiktai vietoj dvieju: printability buvo PAVADINTAS SKIP, nors IVYKO
- **Where:** `scad-modeler/scripts/validate_scad.sh`, `check_rules.py`.
- **Kaip rasta:** priešiškas tarpdisciplininis recenzentas, paprašytas patikrinti, ar kitos sritys jau išsprendė šias problemas.
- **Kas buvo neteisinga:** `printability` suveikė **4/4** realiose dalyse ir kiekvienoje ką nors rado. Aš jį pavadinau `SKIP`, o SKIP reiškia 'nepaleista / negaliu nustatyti'. Tai **neteisingas teiginys apie įrankį** ir jis paslepia radinį nuo būsimo prižiūrėtojo.
- **Standartas, kurio nesilaikiau:** `SKIP` suliejo tris skirtingus dalykus -- 'netaikoma', 'paleista, bet negalėjau išmatuoti' ir 'paleista, bet ne vartai'. Jie turi tris skirtingus veiksmus. SARIF `result.kind` skiria `notApplicable` nuo `open`; TTCN-3 `verdicttype` turi penkias reikšmes (`inconc` ir `none` yra verdiktai, ne anotacijos); pytest tuščiam paleidimui grąžina **6**, ne 0.
- **Klaidingo žymėjimo kaina:** Google Tricorder patirtis -- jie **pašalino** vartotojo lygio derinimą, sutaisė šaknis ir **IŠJUNGĖ** HTML linterį visiškai. Jų užrašyta pamoka: slopinimas 'sukėlė paslėptų bug'ų'.
- **Fix, penki verdiktai:** `PASS` / `FAIL` / `SKIP` (netaikoma) / `INCONCLUSIVE` (paleista, negalėjau nustatyti) / `ADVISORY` (paleista, ne vartai).
  - `printability` -> **ADVISORY** (jis įvyko; FP dalis 4/4 = ~100 %, tai **virš** literatūros >50 % 'neverta integruoti' ribos, tad jis praneša, bet neblokuoja)
  - trys `collisions` atvejai ir `mechanics` be `assembly.scad` -> **INCONCLUSIVE**
  - `check_rules.py` -> naujas `[INCONC]` verdiktas; jis **ne** `FAIL` (FAIL = taisyk modelį, INCONC = taisyk checker'į ar jo įvestį) ir paleidimas lieka ne-žalias
  - COVERAGE eilutė: `'COVERAGE: 6 passed, 3 failed, 7 not-applicable, 1 inconclusive, 1 advisory (18 checks reported).'`
- **Kodėl INCONCLUSIVE niekada neturi virsti FAIL:** tai būtų trijų reikšmių problemos suliejimas į dvi -- tą patį, ką recenzentas jau buvo radęs P2 sprendime. Netinkama patikra, pranešanti FAIL, yra **klaidingas teigiamas**.
- **Patikrinta:** `server_rack_modular_v4` -- `collisions=INCONCLUSIVE` (MODE sulaužytas), `mechanics=FAIL` (sutarties pažeidimas), `printability=ADVISORY`. Suite: **41 passed, 0 failed**.
- **Kas liko nepadaryta iš recenzento sąrašo:** (a) pervasiveness taisyklė -- kurie SKIP'ai užteršia verdiktą (ISA 705); (b) cover-property analogas -- ar kiekvienos taisyklės antecedentas kada nors įvyko (6 niekada); (c) neigiamas įrodymas -- ar patikra apskritai gali nepavykti.
### 2026-09-12 -- Cover ataskaita, neigiami irodymai ir pervasiveness (isleista is tyrimo)
- **Where:** `check_rules.py`, `tests/fixtures/`.
- **Trys dalykai, kuriuos radau tik tyrimo deka, ir kurie buvo nepadaryti:**

- **1. COVER ataskaita (formalios verifikacijos 'cover property' analogas).** Formalioje verifikacijoje kiekvienas `assert property` privalo tureti suporuota `cover property` ant savo antecedento, ir cover **turi įvykti**: sėkmingas assertion, kurio antecedentas niekada nesuveikė, yra **verifikacijos spraga, ne sekme**. `check_rules.py` dabar spausdina `'COVER: 4 rule(s) exercised, 8 whose antecedent never fired: R-01, R-02, R-06, R-09, R-11, R-12, R-14, R-18'` ir įvardija jas. Anksčiau kiekvienas paleidimas garbingai sakydavo 'N/A', o **sankaupa buvo nematoma**: 6 is 18 taisykliu nebuvo įsijungusios nė viename is 11 projektu.
- **2. Neigiami įrodymai.** Formalioje pusėje assertion, kuri **negali** nepavykti, yra vakuumine antru budu (`vacuous` įrankio klases: `constant-assertion`, `no-assertions`). Auditas parodė: **15 is 17 checker'iu turi fixture, kuriame krenta; 2 neturėjo** -- `check_dependencies` (turėjo tik teigiama: pakeitimu medis veikia) ir `doctor` (tik teigiama: praneša apie mašina). Abu sukurti: `dependencies_reaches_part` tikrina, kad pakeitimas **pasiekia** dali (C2, ne C1) ir ja įvardija; `doctor_reports_degraded` sulaužo priklausomybe per `PYTHONPATH` ir reikalauja, kad `doctor` tai **pasakytu ir įvardytu pasekme**, o ne grazintu sveikatos pažyma.
- **3. Pervasiveness (ISA 705).** Audito standartas: kai įrodymu gauti nepavyksta, o poveikis gali buti **reikšmingas IR visapusiškas**, auditorius **atsisako nuomones**, o ne duoda švaria. `check_rules.py` dabar: jei daugiau nei puse automatiniu taisykliu neįsijungė, spausdina `PERVASIVE` ir OK eilutė neša skaičiu (`'only 4 of 12 automated rules had their antecedent fire'`).
- **Radau ir savo klaida:** pirma versija įdėjo `PERVASIVE` bloka **po** `if any_auto_fail: return EXIT_FAIL`, tad krentančiame projekte jis **niekada nepasireikšdavo** -- t.y. butent ten, kur svarbiausia. Perkelta auksčiau.
- **Naujas fixture `rules_cover_and_pervasive`:** reikalauja, kad COVER butu, kad jis **įvardytu** taisykles (ne tik skaičiuotu), ir kad PERVASIVE atsirastu, o jei paleidimas žalias -- OK eilutė neša skaičiu.
- **Suite:** 43 -> **44 passed, 0 failed**.
- **Kas dar liko is recenzento sąrašo:** golden set'o mutation matavimas ir kainos permatavimas.
### 2026-09-12 -- INCONCLUSIVE per platus: tuscias motion masyvas duoda klaidinga teigiama
- **Where:** `validate_scad.sh`, mechanikos blokas.
- **Kaip rasta:** agentas, dirbdamas NESUSIJUSIA uzduoti (detalės atkurimas pagal spec'a), savo ataskaitoje parase: *"validate_scad.sh reports mechanics=INCONCLUSIVE purely because joints.json exists with an empty motion array -- a false positive of the bundle, not a defect here"*. **Radė agentas, ne suite.**
- **Kas buvo neteisinga:** INCONCLUSIVE sakaka buvo prideta 2026-09-12 ir tikrino **tik ar failas egzistuoja** (`[ -f joints.json ] && [ ! -f assembly.scad ]`). Bet projektas gali tureti `joints.json` su **TUSCIU** motion masyvu -- taip jis dokumentuoja, kad judesio nera. Tada patikra **netaikoma**, ir verdiktas turi buti SKIP.
- **Kaina:** kiekvienas toks projektas gaudavo INCONCLUSIVE, o INCONCLUSIVE paleidima padaro ne-zalia. Tai **klaidingas teigiamas, verciantis ignore'inti signalą** -- ka tik uzfiksavau kaip atskira problema (Google Tricorder: <10 % FP patariamajam, 0 blokuojanciam).
- **Antras bug'as tame paciame bloke:** `echo "CHECK_RESULT mechanics=SKIP"` buvo spausdinamas **visada** pries `if`, tad INCONCLUSIVE atveju išeidavo ABU verdiktai.
- **Fix:** motion deklaracija tikrinama atskirai (python inline, tas pats pattern kaip `has_motion`); SKIP spausdinamas tik `else` sakoje.
- **Patikrinta:** to paties agento projekte -- `mechanics=SKIP`, `COVERAGE: 12 passed, 0 failed, 4 not-applicable, 0 inconclusive`.
- **Naujas fixture `mechanics_empty_motion_is_skip`:** reikalauja SKIP, draudzia INCONCLUSIVE, ir tikrina, kad COVERAGE skaiciuoja kaip not-applicable. Suite: 44 -> **45 passed**.