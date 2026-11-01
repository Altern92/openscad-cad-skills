#!/usr/bin/env bash
# P14 / AC-1..AC-5 (2026-11-01). BOSL2 2.0.782 dropped worm_gear_thickness(); the
# steering gearbox rendered a wrong output_gear with no error. env_gate checked
# that BOSL2 exists, never which one. libs.lock pins it.
set -uo pipefail
G="$SCAD_MODELER_SCRIPTS/env_gate.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
mkdir -p "$tmp/lib/BOSL2" "$tmp/lib/NopSCADlib" "$tmp/p"
echo '' > "$tmp/lib/BOSL2/std.scad"
echo 'BOSL_VERSION = [2,0,750];' > "$tmp/lib/BOSL2/version.scad"
echo 'module nop() {}' > "$tmp/lib/NopSCADlib/core.scad"
printf 'include <BOSL2/std.scad>\nuse <NopSCADlib/core.scad>\ncube(1);\n' > "$tmp/p/part.scad"
export OPENSCADPATH="$tmp/lib"
gate() { out=$(python3 "$G" --project-dir "$tmp/p" "$@" 2>&1); rc=$?; }

gate; [ "$rc" -eq 0 ] || die "AC-4: no lock should pass, got $rc"
gate --write-lock; [ "$rc" -eq 0 ] || die "AC-5: --write-lock exit $rc"
grep -qx 'BOSL2 2.0.750' "$tmp/p/libs.lock" || { out=$(cat "$tmp/p/libs.lock"); die "AC-5: no 'BOSL2 2.0.750' line"; }
grep -qE '^NopSCADlib tree:[0-9a-f]{12}$' "$tmp/p/libs.lock" || { out=$(cat "$tmp/p/libs.lock"); die "AC-5: no NopSCADlib tree line"; }
gate; [ "$rc" -eq 0 ] || die "AC-1: matching lock should pass, got $rc"

echo 'BOSL_VERSION = [2,0,1];' > "$tmp/lib/BOSL2/version.scad"
gate; [ "$rc" -eq 5 ] || die "AC-2: version mismatch should exit 5, got $rc"
for w in 2.0.750 2.0.1 "$tmp/lib/BOSL2"; do echo "$out" | grep -qF -- "$w" || die "AC-2: message lacks $w"; done

echo 'BOSL_VERSION = [2,0,750];' > "$tmp/lib/BOSL2/version.scad"
echo 'module nop() { cube(2); }' > "$tmp/lib/NopSCADlib/core.scad"
gate; [ "$rc" -eq 5 ] || die "AC-3: tree mismatch should exit 5, got $rc"
echo "$out" | grep -q NopSCADlib || die "AC-3: message lacks NopSCADlib"
exit 0
