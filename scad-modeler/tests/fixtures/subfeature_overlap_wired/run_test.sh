#!/usr/bin/env bash
# check_subfeature_overlap.py was written and tested but NEVER FED: it needs the
# sub-features exported SOLO, and nothing in the skill produced such exports, so
# it reported SKIP in every project (0 of 11 declared the input). This fixture
# pins the two halves of the wiring now that it exists:
#
#   1. no declaration -> SKIP, naming what would turn it on
#   2. declaration    -> the solo renders actually happen and a real 180mm3
#      overlap FAILS the run
#
# Run against validate_scad.sh, not the checker, because the missing piece was
# the plumbing rather than the check.
set -uo pipefail

scratch=$(mktemp -d)
mkdir -p "$scratch/parts"
cp part.scad "$scratch/parts/demo.scad"
printf '%s\n' '$fa = 2; $fs = 0.3;' > "$scratch/params.scad"

# --- 1: declaration present -> FAIL with the overlap reported --------------
( cd "$scratch" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all > out 2>&1 )
out=$(cat "$scratch/out")

echo "$out" | grep -q "UNINTENDED SUB-FEATURE OVERLAP" || {
    echo "the overlap was not reported at all:" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q "CHECK_RESULT subfeature_overlap=FAIL" || {
    echo "expected subfeature_overlap=FAIL:" >&2; echo "$out" >&2; exit 1; }
n=$(echo "$out" | grep -c "^CHECK_RESULT subfeature_overlap")
if [ "$n" -ne 1 ]; then
    echo "expected exactly ONE subfeature_overlap line, got $n:" >&2
    echo "$out" | grep "subfeature_overlap" >&2; exit 1
fi

# --- 2: no declaration -> SKIP, and it says what it needs ------------------
sed -i.bak '/SUBFEATURES:/d' "$scratch/parts/demo.scad"
( cd "$scratch" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all > out2 2>&1 )
out2=$(cat "$scratch/out2")
echo "$out2" | grep -q "CHECK_RESULT subfeature_overlap=SKIP" || {
    echo "expected SKIP without a declaration:" >&2; echo "$out2" >&2; exit 1; }
echo "$out2" | grep -qi "templates/part_template.scad" || {
    echo "the SKIP must name how to turn the check on, got:" >&2
    echo "$out2" | grep -A1 "subfeature_overlap" >&2
    exit 1; }

rm -rf "$scratch"
exit 0
