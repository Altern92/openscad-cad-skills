#!/usr/bin/env bash
# AC-H1: same 4.5 mm in aluminium (Tameson thread-engagement chart: 2.0-2.5 d, verified): FAIL.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" engage 4.5 '{"into_material":"aluminium"}' || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "FAIL screw|engagement 4.5 mm < 2 d" || { echo "missing /FAIL screw|engagement 4.5 mm < 2 d/"; echo "$o"; exit 1; }
exit 0
