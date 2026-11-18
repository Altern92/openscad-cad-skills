#!/usr/bin/env bash
# P25 / AC-8 (2026-11-18): the exit-0 stub (mutant_coverage) only proves a fixture notices a silent checker.
# tests/semantic_mutants.tsv holds plausible logic errors (wall check dropped, depth L instead of L + 1,
# no Z strength, angle and DOF slack, head room ignored, limit direction lost); every one must be KILLED
# by an assertion. bad.tsv proves the runner can say NOT_APPLICABLE, CRASH and SURVIVED.
set -uo pipefail
[ -n "${SCAD_MUTANT_INNER:-}" ] && exit 0
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
R="$here/../../tools/semantic_mutants.py"; F="$here/.."
fail=0
o=$(python3 "$R" "$SCAD_MODELER_SCRIPTS" "$F" "$here/../../semantic_mutants.tsv"); r=$?
echo "$o"
[ "$r" -eq 0 ] || { echo "AC-8: a semantic mutant was not killed" >&2; fail=1; }
o=$(python3 "$R" "$SCAD_MODELER_SCRIPTS" "$F" "$here/bad.tsv"); r=$?
[ "$r" -eq 1 ] || { echo "AC-8: bad catalogue must exit 1" >&2; fail=1; }
for w in "NOT_APPLICABLE  stale" "CRASH           crash" "SURVIVED        harmless"; do
    grep -qF <<< "$o" "$w" || { echo "AC-8: runner did not report '$w': $o" >&2; fail=1; }
done
exit $fail
