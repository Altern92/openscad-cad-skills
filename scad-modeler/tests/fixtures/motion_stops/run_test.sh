#!/usr/bin/env bash
# P28 joint stops (motion_sweep.py "stops"): a motion that claims mechanical end stops must be stopped by
# the parts within "within_deg" past each end of range_deg. An arm swung 0..80 deg with a post at ~90 deg
# is stopped (PASS, stop reported); with the post moved to ~150 deg nothing stops it (FAIL, names the
# end); the low end (0) has no post at all, so asking for stops at both ends FAILs there.
set -uo pipefail
M="$SCAD_MODELER_SCRIPTS/motion_sweep.py"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; cd "$t"
OPENSCAD=${OPENSCAD:-openscad}
printf 'translate([2, -2, 0]) cube([30, 4, 4]);\n' > arm.scad                         # arm along +X, pivot at origin
printf 'rotate([0, 0, 92]) translate([24, -2, 0]) cube([4, 4, 4]);\n' > post.scad      # first touch measured at 83 deg (arm corner sweeps into the post face)
printf 'rotate([0, 0, 150]) translate([24, -2, 0]) cube([4, 4, 4]);\n' > postfar.scad
for f in arm post postfar; do "$OPENSCAD" --backend=Manifold -o $f.stl $f.scad >/dev/null 2>&1 || { echo "render $f failed"; exit 1; }; done
mj() {  # name post stops-json
    echo '{"static": ["'$2'"], "motion": [{"id": "swing", "range_deg": [0, 80], "step_deg": 1, '"$3"'
           "drivers": [{"part": "arm", "type": "revolute", "axis": [0, 0, 1], "origin": [0, 0, 0], "ratio": 1}]}]}' > $1.json; }
fail=0
run() { o=$(python3 "$M" --joints "$1.json" arm.stl "$2.stl" 2>&1); r=$?; }
mj near post '"stops": {"ends": ["high"], "within_deg": 10},'; run near post
[ $r -eq 0 ] && grep -q "stop at the high end: parts meet at t=83.0deg" <<< "$o" || { echo "stopped arm (rc $r): $o"; fail=1; }
mj far postfar '"stops": {"ends": ["high"], "within_deg": 10},'; run far postfar
[ $r -eq 3 ] && grep -q "nothing stops 'swing' within 10.0 deg past its high end (80.0)" <<< "$o" || { echo "free arm passed (rc $r): $o"; fail=1; }
mj both post '"stops": {"ends": ["low", "high"], "within_deg": 10},'; run both post
[ $r -eq 3 ] && grep -q "past its low end (0.0)" <<< "$o" || { echo "missing low stop passed (rc $r): $o"; fail=1; }
mj none postfar ''; run none postfar
[ $r -eq 0 ] || { echo "no stops declared must not check stops (rc $r): $o"; fail=1; }
mj badend post '"stops": {"ends": ["top"], "within_deg": 10},'; run badend post
[ $r -eq 4 ] || { echo "bad stops.ends not usage (rc $r): $o"; fail=1; }
exit $fail
