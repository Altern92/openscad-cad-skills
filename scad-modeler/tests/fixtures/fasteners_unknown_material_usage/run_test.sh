#!/usr/bin/env bash
# wave2 review: an unknown "insert" key / "into_material" value used to be silently skipped; now usage error exit 4 listing accepted values.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" engage 16 '{"into_material": "aluminum"}' || exit 1
sed -i.bak 's/"aluminum"/"brass"/' "$t/f.json"
want='brass'
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 4 ] || { echo "expected exit 4, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -q "$want" && echo "$o" | grep -Eq "accepted: .*aluminium" || { echo "usage message must name the bad value and the accepted ones"; echo "$o"; exit 1; }
exit 0
