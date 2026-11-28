#!/usr/bin/env bash
# P41 / AC-W3-2: Bethune sec 6-13 M10x1.25x25 through a 10 mm cover: tapped hole 18 deep is OK (3.0 >= 2P past the
# tip), 17 deep WARNs "2P" (2.0 < 2.5) but still exits 0 (book rule, not a part-killer); through hole: no WARN.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
run() { rm -f "$t"/*.stl; python3 "$here/make.py" "$t" "$1" || exit 1
        o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?; }
run 18; [ "$r" -eq 0 ] || { echo "18 deep: expected exit 0, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -q "2P" && { echo "18 deep: unexpected 2P warning"; echo "$o"; exit 1; }
run 17; [ "$r" -eq 0 ] || { echo "17 deep: expected exit 0 (WARN only), got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "WARN .*2\.0 mm past the tip < 2P = 2\.5" || { echo "17 deep: missing 2P WARN"; echo "$o"; exit 1; }
run 26; [ "$r" -eq 0 ] || { echo "through: expected exit 0, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -q "2P" && { echo "through hole: unexpected 2P warning"; echo "$o"; exit 1; }
exit 0
