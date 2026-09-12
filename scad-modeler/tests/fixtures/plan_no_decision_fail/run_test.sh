#!/usr/bin/env bash
# check_plan.py's core claim is that comparing options without choosing one is
# not planning. An unfilled copy of the template has two architecture options
# and no Confirmed Decision row -- exactly that state.
set -uo pipefail
cp "$SCAD_MODELER_SCRIPTS/../templates/plan.md" plan.md
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_plan.py" --plan plan.md 2>&1)
actual=$?
rm -f plan.md
if [ "$actual" -ne 1 ]; then
    echo "expected exit 1 on a plan with no Confirmed Decision, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -q "Decision" || {
    echo "expected the failure to name the missing Decision row, got:" >&2; echo "$out" >&2; exit 1; }
exit 0
