#!/usr/bin/env bash
set -uo pipefail
EXPECTED_EXIT=0
python3 "$SCAD_MODELER_SCRIPTS/check_param_context.py" --project-dir .
actual=$?
if [ "$actual" -eq "$EXPECTED_EXIT" ]; then
    exit 0
fi
echo "expected exit $EXPECTED_EXIT, got $actual" >&2
exit 1
