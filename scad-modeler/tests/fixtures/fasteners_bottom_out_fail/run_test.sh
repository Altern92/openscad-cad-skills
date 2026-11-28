#!/usr/bin/env bash
# AC-H1: 16 mm screw, blind pilot only 10 mm deep: the tip hits the hole bottom before the head seats: FAIL 'bottoms out'.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" bottom || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "bottoms out" || { echo "missing /bottoms out/"; echo "$o"; exit 1; }
exit 0
