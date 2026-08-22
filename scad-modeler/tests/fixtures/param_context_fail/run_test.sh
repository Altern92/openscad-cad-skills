#!/usr/bin/env bash
# Proves check_param_context.py catches the real axle_d incident shape:
# a shared parameter with 2 hardware-fit contexts where only one was
# ever actually verified.
set -uo pipefail
EXPECTED_EXIT=3
python3 "$SCAD_MODELER_SCRIPTS/check_param_context.py" --project-dir .
actual=$?
if [ "$actual" -eq "$EXPECTED_EXIT" ]; then
    exit 0
fi
echo "expected exit $EXPECTED_EXIT, got $actual" >&2
exit 1
