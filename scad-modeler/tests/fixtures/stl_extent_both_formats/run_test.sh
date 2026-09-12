#!/usr/bin/env bash
# stl_extent.py must read BOTH STL encodings, because OpenSCAD chooses.
#
# This exists because the first version of the tripwire that uses it parsed the
# file as binary and assumed a 4-byte triangle count at offset 80. OpenSCAD
# writes ASCII STL by default ("solid OpenSCAD_Model"), so the parser read the
# ASCII body as a count (943009847), raised, and the shell call -- wrapped in
# "|| echo 0" -- turned that into a silent "nothing is suspicious". The tripwire
# then detected nothing at all, and the only reason it was caught is that the
# case it was built for was re-measured: server_rack_modular_v4 again reported
# all 136 collision pairs at an identical 170.000mm (INCIDENTS.md, 2026-09-12).
#
# The negative half matters as much as the positive: a tool that reports every
# file as unreadable would also "fail loudly" and be useless.
set -uo pipefail

work=$(mktemp -d)
cd "$work"

# 1. ASCII, as OpenSCAD writes it by default
"${OPENSCAD:-openscad}" --backend=Manifold -o ascii.stl -D 'x=10' /dev/stdin <<'SCAD' 2>/dev/null ||     printf 'cube([10, 20, 30]);\n' > m.scad
SCAD
if [ ! -s ascii.stl ]; then
    printf 'cube([10, 20, 30]);\n' > m.scad
    "${OPENSCAD:-openscad}" --backend=Manifold -o ascii.stl m.scad >/dev/null 2>&1
fi
head -c 5 ascii.stl | grep -q "solid" || {
    echo "fixture precondition failed: OpenSCAD did not write an ASCII STL" >&2
    rm -rf "$work"; exit 1; }

# 2. the same mesh, converted to binary by trimesh
python3 - <<'PY'
import trimesh
m = trimesh.load("ascii.stl", force="mesh")
m.export("binary.stl")
PY
head -c 5 binary.stl | grep -q "solid" && {
    echo "fixture precondition failed: the 'binary' file is still ASCII" >&2
    rm -rf "$work"; exit 1; }

a=$(python3 "$SCAD_MODELER_SCRIPTS/stl_extent.py" ascii.stl) || {
    echo "stl_extent.py failed on an ASCII STL" >&2; rm -rf "$work"; exit 1; }
b=$(python3 "$SCAD_MODELER_SCRIPTS/stl_extent.py" binary.stl) || {
    echo "stl_extent.py failed on a binary STL" >&2; rm -rf "$work"; exit 1; }

# Both must report 10 x 20 x 30, whichever way the file was encoded.
for got in "$a" "$b"; do
    set -- $got
    if [ "$1" != "10.000000" ] || [ "$2" != "20.000000" ] || [ "$3" != "30.000000" ]; then
        echo "expected 10 20 30, got: $got" >&2
        rm -rf "$work"; exit 1
    fi
done

# 3. garbage in must be an error, never a number
printf 'not an stl at all\n' > junk.stl
if python3 "$SCAD_MODELER_SCRIPTS/stl_extent.py" junk.stl >/dev/null 2>&1; then
    echo "stl_extent.py returned success on a non-STL file" >&2
    rm -rf "$work"; exit 1
fi

rm -rf "$work"
exit 0
