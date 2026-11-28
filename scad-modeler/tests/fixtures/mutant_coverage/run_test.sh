#!/usr/bin/env bash
# P1b / AC-10, AC-11 (2026-11-01). 31 of 95 incidents were a checker that said
# PASS, or said nothing, while the defect was there. A fixture only proves a
# checker works if it FAILS when the checker is replaced by a silent `exit 0`.
# tests/mutants.tsv names one such fixture per scripts/check_*.py; this
# fixture proves the table is complete and that every listed fixture kills
# its mutant. P25 / AC-7: and that a reject-everything stub is caught as well.
set -uo pipefail
[ -n "${SCAD_MUTANT_INNER:-}" ] && exit 0
T="$SCAD_MODELER_SCRIPTS/../tests"; TSV="$T/mutants.tsv"
fail=0
for c in "$SCAD_MODELER_SCRIPTS"/check_*.py; do
    n=$(basename "$c" .py)
    grep -q "^$n	" "$TSV" || { echo "AC-10: $n has no mutant fixture in mutants.tsv" >&2; fail=1; }
done
# P28 (2026-11-28): and at least one semantic row (a plausible logic error, tests/semantic_mutants.tsv) per checker;
# the semantic_mutants fixture proves each row is KILLED
for c in "$SCAD_MODELER_SCRIPTS"/check_*.py "$SCAD_MODELER_SCRIPTS"/motion_sweep.py; do
    n=$(basename "$c" .py)
    awk -F'\t' -v n="$n" '!/^#/ && $2 == n {f=1} END {exit !f}' "$T/semantic_mutants.tsv" \
        || { echo "P28: $n has no semantic mutant in semantic_mutants.tsv -- Hint: add a row that breaks one real check" >&2; fail=1; }
done
[ "$fail" -eq 0 ] || exit 1
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
grep -v '^#' "$TSV" | while IFS=$'\t' read -r checker fixture pass_fx; do
    [ -n "$checker" ] || continue
    [ -f "$T/fixtures/$fixture/run_test.sh" ] || { echo "AC-10: $checker -> $fixture: no such fixture" >&2; echo x >> "$tmp/bad"; continue; }
    rm -rf "$tmp/s"; cp -R "$SCAD_MODELER_SCRIPTS" "$tmp/s"
    printf 'import sys\nsys.exit(0)\n' > "$tmp/s/$checker.py"
    if (cd "$T/fixtures/$fixture" && SCAD_MUTANT_INNER=1 SCAD_MODELER_SCRIPTS="$tmp/s" bash run_test.sh >/dev/null 2>&1); then
        echo "AC-11: $fixture still PASSES with $checker stubbed to exit 0 -- it does not test the checker" >&2
        echo x >> "$tmp/bad"
    fi
    # P25 / AC-7: a checker that rejects EVERYTHING must be caught too (positive witness), once per checker
    grep -qx "$checker" "$tmp/seen" 2>/dev/null && continue; echo "$checker" >> "$tmp/seen"
    pf=${pass_fx:-$fixture}
    [ -f "$T/fixtures/$pf/run_test.sh" ] || { echo "AC-7: $checker -> $pf: no such fixture" >&2; echo x >> "$tmp/bad"; continue; }
    printf 'import sys\nprint("FAIL: stub rejects everything")\nsys.exit(1)\n' > "$tmp/s/$checker.py"
    if (cd "$T/fixtures/$pf" && SCAD_MUTANT_INNER=1 SCAD_MODELER_SCRIPTS="$tmp/s" bash run_test.sh >/dev/null 2>&1); then
        echo "AC-7: $pf still PASSES with $checker rejecting everything -- name a PASS fixture in column 3" >&2
        echo x >> "$tmp/bad"
    fi
done
[ ! -s "$tmp/bad" ]
