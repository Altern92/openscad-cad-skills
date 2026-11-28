#!/usr/bin/env bash
# AC-H1: heat-set insert M3 (L 5.7, inserts.json) with only 4 mm of screw reaching into it: FAIL.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" insert 4 || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "engagement 4.0 mm < insert length 5.7" || { echo "missing /engagement 4.0 mm < insert length 5.7/"; echo "$o"; exit 1; }
exit 0
