#!/usr/bin/env bash
# Monthly geometric mutation test runner for scad-modeler (GenKit lives in scad-modeler/tests/genkit).
# Installed as ~/Library/LaunchAgents/local.scad-modeler.geom-mutation.plist (1st of each month, 10:00).
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

SKILL_DIR="${SCAD_MODELER_SKILL_DIR:-$HOME/.claude/skills/scad-modeler}"
LOG_DIR="$HOME/.claude/scad_modeler/validation_log"
LOG_FILE="$LOG_DIR/geom_mutation_monthly.log"
mkdir -p "$LOG_DIR"

VENV_PY="$HOME/.local/share/scad-modeler/venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  VENV_PY="$(command -v python3)"
fi

{
  echo "=== $(date -u +"%Y-%m-%dT%H:%M:%SZ") geom_mutation monthly run ==="
  "$VENV_PY" "$SKILL_DIR/tests/genkit/geom_mutation.py" --jobs 4
  echo "=== PASS ==="
} >> "$LOG_FILE" 2>&1

