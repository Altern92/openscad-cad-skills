#!/usr/bin/env bash
# Owner's deploy: install this repo's OpenSCAD skills into the canon (~/Skills-plugins-etc/skills),
# the tree ~/.claude/skills links to. Same path as everyone else -- install.sh, i.e. only a commit
# that is on GitHub origin/main -- plus the canon extras: manual-only SKILL.md for openscad-cad and
# scad-modeler (user rule), the DSH fork of openscad-organic, and an INCIDENTS.json schema check.
# GenKit (kit/, gen/, tests/genkit/) lives in this repo since 2026-11-14; nothing is synced from the
# SSD any more (INC-2026-11-13-09: that sync rolled back a newer fix).
# Usage: bash scripts/deploy_to_canon.sh [--dev] [CANON_SKILLS_DIR]
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEV=""; DST=""
for a in "$@"; do case "$a" in --dev) DEV="--dev" ;; *) DST="$a" ;; esac; done
DST="${DST:-$HOME/Skills-plugins-etc/skills}"
[ -d "$DST" ] || { echo "ERROR: no canon dir $DST" >&2; exit 1; }
python3 "$SRC/scad-modeler/scripts/incidents.py" check --file "$SRC/INCIDENTS.json" >/dev/null || {
    echo "ERROR: INCIDENTS.json failed schema validation -- run: python3 scad-modeler/scripts/incidents.py check" >&2
    exit 1
}
bash "$SRC/scripts/test_install.sh"   # install.sh's own guard behaves (clean clone ok, dirty refused)
bash "$SRC/scripts/test_plugin.sh"    # the repo still installs as a plugin (SKIP without the claude CLI)
# DSH keeps its own manual-only copy of openscad-organic; it went stale (no P6) when
# only skills/ was deployed.
FORK="$DST/../skills-forks/dsh/openscad-organic"
bash "$SRC/install.sh" $DEV --manual-only --no-test "$DST"
if [ -d "$FORK" ]; then
    rsync -a --delete --exclude __pycache__ --exclude SKILL.md "$SRC/openscad-organic/" "$FORK/"
    awk 'NR==1{print; print "disable-model-invocation: true"; next} /^disable-model-invocation:/{next} 1' \
        "$SRC/openscad-organic/SKILL.md" > "$FORK/SKILL.md"
fi
echo "Running full canonical regression suite ($DST/scad-modeler/tests/run_all.sh, includes GenKit)..."
out="$(cd "$DST/scad-modeler" && bash tests/run_all.sh 2>&1)" && rc=0 || rc=$?
line="$(printf '%s\n' "$out" | grep '^Regression suite:' | tail -1)"
if [ "$rc" -ne 0 ]; then
    printf '%s\n' "$out" | tail -30 >&2
    echo "ERROR: canonical regression suite failed (${line:-rc=$rc}) -- run: (cd $DST/scad-modeler && bash tests/run_all.sh)" >&2
    exit 1
fi
echo "Canonical ${line}"
echo "deployed to $DST (scad-modeler + GenKit regression suite passed)"
