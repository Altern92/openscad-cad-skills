#!/usr/bin/env bash
# P1 / AC-8 (2026-11-01): the gate only helps if the agent stops on it. Both
# skills must say what env=FAIL means and what to do; scad-modeler must not
# keep claiming validate_scad.sh returns only 0 or 1 (it now returns 5 too);
# openscad-cad gates a lone part through validate_scad.sh <file>.scad, never by
# running check_dimensions/check_features by hand (P10 / AC-4: one validation path).
set -uo pipefail
M="$SCAD_MODELER_SCRIPTS/../SKILL.md"; C="$SCAD_MODELER_SCRIPTS/../../openscad-cad/SKILL.md"
fail=0
need() { grep -q -- "$2" "$1" || { echo "$(basename "$(dirname "$1")")/SKILL.md lacks: $2" >&2; fail=1; }; }
need "$M" 'env=FAIL'; need "$M" 'setup_env.sh'; need "$M" 'exit 5'
grep -q 'only ever returns `0` or `1`' "$M" && { echo "scad-modeler still says validate_scad.sh returns only 0 or 1" >&2; fail=1; }
need "$C" 'env=FAIL'; need "$C" 'validate_scad.sh [^ ]*\.scad'
grep -nE '^[^#]*check_(dimensions|features)\.py +--' "$C" && { echo "openscad-cad runs a gating checker by hand (second path)" >&2; fail=1; }
exit $fail
