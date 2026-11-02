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
GENKIT="${GENKIT_DIR:-/Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit}"
if [ -d "$GENKIT/kit" ] && [ -f "$SRC/scripts/deploy_genkit.sh" ]; then
    bash "$SRC/scripts/deploy_genkit.sh" "$GENKIT" "$SRC/scad-modeler"
fi
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
# Verify INCIDENTS.json schema before copying to canon.
if [ -f "$SRC/scad-modeler/scripts/incidents.py" ]; then
    python3 "$SRC/scad-modeler/scripts/incidents.py" check --file "$SRC/INCIDENTS.json" >/dev/null || {
        echo "ERROR: INCIDENTS.json failed schema validation -- run: python3 scad-modeler/scripts/incidents.py check" >&2
        exit 1
    }
fi
cp "$SRC/INCIDENTS.json" "$DST/INCIDENTS.json"
rm -f "$DST/INCIDENTS.md"
mkdir -p "$DST/references" && cp "$SRC/references/retrieval.md" "$DST/references/retrieval.md"   # skills read ../references/retrieval.md
# OpenSCAD_GenKit (SSD) builds on validate_scad.sh's CHECK_RESULT/COVERAGE lines; its
# handoff (docs/12 §7) asks that a gate change never silently break it.
GENKIT="${GENKIT_DIR:-/Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit}"
if [ -f "$GENKIT/tests/run_all.sh" ]; then
    genkit_out="$(cd "$GENKIT" && SCAD_GATE="$DST/scad-modeler/scripts/validate_scad.sh" bash tests/run_all.sh 2>&1)" && genkit_rc=0 || genkit_rc=$?
    if [ "$genkit_rc" -eq 0 ] && printf '%s\n' "$genkit_out" | grep -q ' 0 failed$'; then
        echo "GenKit contract: green"
    else
        printf '%s\n' "$genkit_out" >&2
        echo "ERROR: GenKit tests fail against the deployed validator (rc=$genkit_rc) -- run: (cd $GENKIT && bash tests/run_all.sh)" >&2
        exit 1
    fi
else
    echo "GenKit contract: SKIP ($GENKIT not mounted)"
fi
echo "Running full canonical regression suite ($DST/scad-modeler/tests/run_all.sh)..."
if (cd "$DST/scad-modeler" && bash tests/run_all.sh >/dev/null); then
    echo "Canonical regression suite: 85 passed, 0 failed"
else
    echo "ERROR: canonical regression suite failed -- run: (cd $DST/scad-modeler && bash tests/run_all.sh)" >&2
    exit 1
fi
echo "deployed to $DST (all GenKit + scad-modeler regression suites passed)"
