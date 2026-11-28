#!/usr/bin/env bash
# AC-H2 (P20b, wave 2): the leg rests on the plate (z=10, 60x40 mm) AND on a step (z=15, 20x40 mm) that carries
# an unused M5 hole at (70, 20). The big plane has no hole; the hole is under the smaller plane. Must FAIL.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_engage/make.py" "$t" twoplane || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "covers host hole at \((69\.9|70\.0|70\.1), (19\.9|20\.0|20\.1), 15" || { echo "no FAIL at (70, 20, 15)"; echo "$o"; exit 1; }
python3 - "$t/f.json" "$t/ok.json" <<'PY'
import json, sys; d = json.load(open(sys.argv[1])); d["mounts"][0]["covered_ok"] = [[70, 20, 15]]; json.dump(d, open(sys.argv[2], "w"))
PY
o2=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/ok.json" "$t"/*.stl 2>&1); r2=$?
[ "$r2" -eq 0 ] || { echo "covered_ok listed: expected exit 0, got $r2"; echo "$o2"; exit 1; }
exit 0
