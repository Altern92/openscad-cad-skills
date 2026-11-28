#!/usr/bin/env bash
# AC-H1: 4.5 mm of M4 thread in plastic (< 1.5 d = 6): WARN only, exit 0 (the 1.5 d plastic figure is unverified, see check_fasteners.py).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" engage 4.5 || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 0 ] || { echo "expected exit 0, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "WARN .*engagement 4.5 mm < 1.5 d" || { echo "missing /WARN .*engagement 4.5 mm < 1.5 d/"; echo "$o"; exit 1; }
exit 0
