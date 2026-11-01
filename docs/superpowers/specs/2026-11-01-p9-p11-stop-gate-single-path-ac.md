# P9–P11: stop gate, single validation path, docs-match-code (AC)

Date: 2026-11-01. Tier: feature (new hook + new validate_scad.sh mode + config change).
Origin: Uber MCP Gateway principles (vault `Research/Runs/2026/2026-10-31-mcp-gateway-agentbus.md`):
deterministic policy per call, one execution path, descriptions must match code.

## Baseline (measured 2026-11-01)
- `validate_scad.sh <basename>` already validates one part from `parts/`, in a bare dir too
  (env, connectivity, dimensions, features + project gates that SKIP/PASS without files), and writes
  `build/.validation_state.json` with `verdict` and sha256 of `params/layout/assembly/parts/*.scad`.
- `openscad-cad/SKILL.md` §4.5 teaches running `check_dimensions.py` / `check_features.py` by hand:
  a second path that skips connectivity and the state file.
- Docs vs code: 63 `scripts/X` references and 21 flags in SKILL.md + references, 0 drift (scan
  script in this session). P11 is a guard against future drift, not a fix.

## Architecture
```
Edit/Write *.scad ──> transcript ──┐
                                   ├─> scad_stop_gate.py (Stop hook) ── block / allow
validate_scad.sh ──> build/.validation_state.json (sha256 per source) ┘
```
The hook trusts only the state file's hashes, never the agent's text.

## P10 – one validation path
- AC-1: Given a dir with only `bracket.scad` (no `parts/`) carrying a correct `// EXPECTED_BBOX`, when
  `validate_scad.sh bracket.scad` runs, then it renders `build/bracket.stl`, prints `CHECK_RESULT`
  lines for env, connectivity, dimensions, features plus `COVERAGE`, exits 0, and the state file's
  `sources` holds `"bracket.scad"` with that file's sha256.
- AC-2: Given the same file with a wrong `EXPECTED_BBOX`, then `CHECK_RESULT dimensions=FAIL`, exit 1,
  state `verdict` = `FAIL`.
- AC-3: Given `validate_scad.sh missing.scad`, then `ERROR: missing.scad not found`, exit 1.
- AC-4: Given `openscad-cad/SKILL.md` §4.5, then its code block gates with `validate_scad.sh <file>.scad`
  and no line there runs `check_dimensions.py` or `check_features.py` directly (`check_printability.py`
  stays, labelled advisory).
- AC-5: `validate_scad.sh <basename>` and `--all` behave as before: full suite green and
  `examples/gear_reduction` CHECK_RESULT lines identical to the baseline.

## P9 – Stop hook `scad-modeler/hooks/scad_stop_gate.py` (stdlib)
- AC-6: Given a transcript where Edit/Write changed `X.scad` and no state file covers X (or its hash
  differs from X's current content), when the hook runs with `stop_hook_active=false`, then it prints
  `{"decision": "block", "reason": ...}` naming X and the command to run, exit 0.
- AC-7: Given the state file (found by walking up from X's dir to `build/.validation_state.json`) has
  X's current sha256, then no output, exit 0 – for verdict PASS and FAIL alike (a FAIL that is
  reported is a legitimate end).
- AC-8: Given a transcript with no `.scad` edits, then no output, exit 0.
- AC-9: Given `stop_hook_active=true`, then never blocks (no loops when validation is impossible).
- AC-10: Given an edited file that no longer exists, a path under `/tests/fixtures/`,
  `SCAD_STOP_GATE=0`, or malformed transcript lines/JSON input, then no block and exit 0 (never crashes).
- AC-11: Registered: `~/Skills-plugins-etc/claude/hooks/scad-stop-gate` + `claude/hooks.json` Stop
  entry; `~/.claude/settings.json` gets the same entry (backup first); a smoke run of the installed
  command on a synthetic input blocks. Vault journal entry written.

## P11 – docs match code
- AC-12: Fixture `skill_docs_match_code`: every `*.py`/`*.sh` name in each skill's `SKILL.md` and
  `references/*.md` exists in the repo, and every `--flag` following a `scripts/X` reference on the
  same line appears in X's source. PASS on the current tree.
- AC-13: The same fixture FAILS on a temp copy where a doc names a nonexistent script, and on one
  where a doc gives a nonexistent flag.

## Provisional assumptions
- `.scad` written through Bash (heredoc, `cp`) is not seen by the hook: shortcut, documented.
- FAIL verdict does not block (AC-7); the hook blocks at most once per stop (AC-9).
