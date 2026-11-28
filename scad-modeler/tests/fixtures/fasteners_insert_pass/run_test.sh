#!/usr/bin/env bash
# AC-H1: the same insert with an 8 mm screw: engages the whole insert, exit 0.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" insert 8 || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 0 ] || { echo "expected exit 0, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "^OK   screw" || { echo "missing /^OK   screw/"; echo "$o"; exit 1; }
exit 0
