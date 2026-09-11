#!/usr/bin/env bash
# Proves check_bore_reachability.py fails a bore whose path from outside to the
# seat runs through solid material -- the sealed-cavity failure that every other
# check in the chain reports clean.
# Direct reproduction of INCIDENTS.md 2026-08-19 (bearing bores).
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=3
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_bore_reachability.py" --bores bores.json part.stl 2>&1)
actual=$?
rm -f part.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -qi "block\|sealed\|FAIL"; then
    echo "expected a blocked/sealed report, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
