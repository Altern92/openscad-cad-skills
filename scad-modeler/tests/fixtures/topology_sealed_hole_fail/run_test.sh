#!/usr/bin/env bash
# P12 / AC-8 (2026-11-01). Euler characteristic (EvoCAD, arXiv 2510.11631):
# genus = (2*components - chi)/2 counts through-holes, so a sealed bore drops it.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_topology.py" --stl part.stl --scad part.scad 2>&1); rc=$?
rm -f part.stl
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
[ "$rc" -eq 3 ] || die "AC-8: exit $rc, want 3"
echo "$out" | grep -q 'expected 2' || die "AC-8: no 'expected 2'"
echo "$out" | grep -q 'found 1' || die "AC-8: no 'found 1'"
exit 0
