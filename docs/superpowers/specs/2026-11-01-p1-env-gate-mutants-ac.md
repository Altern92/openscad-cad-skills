# P1 environment gate + P1b checker mutants — Acceptance Criteria

Date: 2026-11-01. Tier: feature (changes the `validate_scad.sh` interface that SKILL.md relies on).
Research: Obsidian `Research/Runs/2026/2026-11-01-openscad-skills.md` (31/95 incidents = false PASS / silent SKIP).

## Baseline (measured 2026-11-01, mini)

- `python3` = `/usr/bin/python3`, without trimesh, shapely, scipy, networkx, manifold3d, rtree, jsonschema (`doctor.py`).
- `validate_scad.sh --all` on `examples/gear_reduction` without `.venv`: rc=1, but the reasons are misleading —
  `connectivity=FAIL`, `mechanics=FAIL`, `collisions=INCONCLUSIVE` (real cause: missing modules).
- BOSL2 not installed (`no OpenSCAD library directory found`) → `render=FAIL` with "Can't find include file".
  An agent may mistake this for a geometry error.
- `doctor.py` diagnoses correctly, but `validate_scad.sh` does not call it.
- 16 `check_*.py`; all have ≥1 fixture, but whether each has a fixture that expects FAIL is unknown (a regex heuristic shows 8 without one ◇).

## Architecture (short)

```
validate_scad.sh / tests/run_all.sh
  └─ scripts/resolve_python.sh  →  SCAD_PYTHON  >  ~/.local/share/scad-modeler/venv/bin/python  >  python3
  └─ env gate (before any check): doctor.py --json with that interpreter
        missing module / openscad / included library → CHECK_RESULT env=FAIL + fix command, exit 5
scripts/setup_env.sh  →  uv venv ~/.local/share/scad-modeler/venv + requirements.txt (idempotent)
```
All `python3 "$SCRIPT_DIR/check_*.py"` calls change to `"$PY" ...`. The venv lives outside the repo so it also works for the installed skill (`~/.claude/skills` → `~/Skills-plugins-etc/skills`) and on the MBP.

## P1: environment gate

- **AC-1.** Given `SCAD_PYTHON` is unset and `~/.local/share/scad-modeler/venv/bin/python` has all modules, when `validate_scad.sh --all` runs in a shell whose `python3` lacks trimesh, then all Python checks run with the venv interpreter and the output has no "not installed" errors.
- **AC-2.** Given `SCAD_PYTHON=/path/python`, when validation runs, then exactly that interpreter is used (precedence over the venv and `python3`); the output contains a line `ENV python=<path>`.
- **AC-3 (error path).** Given the selected interpreter lacks at least one of trimesh, shapely, scipy, networkx, manifold3d, rtree, yaml, jsonschema, when validation runs, then it prints `CHECK_RESULT env=FAIL`, the list of missing modules and the command `bash <scripts>/setup_env.sh`; no other `CHECK_RESULT` lines; exit 5.
- **AC-4 (error path).** Given `openscad` is not found (`OPENSCAD` or PATH), when validation runs, then `CHECK_RESULT env=FAIL` with install instructions, exit 5 (now: exit 1 with ERROR).
- **AC-5 (error path, ◇ provisional).** Given a project `.scad` has `include <BOSL2/...>` (or another `doctor.py` LIBRARIES library) and `doctor.py` reports it missing, when validation runs, then `CHECK_RESULT env=FAIL` names the library and the file that includes it; exit 5. A library the project does not include does not stop the gate.
- **AC-6.** Given `uv` is on the machine, when `bash scripts/setup_env.sh`, then a venv is created from `requirements.txt`, and `doctor.py` with that interpreter shows all Python packages `ok`; a second run exits 0 and reinstalls nothing.
- **AC-7.** Given modules are missing, when `bash tests/run_all.sh`, then it prints the same gate message and exits ≠0 before running fixtures (not "16/48 FAIL").
- **AC-8.** Given `scad-modeler/SKILL.md` and `openscad-cad/SKILL.md`, when searched for `env=FAIL`, then each has a rule: stop, show the user the fix command, report no check results. Check: doc fixture with `grep`.
- **AC-9 (regression).** Given all dependencies and BOSL2 are present, when `tests/run_all.sh`, then all existing fixtures PASS (48/48 + new ones), and the `examples/gear_reduction` `CHECK_RESULT` set matches the current one, except for the new `env=PASS` line.

## P1b: checker mutants

- **AC-10.** Given `tests/mutants.tsv` (columns: checker, fixture), when the meta-fixture `mutant_coverage` runs, then it FAILs if any `scripts/check_*.py` is not in the table or the named fixture does not exist.
- **AC-11 (mutant check).** Given each `mutants.tsv` fixture, when it runs with `SCAD_MODELER_SCRIPTS` pointed at a copy where that checker is replaced by an `exit 0` stub, then the fixture FAILs. This proves the fixture really depends on the checker catching the defect, rather than passing regardless.
- **AC-12.** Given the checkers that currently have no fixture satisfying AC-11, when implementation is done, then each gets one deliberately broken-input fixture (the list comes out of the AC-11 measurement; ◇ the heuristic shows up to 8).

## Out of scope
- Installing BOSL2 on mini (proposed separately; AC-5 only reports).
- The `run_checks.py` prototype (not the main path) – only swap `python3` for the resolver, if simple.
- P2–P7.
