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
cp "$SRC/INCIDENTS.md" "$DST/INCIDENTS.md"
echo "deployed to $DST -- now: (cd ~/.claude/skills/scad-modeler && bash tests/run_all.sh)"
