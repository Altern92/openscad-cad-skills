# Claude Code plugin + marketplace — Acceptance Criteria (2026-11-14)

Approval: the user asked whether the skills should become a plugin, got the plan (plugin as the main install path, install.sh kept, claude.ai ZIP dropped) and answered "tai padaryk tai!" ("then do it!").

Facts checked before writing (prototype in a scratch copy, Claude Code CLI):
- `.claude-plugin/plugin.json` with `"skills": ["./openscad-cad", "./scad-modeler", "./openscad-organic"]` passes `claude plugin validate`; the skills stay where they are.
- An install copies the whole repo into `~/.claude/plugins/cache/<mkt>/<plugin>/<version>/`, so `../INCIDENTS.json`, `../references/` and `../scad-modeler` resolve.
- Without `version`, the version is the commit sha, and `claude plugin update` installs each new commit into a new directory. Anything written into the cache is therefore lost on update.

## Plugin
- **P1** Given the repo root, when `claude plugin validate .` runs, then it exits 0. `plugin.json` has `name`, `description`, `author`, `skills` (the 3 paths) and no `version`. `marketplace.json` has `name`, `description`, `owner` and one plugin with `"source": "./"`.
- **P2** Given a git repo of the working tree added as a marketplace into a temp `CLAUDE_CONFIG_DIR`, when `claude plugin install openscad-cad-skills@openscad-cad-skills` runs, then `claude plugin details openscad-cad-skills` lists exactly `openscad-cad`, `openscad-organic` and `scad-modeler`.

## Incidents from an installed plugin
- **P3** Given the installed cache, when `python3 scad-modeler/scripts/incidents.py list` runs there with no `--file`, then the total equals the repo's `INCIDENTS.json` count.
- **P4** Given the same cache, when `incidents.py add ...` runs with no `--file`, then the entry is written to `$SCAD_INCIDENTS_LOCAL` (default `${XDG_DATA_HOME:-~/.local/share}/scad-modeler/INCIDENTS.local.json`), the cache `INCIDENTS.json` stays byte-identical, `list` shows count + 1, and the new id does not repeat an id already in the shipped file.
- **P5** (failure path) Given a local file with invalid JSON, when `add` runs, then it exits non-zero, the error names the local path, and nothing is written.
- **P6** Given the dev repo or a `~/.claude/skills` install (no `/plugins/cache/` in the path), when `incidents.py` runs, then its behaviour is unchanged: it reads and writes `../../INCIDENTS.json`, and `--file` still wins.

## Docs and wiring
- **P7** The README's install section shows the plugin route first (`/plugin marketplace add Altern92/openscad-cad-skills` + install), with `install.sh` as the alternative. The skill names are listed as `openscad-cad-skills:<skill>`.
- **P8** `scripts/test_plugin.sh` checks P1–P5 and prints `SKIP` (exit 0) when no `claude` CLI is present, as in CI. `deploy_to_canon.sh` runs it next to `test_install.sh`.

## Regression
- **R1** `scad-modeler/tests/run_all.sh` passes everything in dev and in canon, and `scripts/test_install.sh` passes 6/6.
