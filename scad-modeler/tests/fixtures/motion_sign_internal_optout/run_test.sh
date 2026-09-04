#!/usr/bin/env bash
# Proves "internal_gear_mesh" (not "gear_mesh") opts a same-sign pair out
# of the sign check -- a genuine internal/planetary mesh legitimately
# turns same-direction, and the check is deliberately scoped to
# joint_type == "gear_mesh" only.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/motion_sweep.py" --joints joints.json fake_a.stl fake_b.stl 2>&1)
actual=$?
if echo "$out" | grep -q "SAME-sign ratio\|ratio 0"; then
    echo "sign check incorrectly fired on an internal_gear_mesh-declared pair:" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "cannot load fake_a.stl"; then
    echo "expected to fail past the sign check on the fake STL path, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
