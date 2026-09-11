#!/usr/bin/env bash
# Proves check_attachment.py passes when the declared attachment point is
# backed by real material (the boss the fastener goes through).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=0
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_attachment.py" --attachments attachments.json part.stl 2>&1)
actual=$?
rm -f part.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "OK"; then
    echo "expected 'OK' in output, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
