#!/usr/bin/env bash
# Proves check_attachment.py fails when a declared attachment point has no
# material -- the "part shipped with no fastening features" failure.
# Direct reproduction of INCIDENTS.md 2026-09-11 (side panels, rack v8).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=3
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_attachment.py" --attachments attachments.json part.stl 2>&1)
actual=$?
rm -f part.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "no material"; then
    echo "expected 'no material' in output, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
