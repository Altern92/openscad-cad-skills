#!/usr/bin/env bash
# P26c / AC-22: a screw that clamps a purchased body (servo tab) seats its head on that body; the
# fastener check renders purchased bodies from assembly.scad instead of seeing only printed parts.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"
mkdir -p build/positioned
printf 'difference(){ cube([20,20,20]); translate([10,10,5]) cylinder(d=2.5, h=16, $fn=24); }\n' > block.scad
"$OPENSCAD" --backend=Manifold --render -o build/positioned/block.stl block.scad >/dev/null 2>&1
cat > assembly.scad <<'S'
MODE = is_undef(MODE) ? "assembly" : MODE;
VIT = is_undef(VIT) ? "" : VIT;
module tab() translate([0, 0, 20]) difference() { cube([20, 20, 3]); translate([10, 10, -1]) cylinder(d=3.4, h=5, $fn=24); }
if (MODE == "vit") { if (VIT == "tab") tab(); else assert(false, str("Unknown vitamin: ", VIT)); }
S
fail=0
scr='"fasteners":[{"name":"tab M3","start":[10,10,23],"axis":[0,0,-1],"d":3,"length":12,"thread_from":3,"into":"block"}]'
run() { echo "$1" > fasteners.json; o=$(python3 "$SCAD_MODELER_SCRIPTS/check_fasteners.py" --fasteners fasteners.json 2>&1); r=$?; }
run '{"purchased":{"tab":{"MODE":"vit","VIT":"tab"}},'"$scr"'}'
{ [ $r -eq 0 ] && [ -s build/purchased/tab.stl ] && [ ! -e build/positioned/tab.stl ]; } \
    || { echo "AC-22: screw on a purchased tab failed (rc $r): $o" >&2; fail=1; }
run '{'"$scr"'}'
[ $r -ne 0 ] && grep -q "seats on nothing" <<< "$o" || { echo "AC-22b: no purchased body, still passed (rc $r): $o" >&2; fail=1; }
run '{"purchased":{"tab":{"MODE":"vit","VIT":"nosuch"}},'"$scr"'}'
[ $r -eq 2 ] && grep -q "tab" <<< "$o" || { echo "AC-22c: failed purchased render not rc 2 (rc $r): $o" >&2; fail=1; }
run '{"purchased":{"tab":{"MODE; x":"vit"}},'"$scr"'}'
[ $r -eq 2 ] || { echo "AC-22c: bad -D key accepted (rc $r): $o" >&2; fail=1; }
run '{"purchased":{"tab":{"VIT":["tab"]}},'"$scr"'}'
[ $r -eq 2 ] || { echo "AC-22c: list value accepted (rc $r): $o" >&2; fail=1; }
exit $fail
