#!/usr/bin/env bash
# Negative witness for doctor.py: when a dependency is unavailable it must SAY
# SO, name the consequence, and exit non-zero -- not report a clean bill of
# health.
#
# The existing fixture (doctor_machine_report) asserts only that doctor runs and
# emits JSON. A tool that always answers "everything is fine" passes that, which
# is the constant-assertion vacuity class: an assertion that cannot fail is not
# an assertion.
#
# The break is forced through PYTHONPATH rather than by emptying PATH, so the
# result does not depend on which interpreter or which OpenSCAD build this
# machine happens to have.
set -uo pipefail

scratch=$(mktemp -d)
# A module named trimesh that always raises, shadowing the real one.
cat > "$scratch/trimesh.py" <<'PY'
raise ImportError("forced missing for the doctor fixture")
PY

run() {  # <extra PYTHONPATH>
    PYTHONPATH="$1" python3 "$SCAD_MODELER_SCRIPTS/doctor.py" 2>&1
}

healthy=$(run "")
healthy_code=$?
broken=$(PYTHONPATH="$scratch" python3 "$SCAD_MODELER_SCRIPTS/doctor.py" 2>&1)
broken_code=$?

rm -rf "$scratch"

# The healthy run may legitimately be 0 (everything present) or 2 (this machine
# is genuinely missing something). What it must never do is report a MISSING
# dependency it does not actually have.
if echo "$healthy" | grep -q "MISSING  trimesh"; then
    echo "the unmodified run reports trimesh missing -- this fixture cannot tell the two states apart" >&2
    exit 1
fi

if [ "$broken_code" -eq 0 ]; then
    echo "doctor exited 0 with a dependency deliberately broken -- it cannot fail" >&2
    echo "$broken" >&2
    exit 1
fi
echo "$broken" | grep -q "MISSING  trimesh" || {
    echo "expected trimesh to be reported MISSING, got:" >&2
    echo "$broken" >&2
    exit 1; }
# The consequence matters as much as the name: "MISSING trimesh" alone does not
# tell a reader which checks just stopped being runnable.
echo "$broken" | grep -A1 "MISSING  trimesh" | grep -qi "STL-side check" || {
    echo "expected the missing dependency to name what it breaks, got:" >&2
    echo "$broken" | grep -A1 "trimesh" >&2
    exit 1; }

if [ "$healthy_code" -ne "$broken_code" ]; then
    exit 0
fi
echo "healthy and broken runs returned the same code ($healthy_code) -- the degradation signal is not distinguishing anything" >&2
exit 1
