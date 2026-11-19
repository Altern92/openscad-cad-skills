#!/usr/bin/env bash
# P27 (Fable calculation audit) on check_fasteners.py: AC-6 instances add to the STL list, AC-7 head_h 0
# crossing, AC-8 entry without start, AC-9 open mesh, AC-10 oversized pilot, AC-11 covered hole under a big lid,
# AC-16 instance render re-made when an imported STL changes
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}; F="$SCAD_MODELER_SCRIPTS/check_fasteners.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"
fail=0
run() { o=$(python3 "$F" --fasteners "$1" 2>&1); r=$?; }
asm() { cat > assembly.scad <<S
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
\$fn = 64;
module plate() difference(){ translate([-20,-20,0]) cube([40,40,5]); translate([0,0,-1]) cylinder(d=4.4,h=10);}
module base() difference(){ translate([-20,-20,-20]) cube([40,40,20]); translate([0,0,-30]) cylinder(d=$1,h=40);}
module cover() translate([-20,-20,5]) cube([40,40,4]);
if (PART=="plate") plate();
if (PART=="base") base();
if (PART=="cover") cover();
S
rm -rf build; mkdir -p build/positioned
for p in plate base cover; do "$OPENSCAD" --backend=Manifold -o build/positioned/$p.stl -D "PART=\"$p\"" assembly.scad >/dev/null 2>&1; done; }
scr='{"name":"s0","start":[0,0,5],"axis":[0,0,-1],"d":4,"length":16,"head_d":7,"head_h":3,"into":"base","thread_from":5}'
asm 3.3
echo "[$scr]" > plain.json; run plain.json
[ $r -ne 0 ] && grep -q "head blocked" <<< "$o" || { echo "baseline: cover must block the head: $o" >&2; fail=1; }
echo '{"instances":["plate","base"],"fasteners":['"$scr"']}' > inst.json; run inst.json
[ $r -ne 0 ] && grep -q "head blocked" <<< "$o" || { echo "AC-6: instances dropped the cover (rc $r): $o" >&2; fail=1; }
rm build/positioned/cover.stl
run plain.json; [ $r -eq 0 ] || { echo "baseline: screw without the cover should pass: $o" >&2; fail=1; }
s1='{"name":"s1","start":[3,0,5],"axis":[0,0,-1],"d":4,"length":16,"head_d":7,"head_h":0,"into":"base","thread_from":5}'
echo "[$scr,$s1]" > h0.json; run h0.json
grep -q "fasteners cross" <<< "$o" || { echo "AC-7: head_h 0 hid a crossing: $o" >&2; fail=1; }
echo '[{"name":"typo","strat":[0,0,5],"axis":[0,0,-1],"d":4,"length":16}]' > nostart.json; run nostart.json
[ $r -eq 2 ] && grep -q "typo" <<< "$o" || { echo "AC-8: entry without start not bad input (rc $r): $o" >&2; fail=1; }
python3 -c "import trimesh; m=trimesh.load('build/positioned/plate.stl'); m.update_faces([i for i in range(len(m.faces)) if i]); m.export('build/positioned/plate.stl')"
run plain.json; [ $r -eq 2 ] && grep -q "watertight" <<< "$o" || { echo "AC-9: open mesh accepted (rc $r): $o" >&2; fail=1; }
asm 3.9; rm build/positioned/cover.stl
run plain.json; [ $r -ne 0 ] && grep -q "no thread material" <<< "$o" || { echo "AC-10: 3.9 mm pilot for M4 passed: $o" >&2; fail=1; }
# P27b: the bite follows the pitch -- M10x1 into its ISO 9.0 mm tap drill is fine (0.44 d failed it)
asm 9.0; rm build/positioned/cover.stl
echo '[{"name":"m10f","start":[0,0,5],"axis":[0,0,-1],"d":10,"pitch":1.0,"length":16,"head_d":16,"head_h":6,"into":"base","thread_from":5}]' > m10.json
sed -i '' 's/cylinder(d=4.4,h=10)/cylinder(d=10.5,h=10)/' assembly.scad
"$OPENSCAD" --backend=Manifold -o build/positioned/plate.stl -D 'PART="plate"' assembly.scad >/dev/null 2>&1
run m10.json; [ $r -eq 0 ] || { echo "P27b: M10x1 into its 9.0 mm tap drill failed: $o" >&2; fail=1; }
# P27b: OpenSCAD's touching cubes give 4-face edges -- closed, not leaky
asm 3.3; rm build/positioned/cover.stl
printf 'translate([100,0,0]) { cube(10); translate([10,10,0]) cube(10); }\n' > edge.scad   # two cubes sharing an edge
"$OPENSCAD" --backend=Manifold -o build/positioned/edge.stl edge.scad >/dev/null 2>&1
python3 -c "import trimesh,sys; sys.exit(0 if not trimesh.load('build/positioned/edge.stl').is_watertight else 1)" \
    || echo "note: this OpenSCAD wrote no 4-face edge; the case below proves nothing here" >&2
o=$(python3 "$F" --fasteners plain.json 2>&1); r=$?
[ $r -eq 0 ] || { echo "P27b: 4-face edges (cubes sharing an edge) rejected (rc $r): $o" >&2; fail=1; }
# AC-11: lids of 60 / 150 / 300 mm cover an unused Ø4 host hole at x = +20
for L in 60 150 300; do
    rm -rf build; mkdir -p build/positioned
    printf 'difference(){ translate([-%s,-%s,0]) cube([%s,%s,10]); translate([-20,0,-1]) cylinder(d=3.3,h=12,$fn=32); translate([20,0,-1]) cylinder(d=4,h=12,$fn=32);}\n' \
        $((L/2+10)) $((L/2+10)) $((L+20)) $((L+20)) > host.scad
    printf 'difference(){ translate([-%s,-%s,10]) cube([%s,%s,3]); translate([-20,0,9]) cylinder(d=4.4,h=5,$fn=32);}\n' $((L/2)) $((L/2)) $L $L > lid.scad
    "$OPENSCAD" --backend=Manifold -o build/positioned/host.stl host.scad >/dev/null 2>&1
    "$OPENSCAD" --backend=Manifold -o build/positioned/lid.stl lid.scad >/dev/null 2>&1
    echo '{"mounts":[{"part":"lid","on":"host"}],"fasteners":[{"name":"s0","start":[-20,0,13],"axis":[0,0,-1],"d":4,"length":12,"head_d":7,"head_h":3,"into":"host","thread_from":3}]}' > m.json
    run m.json; [ $r -ne 0 ] && grep -q "covers host hole" <<< "$o" || { echo "AC-11: $L mm lid hid the covered hole: $o" >&2; fail=1; }
done
# AC-16: an instance that imports an STL re-renders when the STL changes
rm -rf build; mkdir -p build/positioned
mk() { python3 -c "import trimesh; m=trimesh.creation.box(extents=[40,40,5]); m.apply_translation([20,20,2.5+$1]); m.export('slab.stl')"; }
mk 0
cat > assembly.scad <<'S'
PART = is_undef(PART) ? "" : PART;
if (PART == "plate") translate([-20, -20, 0]) difference() { import("slab.stl"); translate([20, 20, -1]) cylinder(d=4.4, h=10, $fn=32); }
if (PART == "base") difference() { translate([-20, -20, -20]) cube([40, 40, 20]); translate([0, 0, -30]) cylinder(d=3.3, h=40, $fn=32); }
S
echo '{"instances":["plate","base"],"fasteners":['"$scr"']}' > inst.json; run inst.json
[ $r -eq 0 ] || { echo "AC-16 baseline: imported plate should pass: $o" >&2; fail=1; }
sleep 1; mk 30   # only the imported STL changes, no .scad is touched
run inst.json; [ $r -ne 0 ] || { echo "AC-16: stale instance render after the imported STL moved: $o" >&2; fail=1; }
exit $fail
