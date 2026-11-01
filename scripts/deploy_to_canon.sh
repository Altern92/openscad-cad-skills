#!/usr/bin/env bash
# Copy this repo's OpenSCAD skills into the canon (~/Skills-plugins-etc/skills), the
# tree ~/.claude/skills links to. One command so the copies cannot drift: by hand,
# skills/INCIDENTS.md was left behind and a deleted script (run_checks.py) would have
# stayed installed. Canon openscad-cad/scad-modeler SKILL.md keep
# `disable-model-invocation: true` (user rule); openscad-organic is copied as is.
# Usage: bash scripts/deploy_to_canon.sh [CANON_SKILLS_DIR]   then run the installed suite.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="${1:-$HOME/Skills-plugins-etc/skills}"
[ -d "$DST" ] || { echo "ERROR: no canon dir $DST" >&2; exit 1; }
rsync -a --delete --exclude __pycache__ "$SRC/openscad-organic/" "$DST/openscad-organic/"
for s in openscad-cad scad-modeler; do
    rsync -a --delete --exclude __pycache__ --exclude build --exclude SKILL.md "$SRC/$s/" "$DST/$s/"
    awk 'NR==1{print; print "disable-model-invocation: true"; next} /^disable-model-invocation:/{next} 1' \
        "$SRC/$s/SKILL.md" > "$DST/$s/SKILL.md"
done
# DSH keeps its own manual-only copy of openscad-organic; it went stale (no P6) when
# only skills/ was deployed.
FORK="$DST/../skills-forks/dsh/openscad-organic"
if [ -d "$FORK" ]; then
    rsync -a --delete --exclude __pycache__ --exclude SKILL.md "$SRC/openscad-organic/" "$FORK/"
    awk 'NR==1{print; print "disable-model-invocation: true"; next} /^disable-model-invocation:/{next} 1' \
        "$SRC/openscad-organic/SKILL.md" > "$FORK/SKILL.md"
fi
cp "$SRC/INCIDENTS.md" "$DST/INCIDENTS.md"
mkdir -p "$DST/references" && cp "$SRC/references/retrieval.md" "$DST/references/retrieval.md"   # skills read ../references/retrieval.md
# OpenSCAD_GenKit (SSD) builds on validate_scad.sh's CHECK_RESULT/COVERAGE lines; its
# handoff (docs/12 §7) asks that a gate change never silently break it.
GENKIT="${GENKIT_DIR:-/Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit}"
if [ -f "$GENKIT/tests/run_all.sh" ]; then
    if (cd "$GENKIT" && SCAD_GATE="$DST/scad-modeler/scripts/validate_scad.sh" bash tests/run_all.sh 2>&1 | tail -1 | grep -q ' 0 failed'); then
        echo "GenKit contract: green"
    else
        echo "ERROR: GenKit tests fail against the deployed validator -- run: (cd $GENKIT && bash tests/run_all.sh)" >&2
        exit 1
    fi
else
    echo "GenKit contract: SKIP ($GENKIT not mounted)"
fi
echo "deployed to $DST -- now: (cd ~/.claude/skills/scad-modeler && bash tests/run_all.sh)"
