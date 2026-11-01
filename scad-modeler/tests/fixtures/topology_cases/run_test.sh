#!/usr/bin/env bash
# P12 / AC-7, AC-9, AC-10 (2026-11-01): declared through-holes match -> PASS;
# no declaration -> SKIP, never a guess; open mesh -> FAIL, never a silent PASS.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
C="$SCAD_MODELER_SCRIPTS/check_topology.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
plate='$fn=48; difference(){ cube([40,20,5]); for (x=[10,30]) translate([x,10,-1]) cylinder(d=5,h=7); }'
printf '// EXPECTED_THROUGH_HOLES: 2\n%s\n' "$plate" > "$tmp/ok.scad"
printf '%s\n' "$plate" > "$tmp/none.scad"
"$OPENSCAD" --backend=Manifold --render -o "$tmp/ok.stl" "$tmp/ok.scad" >/dev/null 2>&1

# AC-7
out=$(python3 "$C" --stl "$tmp/ok.stl" --scad "$tmp/ok.scad" 2>&1); rc=$?
[ "$rc" -eq 0 ] || die "AC-7: exit $rc, want 0"
echo "$out" | grep -q 'PASS' || die "AC-7: no PASS"

# AC-9
out=$(python3 "$C" --stl "$tmp/ok.stl" --scad "$tmp/none.scad" 2>&1); rc=$?
[ "$rc" -eq 0 ] || die "AC-9: exit $rc, want 0"
echo "$out" | grep -q 'SKIP' || die "AC-9: no SKIP"
echo "$out" | grep -q 'EXPECTED_THROUGH_HOLES' || die "AC-9: reason does not name the declaration"

# AC-10: a cube with its top face missing (10 of 12 triangles)
python3 - "$tmp/open.stl" <<'PY'
import sys
v=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
tris=[(0,2,1),(0,3,2),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
with open(sys.argv[1],"w") as f:
    f.write("solid open\n")
    for t in tris:
        f.write(" facet normal 0 0 0\n  outer loop\n")
        for i in t: f.write("   vertex %g %g %g\n" % v[i])
        f.write("  endloop\n endfacet\n")
    f.write("endsolid open\n")
PY
out=$(python3 "$C" --stl "$tmp/open.stl" --scad "$tmp/ok.scad" 2>&1); rc=$?
[ "$rc" -eq 3 ] || die "AC-10: exit $rc, want 3"
echo "$out" | grep -q 'not watertight' || die "AC-10: no 'not watertight'"
exit 0
