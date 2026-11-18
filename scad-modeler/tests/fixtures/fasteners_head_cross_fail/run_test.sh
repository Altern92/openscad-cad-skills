#!/usr/bin/env bash
# Proves check_fasteners.py fails on (1) a screw head covered by a panel without a head hole
# (INC-2026-11-08-01, cnc-valdymo-punktas) and (2) two screws whose paths cross inside a block
# (INC-2026-08-21-07, server_rack). Both screws are 24 mm long and meet at the block centre.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=3
"$OPENSCAD" --backend=Manifold --render -o block.stl block.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o cover.stl cover.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners fasteners.json block.stl cover.stl 2>&1)
actual=$?
rm -f block.stl cover.stl
[ "$actual" -eq "$EXPECTED_EXIT" ] || { echo "expected exit $EXPECTED_EXIT, got $actual" >&2; echo "$out" >&2; exit 1; }
for want in "head blocked" "fasteners cross"; do
    grep -q <<< "$out" "$want" || { echo "expected '$want' in output, got:" >&2; echo "$out" >&2; exit 1; }
done
exit 0
