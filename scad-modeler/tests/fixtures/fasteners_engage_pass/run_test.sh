#!/usr/bin/env bash
# AC-H1: M4 screw 16 mm into a 20 mm blind pilot: engagement 16 >= 1.5 d, no WARN/FAIL (negative control for the short cases).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" engage 16 || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 0 ] || { echo "expected exit 0, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "^OK   screw" || { echo "missing /^OK   screw/"; echo "$o"; exit 1; }
exit 0
