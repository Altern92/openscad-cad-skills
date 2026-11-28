#!/usr/bin/env bash
# wave2 review: "aluminum" is an alias of "aluminium": 4.5 mm engagement (< 2 d) must FAIL, not be skipped.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" engage 4.5 '{"into_material": "aluminum"}' || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] && echo "$o" | grep -q "aluminium, Tameson" || { echo "expected exit 3 aluminium engagement FAIL, got $r"; echo "$o"; exit 1; }
exit 0
