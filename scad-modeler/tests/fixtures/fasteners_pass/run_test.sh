#!/usr/bin/env bash
# Same block and cover as fasteners_head_cross_fail, but the cover has its 8.5 mm head hole and the
# side screw sits 10 mm higher, so the paths do not meet: check_fasteners.py must pass.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
"$OPENSCAD" --backend=Manifold --render -o block.stl block.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -D 'HEAD_HOLE=true' -o cover.stl cover.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners fasteners.json block.stl cover.stl 2>&1)
actual=$?
rm -f block.stl cover.stl
[ "$actual" -eq 0 ] || { echo "expected exit 0, got $actual" >&2; echo "$out" >&2; exit 1; }
exit 0
