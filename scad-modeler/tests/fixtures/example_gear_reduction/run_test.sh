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
grep -q "OK: face overlap pinion<->spur" <<< "$o" || { echo "face overlap not reported: $(grep -i overlap <<< "$o")"; exit 1; } >&2
# Audit A1 (2026-11-28): the spur lifted 8.2 mm (above the 8 mm pinion: teeth share no face width) passed --all,
# because centre distance ignores the axial position and a 0.24 mm diagonal gap satisfied max_gap.
sed -i.bak 's|\["spur",   \[center_distance, 0, 0\]|["spur",   [center_distance, 0, 8.2]|' layout.scad
grep -q "center_distance, 0, 8.2" layout.scad || { echo "fixture sed did not apply"; exit 1; } >&2
rm -rf build; o=$(bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all 2>&1); r=$?
[ $r -ne 0 ] && grep -q "face overlap pinion<->spur" <<< "$o" \
    || { echo "A1: axially stacked gears passed (rc $r): $(grep -iE "overlap|centre" <<< "$o" | head)"; exit 1; } >&2
exit 0
