#!/usr/bin/env bash
# Sync OpenSCAD_GenKit's payload (kit/, gen/, tests/) into scad-modeler so the
# SSD project, the skill dev repo, and the canon (via deploy_to_canon.sh) cannot
# drift (audit 2026-11-02 §5 #1 & #5).
#
# Usage:
#   bash scripts/deploy_genkit.sh [GENKIT_DIR] [SKILL_DIR]
set -euo pipefail

SRC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GENKIT="${1:-${GENKIT_DIR:-/Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit}}"
SKILL="${2:-$SRC_ROOT/scad-modeler}"

if [ ! -d "$GENKIT/kit" ] || [ ! -d "$GENKIT/gen" ] || [ ! -d "$GENKIT/tests" ]; then
    echo "ERROR: GenKit source not found at $GENKIT (expected kit/, gen/, tests/)" >&2
    exit 1
fi
[ -d "$SKILL/scripts" ] || { echo "ERROR: skill dir not found at $SKILL" >&2; exit 1; }

mkdir -p "$SKILL/kit" "$SKILL/gen" "$SKILL/tests/genkit"
rsync -a --delete --exclude __pycache__ "$GENKIT/kit/" "$SKILL/kit/"
rsync -a --delete --exclude __pycache__ \
    "$GENKIT/gen/emit_part.py" "$GENKIT/gen/schema.json" "$GENKIT/gen/validate_schema.py" \
    "$SKILL/gen/"
rsync -a --delete --exclude __pycache__ "$GENKIT/tests/" "$SKILL/tests/genkit/"
chmod +x "$SKILL/gen/emit_part.py" "$SKILL/gen/validate_schema.py" \
         "$SKILL/tests/genkit/run_all.sh" "$SKILL/tests/genkit/geom_mutation.py" 2>/dev/null || true

# Verify that emit_part.py inside the skill resolves DEFAULT_KIT to $SKILL/kit.
probe="$(mktemp /tmp/genkit_deploy_probe.XXXXXX.scad)"
trap 'rm -f "$probe"' EXIT
python3 "$SKILL/gen/emit_part.py" "$SKILL/tests/genkit/fixtures/box.json" -o "$probe" >/dev/null
REAL_KIT="$(cd "$SKILL/kit" && pwd -P)"
if ! grep -qF "include <$REAL_KIT/lib.scad>" "$probe" && ! grep -qF "include <$SKILL/kit/lib.scad>" "$probe"; then
    echo "ERROR: emitted include does not point at $SKILL/kit:" >&2
    grep '^include' "$probe" >&2
    exit 1
fi

echo "GenKit synced: $GENKIT -> $SKILL/{kit,gen,tests/genkit}"

