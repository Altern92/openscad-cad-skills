#!/usr/bin/env bash
# P2(b) / AC-3 (2026-11-01). INCIDENTS.md 2026-08-23: unit_1U = 44.5 instead of
# EIA-310's 44.45 put 0.05 mm of error into every rack module.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_scad_lint.py" --project-dir . 2>&1); rc=$?
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }
[ "$rc" -eq 3 ] || die "AC-3: exit $rc, want 3"
echo "$out" | grep -q 'params.scad:2' || die "AC-3: line 2 not named"
echo "$out" | grep -q 'params.scad:3' || die "AC-3: line 3 (rack_u) not named"
echo "$out" | grep -q '44.45' || die "AC-3: exact value not named"
exit 0
