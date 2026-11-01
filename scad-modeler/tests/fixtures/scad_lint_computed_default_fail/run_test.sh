#!/usr/bin/env bash
# P2(a) / AC-1 (2026-11-01). INCIDENTS.md 2026-09-04: beam.scad kept `len = 211`
# as a default while the assembly computed 216.5; the shaft rammed 10 mm into the
# node. One caller computes the argument, another omits it and gets the literal.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_scad_lint.py" --project-dir . 2>&1); rc=$?
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
[ "$rc" -eq 3 ] || die "AC-1: exit $rc, want 3"
for w in beam len 211 assembly.scad 'parts/beam.scad:3'; do echo "$out" | grep -q -- "$w" || die "AC-1: output lacks $w"; done
exit 0
