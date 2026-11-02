#!/usr/bin/env bash
# Proves `// EXPECTED_BBOX_TOL:` tightens check_dimensions.py: the same 0.2 mm
# slip passes under the derived bound (control) and fails with the declaration.
# Also proves a declaration can never LOOSEN the gate.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
CHK="$SCAD_MODELER_SCRIPTS/check_dimensions.py"
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
fail() { echo "$1" >&2; echo "$2" >&2; rm -f part.stl loose.scad nodecl.scad; exit 1; }

out=$(python3 "$CHK" --stl part.stl --scad part.scad 2>&1); rc=$?
[ "$rc" -eq 1 ] || fail "declared tol: expected exit 1, got $rc" "$out"

grep -v EXPECTED_BBOX_TOL part.scad > nodecl.scad
out=$(python3 "$CHK" --stl part.stl --scad nodecl.scad 2>&1); rc=$?
[ "$rc" -eq 0 ] || fail "control (derived bound only): expected exit 0, got $rc" "$out"

sed 's#EXPECTED_BBOX_TOL: 0.01#EXPECTED_BBOX_TOL: 5#' part.scad > loose.scad
out=$(python3 "$CHK" --stl part.stl --scad loose.scad 2>&1); rc=$?
[ "$rc" -eq 0 ] || fail "loose declaration: expected the derived bound (exit 0), got $rc" "$out"
echo "$out" | grep -q "looser than the derived bound" || fail "loose declaration: NOTE missing" "$out"
python3 - "$out" <<'PY' || fail "loose declaration widened the tolerance" "$out"
import re, sys
tols = [float(x) for x in re.search(r"within \[([^\]]*)\]", sys.argv[1]).group(1).split(",")]
sys.exit(0 if max(tols) < 1.0 else 1)
PY
rm -f part.stl loose.scad nodecl.scad
exit 0
