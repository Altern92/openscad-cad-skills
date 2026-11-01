#!/usr/bin/env bash
# P14 / AC-6, AC-7 (2026-11-01): the state file records which library versions a
# verdict was made with, and a preflight stopped by a WARNING says so instead of
# blaming an assert() (the gearbox run printed "an assert() failed" for an
# unknown function).
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
mkdir -p "$tmp/lib/BOSL2" "$tmp/ok" "$tmp/warn"
echo '' > "$tmp/lib/BOSL2/std.scad"
echo 'BOSL_VERSION = [2,0,750];' > "$tmp/lib/BOSL2/version.scad"
export OPENSCADPATH="$tmp/lib"
printf 'include <BOSL2/std.scad>\ncube([10,10,10]);\n' > "$tmp/ok/block.scad"
out=$(cd "$tmp/ok" && bash "$V" block.scad 2>&1); rc=$?
[ "$rc" -eq 0 ] || die "AC-6: exit $rc"
grep -q '"libs":{"BOSL2":"2.0.750"}' "$tmp/ok/build/.validation_state.json" || { out=$(cat "$tmp/ok/build/.validation_state.json"); die "AC-6: state lacks libs"; }

printf 'w = no_such_function(3);\n' > "$tmp/warn/params.scad"
printf 'cube(5);\n' > "$tmp/warn/block.scad"
out=$(cd "$tmp/warn" && bash "$V" block.scad 2>&1)
echo "$out" | grep -q '^CHECK_RESULT analytic_bounds=FAIL' || die "AC-7: no analytic_bounds=FAIL"
echo "$out" | grep -q 'warning under --hardwarnings' || die "AC-7: cause not named as a warning"
echo "$out" | grep -q "WARNING: Ignoring unknown function 'no_such_function'" || die "AC-7: WARNING line not shown"
echo "$out" | grep -q 'an assert() in params.scad failed' && die "AC-7: still blames an assert()"
exit 0
