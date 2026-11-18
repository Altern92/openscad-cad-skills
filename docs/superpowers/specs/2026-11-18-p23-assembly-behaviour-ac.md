# P23 Surinkimo elgsena: laikosi / juda / stovi (AC, 2026-11-18)

Kilmė: INC-2026-11-18-01. Priekinė ašis (`esp32_rc_modelis/mechanical/front_axle_v4`) praėjo visus vartus,
o svirtys kabojo ore: šarnyrų antgaliai (pirktos dalys) nebuvo sumodeliuoti, `joints.json`/`attachments.json`
deklaravo jungtis, kurių geometrijoje nebuvo. Keturgrandės pakabos su vairu `motion_sweep.py` neišreiškia,
todėl projektas rašė savo `check_sweep.py`.

Vartotojas 2026-11-18: „Daryk viska pagal savo siulymus, kad geriau veiktu tai ir ateityje nesikartotu“
(patvirtina siūlymą: vartai 1–3, be fizikos simuliacijos).

Tier: feature (naujas checker'is + vartai + taisyklė). Architektūra: vienas skriptas `check_behavior.py`,
deklaracija `behavior.json` projekto šaknyje, kviečiamas iš `validate_scad.sh` (`CHECK_RESULT behavior=`).

## behavior.json

```json
{"scad": "assembly.scad",
 "poses": {"BUMP": [-10, 0, 15], "STEER": [-30, 0, 35]},
 "bodies": {"frame": {"render": [{"MODE": "part", "PART": "frame"}], "static": true, "mass_g": 120},
            "cup_l": {"render": [{"MODE": "vit", "VIT": "cup_la"}], "density": 7.8}},
 "joints": [{"a": "cup_l", "b": "lower_arm", "max_gap": 0.3, "why": "screwed into the arm"}],
 "clearance": {"default": 0.0, "pairs": [{"a": "wheel", "b": "frame", "min": 1.5}]},
 "ground": {"z": 0, "bodies": ["tire"], "tol": 0.5}}
```

## AC

**Laikosi (holds)**
- AC-1: Given a body that is in no `joints` entry, when the check runs, then FAIL names it ("not held by anything").
- AC-2: Given a joint whose two bodies are farther apart than its `max_gap` at any pose, then FAIL names the pair, the gap and the pose (the front-axle case: arm without its rod end).
- AC-3: Given a joint with `max_gap` > 1.0 mm, then FAIL "model the purchased part that bridges it" (a gap is not a joint; the cap is not configurable).
- AC-4: Given bodies whose joint graph splits into 2+ groups (or, with `ground`, a group not reaching a ground body), then FAIL lists the detached group.
- AC-5: Given a part STL with an enclosed cavity, when `check_connectivity.py` runs, then FAIL unless the part declares `// EXPECTED_CAVITIES: N` with the same count (was a note only).

**Juda (moves)**
- AC-6: Given `poses`, the check renders every non-static body at every point of the pose grid (static bodies once) and evaluates AC-2, AC-7, AC-8 at each pose; output names the number of poses and pairs.
- AC-7: Given two non-joint bodies that interpenetrate (> 0.01 mm³ intersection) at any pose, then FAIL with the volume and pose.
- AC-8: Given a `clearance.pairs` entry, when the pair's minimum distance at any pose is below `min`, then FAIL with distance and pose; the worst distance per declared pair is always printed.

**Stovi (stands)** — only when `ground` is declared
- AC-9: Given a ground body whose lowest point is more than `tol` above or below `ground.z` at any pose, then FAIL.
- AC-10: Given the mass centre (`mass_g`, else volume × `density` g/cm³, default 1.0 with a NOTE) whose XY lies outside the convex hull of ground-contact points, then FAIL with the margin; inside, PASS prints the margin.

**Wiring and failure paths**
- AC-11: `validate_scad.sh --all` prints `CHECK_RESULT behavior=PASS|FAIL` when `behavior.json` exists, `SKIP` with a how-to line when it does not; a render error is FAIL, never PASS; malformed JSON/unknown body name exits 4 → FAIL.
- AC-12: Rule R-24 in `rules_manifest.yaml`: applies when `joints.json` exists, success = `CHECK_RESULT behavior=PASS` (an assembly that declares joints must prove them geometrically).
- AC-13: A mutant (`check_behavior` replaced by `exit 0`) makes a fixture fail (`tests/mutants.tsv`).
- AC-14: Fixtures: floating arm FAIL / bridged PASS; collision across a pose sweep FAIL; COM outside support FAIL; gap cap FAIL; cavity undeclared FAIL / declared PASS.
- AC-15: Applied to `front_axle_v4` and `vehicle_v4`: PASS on the current models; removing the rod-end vitamins from `behavior.json` reproduces INC-2026-11-18-01 as FAIL.
- AC-16: Docs: SKILL.md §0.6 table + §7, `references/validation.md`, `templates/behavior.json`; `skill_docs_match_code` stays green; suite green in dev and installed.

Not in scope: physics simulation (forces, friction), strength.
