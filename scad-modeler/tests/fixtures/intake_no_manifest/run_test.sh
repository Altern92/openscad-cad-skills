#!/usr/bin/env bash
# check_intake.py's exit code is NOT 1 for a missing manifest -- it is 2, and 3
# for a manifest that fails. That split is load-bearing: validate_scad.sh must
# tell "Stage 0 never produced its output" (a process failure) from "the spec
# is wrong" (a content failure). This fixture pins both numbers, and pins the
# runner directory so no stray manifest in it can make the test pass by
# accident.
set -uo pipefail
scratch=$(mktemp -d)
( cd "$scratch" && python3 "$SCAD_MODELER_SCRIPTS/check_intake.py" > out 2>&1 )
actual=$?
out=$(cat "$scratch/out")
rm -rf "$scratch"
if [ "$actual" -ne 2 ]; then
    echo "expected exit 2 for a missing manifest, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -qi "manifest" || {
    echo "expected the message to name the missing manifest, got:" >&2; echo "$out" >&2; exit 1; }
exit 0
