#!/usr/bin/env bash
# Proves a correctly opposite-signed gear_mesh pair is NOT flagged by the
# sign check -- it must get past the sign gate and fail LATER, for a
# different, expected reason (the STL paths are fake), not at the sign
# check itself. Confirms the check doesn't false-positive on the correct
# case, matching the real gear_reduction example's own joints.json shape.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/motion_sweep.py" --joints joints.json fake_a.stl fake_b.stl 2>&1)
actual=$?
if echo "$out" | grep -q "SAME-sign ratio\|ratio 0"; then
    echo "sign check incorrectly flagged a correctly-signed pair:" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "cannot load fake_a.stl"; then
    echo "expected to fail past the sign check on the fake STL path, got:" >&2
    echo "$out" >&2
    exit 1
fi
exit 0
