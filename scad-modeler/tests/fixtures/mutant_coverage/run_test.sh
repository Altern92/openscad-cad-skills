#!/usr/bin/env bash
# P1b / AC-10, AC-11 (2026-11-01). 31 of 95 incidents were a checker that said
# PASS, or said nothing, while the defect was there. A fixture only proves a
# checker works if it FAILS when the checker is replaced by a silent `exit 0`.
# tests/mutants.tsv names one such fixture per scripts/check_*.py; this
# fixture proves the table is complete and that every listed fixture kills
# its mutant.
set -uo pipefail
[ -n "${SCAD_MUTANT_INNER:-}" ] && exit 0
T="$SCAD_MODELER_SCRIPTS/../tests"; TSV="$T/mutants.tsv"
fail=0
for c in "$SCAD_MODELER_SCRIPTS"/check_*.py; do
    n=$(basename "$c" .py)
    grep -q "^$n	" "$TSV" || { echo "AC-10: $n has no mutant fixture in mutants.tsv" >&2; fail=1; }
done
[ "$fail" -eq 0 ] || exit 1
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
grep -v '^#' "$TSV" | while IFS=$'\t' read -r checker fixture; do
    [ -n "$checker" ] || continue
    [ -f "$T/fixtures/$fixture/run_test.sh" ] || { echo "AC-10: $checker -> $fixture: no such fixture" >&2; echo x >> "$tmp/bad"; continue; }
    rm -rf "$tmp/s"; cp -R "$SCAD_MODELER_SCRIPTS" "$tmp/s"
    printf 'import sys\nsys.exit(0)\n' > "$tmp/s/$checker.py"
    if (cd "$T/fixtures/$fixture" && SCAD_MUTANT_INNER=1 SCAD_MODELER_SCRIPTS="$tmp/s" bash run_test.sh >/dev/null 2>&1); then
        echo "AC-11: $fixture still PASSES with $checker stubbed to exit 0 -- it does not test the checker" >&2
        echo x >> "$tmp/bad"
    fi
done
[ ! -s "$tmp/bad" ]
