# P20–P22 + GenKit in repo + GitHub install — Acceptance Criteria (2026-11-14)

Approval: the user wrote on 2026-11-14 "update those items and continue development! make genkit a permanent part of it! and make it always install via GitHub if anyone tries to install it in the future!" (translated from Lithuanian). That covers the P20/P21 AC proposed in NEXT.md §0 and the two new requests. P22 was replaced by G1–G3: once GenKit lives only in this repo, nothing syncs from the SSD any more.

## GenKit is part of the repo (replaces P22)
- **G1** Given `scripts/deploy_to_canon.sh`, when it runs, then it never reads `/Volumes/.../OpenSCAD_GenKit`, and `scripts/deploy_genkit.sh` is gone. Check: `grep -c OpenSCAD_GenKit scripts/*.sh` → 0. Reason: INC-2026-11-13-09, where the SSD copy rolled back a fix.
- **G2** Given the old SSD-only material (`docs/`, `examples/`, `scripts/run_geom_mutation_monthly.sh`), when the move is done, then it lives in this repo: docs under `docs/genkit/`, examples under `scad-modeler/gen/examples/` (they must pass `validate_schema.py`), and the monthly runner under `scripts/`. The SSD repo gets a MOVED banner and nothing on it is deleted.
- **G3** Given the deploy, when it finishes, then the GenKit contract (`tests/genkit`) has run against the deployed validator. It already runs inside `scad-modeler/tests/run_all.sh`, so no second, SSD-based run is needed.

## Install from GitHub
- **H1** Given a machine with git, when someone runs `bash install.sh`, either from a clone or from the GitHub raw URL, then the source is the GitHub repo `Altern92/openscad-cad-skills`:
  - if the script is not inside a clone of it, it clones or pulls into `${SCAD_SKILLS_SRC:-~/.local/share/openscad-cad-skills}`;
  - it then copies `openscad-cad`, `scad-modeler` (with `kit/`, `gen/` and `tests/genkit/`), `openscad-organic`, `INCIDENTS.json` and `references/retrieval.md` into `${1:-~/.claude/skills}`.
- **H2** Given a clone whose HEAD is not on `origin/main`, or that has uncommitted tracked changes, when `install.sh` runs, then it stops with exit 1 and installs nothing, unless `--dev` is given. Reason: an install must equal what is on GitHub.
- **H3** Given `deploy_to_canon.sh` (the owner's canon), when the dev tree is dirty or HEAD is not pushed, then it refuses (exit 1), unless `--dev` is given. With `--dev` it prints `WARNING: deploying unpushed dev tree`.
- **H4** Given install or deploy has finished, when the installed suite runs, then the reported count is the real one. Today the message is hard-coded as "85 passed", while the suite actually has 89 tests.
- **H5** A fixture runs `install.sh` against a local bare repo into a temp dir:
  - a clean clone → installed tree with `scad-modeler/kit/lib.scad`, exit 0;
  - a dirty clone without `--dev` → exit 1 and an empty target.

## P20: parts made outside parts/*.scad
- **F1** Given `fasteners.json` with `"mounts": [{"part": "leg", "on": "plate"}]`, when no declared fastener goes through `leg` (a shank point inside the leg mesh) with `into` matching `plate`, then `check_fasteners.py` FAILs with `mount leg -> plate: no declared fastener` (exit 3).
- **F2** Given a mounted part whose body covers a declared host screw head, then the result is FAIL `head blocked` (this check already exists; the fixture proves it for STLs made outside OpenSCAD).
- **F3** Given the same leg with head reliefs and 2 screws into the plate, then the result is PASS (exit 0).
- **F4** Given positioned STLs and `fasteners.json` but no `assembly.scad` (a Python- or trimesh-built project), when `validate_scad.sh` runs, then `fasteners` actually runs on `build/positioned/*.stl`. Before this change it was INCONCLUSIVE.
- **F5** A `mutants.tsv` row: `check_fasteners` → `fasteners_mount_unfastened_fail`.

## P21: declared motion groups
- **M1** Given a motion driver with `"parts": [..]` in place of `"part"`, then every listed part moves with the same transform. The gear-sign check must not treat the empty `part` as a match for every name.
- **M2** Given a top-level `"static": [..]` in `joints.json`, when an STL is matched neither by any driver nor by `static`, then `motion_sweep.py` FAILs (exit 3) and names the part before any sweep runs.
- **M3** Given a prismatic group whose path crosses a static sensor, then the result is FAIL, and the report names the pair and the travel position.
- **M4** Given the same set-up with the sensor out of the path and every part assigned, then the result is PASS, and the report prints the worst clearance and the pair names.
- **M5** A `mutants.tsv` row: `motion_sweep` → `motion_groups_unassigned_fail`.

## NEXT.md
- **N1** In §0, P20 and P21 are marked [x] with their commits, and P22 is marked as superseded by G1–G3.
- **N2** §1, §6 and the header get a note that P7, P18 and P19 superseded them.
- **N3** §3b and §4 stay as open items; the cost-of-pass agent run is listed as waiting for paid-run permission.

## Regression
- **R1** `scad-modeler/tests/run_all.sh` passes everything, in dev and via `~/.claude/skills`, including the new fixtures.
