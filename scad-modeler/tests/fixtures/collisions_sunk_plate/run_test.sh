#!/usr/bin/env bash
# P28 (2026-11-27): a 0.5 mm plate sunk 10 mm inside a 30 mm block was reported as depth 0.5
# (the plate thickness). Penetration = smallest translation that separates the parts:
# 10.5 mm (down, out of the block). A plate overlapping the top face by 1 mm stays 1.0.
set -uo pipefail
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
C="$SCAD_MODELER_SCRIPTS/check_collisions.py"
r() { printf '%s\n' "$2" > "$tmp/$1.scad"; openscad -q -o "$tmp/$1.stl" "$tmp/$1.scad"; }
r block 'cube([30,30,30]);'
r deep 'translate([5,5,10]) cube([20,20,0.5]);'
r over 'translate([5,5,29]) cube([20,20,2]);'
chk() { out=$(python3 "$C" "$tmp/block.stl" "$tmp/$1.stl" 2>&1); rc=$?
  [ "$rc" -eq 3 ] || { echo "$1: exit $rc, want 3" >&2; echo "$out" >&2; exit 1; }
  echo "$out" | grep -Eq "penetration depth (is )?$2 mm" || { echo "$1: depth not $2" >&2; echo "$out" >&2; exit 1; }; }
chk deep '10\.[45][0-9]*'
chk over '(0\.9[0-9]*|1\.0[0-9]*)'
exit 0
