#!/usr/bin/env bash
# Proves an undeclared, exactly-touching pair (Phase-2 Pattern 2) is
# classified CANDIDATE INTENTIONAL TOUCH with a printed joints.json stub,
# not a bare UNINTENDED INTERFERENCE -- still a FAIL either way.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=3
"$OPENSCAD" --backend=Manifold --render -o box_a.stl box_a.scad >/dev/null 2>&1
"$OPENSCAD" --backend=Manifold --render -o box_b.stl box_b.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_collisions.py" box_a.stl box_b.stl)
actual=$?
rm -f box_a.stl box_b.stl
if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    exit 1
fi
if ! echo "$out" | grep -q "CANDIDATE INTENTIONAL TOUCH"; then
    echo "expected 'CANDIDATE INTENTIONAL TOUCH' in output, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
