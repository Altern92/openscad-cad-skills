#!/usr/bin/env bash
# P40 / AC-W3-1: Bethune sec 8-48 oracle, O20 holes, position_tol T = 0.03: floating needs F <= 19.97 (H - T = F),
# fixed F <= 19.94 (H - 2T = F). 0.01-0.02 mm either side of each limit (a facet-exact limit would be mesh noise).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
run() { rm -f "$t"/*.stl; python3 "$here/make.py" "$t" "$1" "$2" || exit 1
        o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?; }
want() { [ "$r" -eq "$1" ] || { echo "$2: expected exit $1, got $r"; echo "$o"; exit 1; }; }
run floating 19.96; want 0 "floating 19.96"
run floating 19.99; want 3 "floating 19.99"
echo "$o" | grep -q "H - T = F" || { echo "floating: missing H - T = F"; echo "$o"; exit 1; }
run fixed 19.93; want 0 "fixed 19.93"
run fixed 19.96; want 3 "fixed 19.96"
echo "$o" | grep -q "H - 2T = F" || { echo "fixed: missing H - 2T = F"; echo "$o"; exit 1; }
# review: a nut modelled as a part under a through-bolt is not a too-small hole once thread_from = stack thickness
run floating 19.96
python3 - "$t" <<'PY2'
import json, sys, trimesh
t = sys.argv[1]; m = trimesh.creation.cylinder(radius=15, height=8, sections=6)
m = trimesh.boolean.difference([m, trimesh.creation.cylinder(radius=8.75, height=10, sections=96)], engine="manifold")
m.apply_translation([0, 0, -4]); m.export(f"{t}/nut.stl")
f = json.load(open(f"{t}/f.json")); f[0].update({"length": 28, "thread_from": 20}); json.dump(f, open(f"{t}/f.json", "w"))
PY2
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
want 0 "floating with nut part, thread_from 20"
# bad input: NaN, or a fixed screw without thread_from (P40 would cover nothing), is a usage error
run fixed 19.96
python3 - "$t/f.json" <<'PY2'
import json, sys; f = json.load(open(sys.argv[1])); del f[0]["thread_from"]; f[0]["bite_from"] = 10; json.dump(f, open(sys.argv[1], "w"))
PY2
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
want 2 "fixed without thread_from"
echo '[{"name": "n", "start": [0,0,20], "axis": [0,0,-1], "d": 19.9, "length": 20, "position_tol": NaN}]' > "$t/f.json"
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
want 2 "NaN position_tol"
# bad input: a negative tolerance is a usage error, not a silent skip
python3 - "$t/f.json" <<'PY'
import json, sys; f = json.load(open(sys.argv[1])); f[0]["position_tol"] = -0.03; json.dump(f, open(sys.argv[1], "w"))
PY
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners "$t/f.json" "$t"/*.stl 2>&1); r=$?
want 2 "negative position_tol"
exit 0
