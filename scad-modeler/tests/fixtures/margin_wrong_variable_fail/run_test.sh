#!/usr/bin/env bash
# Proves check_margin_provenance.py's second detection mode (wrong-
# variable-family) catches the real nas_deck_v3 incident shape: geometry
# uses a new local variable, but the assert meant to guard it still
# checks an older, same-family sibling.
set -uo pipefail
EXPECTED_EXIT=3
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_margin_provenance.py" --scad params.scad --parts-dir parts)
actual=$?
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "_deck_socket_depth.*no assert"; then
    echo "expected a wrong-variable-family message about _deck_socket_depth, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
