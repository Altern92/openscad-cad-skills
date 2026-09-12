#!/usr/bin/env bash
# check_service_envelope.py exists to force every field to be explicitly
# stated. An UNFILLED copy of the skill's own template is the cleanest
# possible reproduction of exactly that failure -- and it doubles as a guard
# on the template: if a field is ever added to templates/service_envelope.md
# with a pre-filled value, this fixture stops failing and says so.
set -uo pipefail
cp "$SCAD_MODELER_SCRIPTS/../templates/service_envelope.md" envelope.md
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_service_envelope.py" --envelope envelope.md 2>&1)
actual=$?
rm -f envelope.md
if [ "$actual" -ne 1 ]; then
    echo "expected exit 1 on an unfilled template, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -qi "blank\|missing" || {
    echo "expected the failure to name blank fields, got:" >&2; echo "$out" >&2; exit 1; }
exit 0
