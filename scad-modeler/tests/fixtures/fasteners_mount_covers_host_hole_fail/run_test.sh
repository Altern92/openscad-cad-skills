#!/usr/bin/env bash
# P20b (2026-11-14): the leg is screwed down correctly and clears the BK12 heads, but its flat
# face covers an M5 hole in the plate that no declared fastener uses (Big_CNC: the Z mount leg
# was drawn over the plate's existing holes). An undeclared host hole under a mounted part
# must FAIL with its position, unless the mount lists it in "covered_ok".
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../fasteners_mount/make_stls.py" "$t" 1 1 1 || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$here/../fasteners_mount/fasteners_full.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -Eq "mount leg -> plate: covers host hole at \((29\.9|30\.0|30\.1), (19\.9|20\.0|20\.1)," || { echo "no covered-hole FAIL at (30, 20)"; echo "$o"; exit 1; }
python3 - "$here/../fasteners_mount/fasteners_full.json" "$t/ok.json" <<'PY'
import json, sys; d = json.load(open(sys.argv[1])); d["mounts"][0]["covered_ok"] = [[30, 20, 10]]; json.dump(d, open(sys.argv[2], "w"))
PY
o2=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/ok.json" "$t"/*.stl 2>&1); r2=$?
[ "$r2" -eq 0 ] || { echo "covered_ok listed: expected exit 0, got $r2"; echo "$o2"; exit 1; }
exit 0
