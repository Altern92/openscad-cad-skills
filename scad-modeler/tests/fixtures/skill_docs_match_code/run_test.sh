#!/usr/bin/env bash
# P11 / AC-12, AC-13 (2026-11-01): docs name only scripts and flags that exist.
# AC-13 proves the check can fail: a temp copy with a fake script, then a fake flag.
set -uo pipefail
R="$(cd "$SCAD_MODELER_SCRIPTS/../.." && pwd)"
C="$(pwd)/docs_match_code.py"
python3 "$C" "$R" || exit 1
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
rsync -a --exclude .git --exclude build "$R/" "$tmp/r/"
echo 'Run `python3 scripts/check_nonexistent.py` first.' >> "$tmp/r/openscad-cad/SKILL.md"
python3 "$C" "$tmp/r" >/dev/null && { echo "AC-13: fake script not caught" >&2; exit 1; }
rsync -a --exclude .git --exclude build "$R/" "$tmp/r2/"
echo 'Run `python3 .../scripts/check_dimensions.py --no-such-flag x`.' >> "$tmp/r2/openscad-cad/SKILL.md"
python3 "$C" "$tmp/r2" >/dev/null && { echo "AC-13: fake flag not caught" >&2; exit 1; }
exit 0
