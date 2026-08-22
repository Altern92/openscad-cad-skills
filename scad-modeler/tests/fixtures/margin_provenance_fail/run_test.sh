#!/usr/bin/env bash
# Proves check_margin_provenance.py catches the real jackshaft_bearing_
# wall_at_diff incident shape: an assert whose formula omits clearance
# terms the geometry applies to the assert's own dependencies.
set -uo pipefail
EXPECTED_EXIT=3
python3 "$SCAD_MODELER_SCRIPTS/check_margin_provenance.py" --scad params.scad --parts-dir parts
actual=$?
if [ "$actual" -eq "$EXPECTED_EXIT" ]; then
    exit 0
fi
echo "expected exit $EXPECTED_EXIT, got $actual" >&2
exit 1
