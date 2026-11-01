# P5: approved acceptance criteria the agent cannot weaken (AC)

Date: 2026-11-01. Tier: feature (new script, validate_scad.sh gate, stop-hook rule). Approved in advance
("tesk implementacija ir imkis visu savo rekomenduojamu sprendimu").
Origin: NEXT.md P5 + the Rust-proposal note: `EXPECTED_*` lines are written by the same agent in the same
`.scad`, so a failing part can be "fixed" by editing its declaration. P15 made declarations required; this
makes the approved numbers immutable without the user.

## Design
- `acceptance.json` (project root): `{"parts": {"<part>": {"bbox": [x, y, z], "through_holes": N}}}`,
  the numbers the user agreed to before geometry.
- `scripts/acceptance.py approve --quote "<the user's own words>"` writes `acceptance.lock`
  (`sha256` of acceptance.json, `quote`, `when`). `emit` prints the declaration lines per part.
- `validate_scad.sh` gate `acceptance`: compares the lock and every part's declarations to acceptance.json.
- Stop hook: an `acceptance.py approve` run in this session must quote words that appear in a user message
  of the same transcript; the agent cannot approve its own numbers.

## AC
- AC-1: `approve` without `--quote` or with an empty quote exits 4 and writes nothing.
- AC-2: `approve --quote "taip"` writes acceptance.lock with the sha256 of acceptance.json and the quote.
- AC-3: Given acceptance.json and no acceptance.lock, then `CHECK_RESULT acceptance=FAIL` ("not approved").
- AC-4: Given acceptance.json changed after approval (sha mismatch), then `acceptance=FAIL` ("changed after
  approval").
- AC-5: Given a part whose `// EXPECTED_BBOX` or `// EXPECTED_THROUGH_HOLES` differs from acceptance.json (or
  uses the NO_ form where acceptance has a number), then `acceptance=FAIL` naming part, field, both values.
- AC-6: Given a part listed in acceptance.json with no `parts/<part>.scad`, then `acceptance=FAIL`.
- AC-7: Given everything matches, then `acceptance=PASS`; without acceptance.json, `acceptance=SKIP`.
- AC-8: `emit` prints, per part, the two declaration lines that make AC-5 pass.
- AC-9: Stop hook: a transcript with a Bash `acceptance.py approve` and a lock whose quote is not in any user
  message blocks the stop; with the quote in a user message it does not. Existing stop_gate cases unchanged.
- AC-10: rule R-20 in rules_manifest.yaml, SKILL.md documents the flow; suite green dev + installed.

## Decisions
- bbox and through-hole count only; EXPECTED_HOLE stays in the part file. shortcut: extend when a part's
  bore is weakened in practice.
- Lock is plain JSON next to the spec, not a database; history is git's job.
- The hook trusts the transcript's user messages; a quote copied from the agent's own text into a user
  message would pass. That is the user's act, which is the point.
