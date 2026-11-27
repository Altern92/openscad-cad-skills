#!/usr/bin/env bash
# P29 / AC-4: the README's headline example must stay green. It silently rotted to 3 FAIL (P15/P23/P25 gates
# added after it was written) while CI stayed green, because nothing ran it.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; ex="$here/../../../examples/gear_reduction"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp -R "$ex"/. "$tmp"/; rm -rf "$tmp/build"; cd "$tmp"
o=$(bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all 2>&1); r=$?
[ $r -eq 0 ] && grep -q "All executed checks passed" <<< "$o" && grep -q "OK: centre distance pinion<->spur" <<< "$o" \
    || { echo "examples/gear_reduction: validate_scad.sh --all rc $r"; grep -E "FAIL|INCONCLUSIVE" <<< "$o" | head -20; exit 1; } >&2
exit 0
