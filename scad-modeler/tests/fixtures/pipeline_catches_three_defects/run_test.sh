#!/usr/bin/env bash
# END-TO-END: three real defects, each one a documented incident, driven through
# the WHOLE pipeline rather than through a checker in isolation.
#
# Every other fixture here tests one script's exit code. This one exists because
# "the checker works" and "the skill works" are different claims: a checker can
# be perfect and still never be called. That exact gap produced two real bugs on
# 2026-09-12 -- check_subfeature_overlap.py had been written, tested and NEVER
# FED, and check_dimensions.py ran on every project without emitting a result
# anyone could see.
#
# So this asserts on what validate_scad.sh REPORTS, not on what a script returns.
set -uo pipefail

scratch=$(mktemp -d)
mkdir -p "$scratch/parts"
cp parts/*.scad "$scratch/parts/"
printf '%s\n' '$fa = 2; $fs = 0.3;' 'panel_t = 3;' 'post_d = 18;' > "$scratch/params.scad"

( cd "$scratch" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all > out 2>&1 )
code=$?
out=$(cat "$scratch/out")
rm -rf "$scratch"

fail=0
check() {  # <description> <grep pattern>
    if echo "$out" | grep -qE "$2"; then
        echo "  seen: $1"
    else
        echo "  MISSED: $1 (no line matching /$2/)" >&2
        fail=1
    fi
}

check "defect 1, disconnected bodies"       "has 2 disconnected bodies"
check "defect 2, wrong bbox"                "bbox mismatch"
check "defect 3, overlap inside one union"  "UNINTENDED SUB-FEATURE OVERLAP"

# The verdicts, not just the detail lines -- a detail line with no CHECK_RESULT
# is exactly the silent gap this fixture exists to prevent.
check "connectivity verdict"        "^CHECK_RESULT connectivity=FAIL"
check "dimensions verdict"          "^CHECK_RESULT dimensions=FAIL"
check "subfeature_overlap verdict"  "^CHECK_RESULT subfeature_overlap=FAIL"

# Every check must still declare itself, pass or skip.
n=$(echo "$out" | grep -c "^CHECK_RESULT")
if [ "$n" -lt 15 ]; then
    echo "  MISSED: only $n CHECK_RESULT lines -- checks went silent" >&2
    fail=1
fi
echo "$out" | grep -q "COVERAGE:" || {
    echo "  MISSED: no COVERAGE line" >&2; fail=1; }

if [ "$code" -eq 0 ]; then
    echo "  the run exited 0 despite three real defects" >&2
    fail=1
fi

[ "$fail" -eq 0 ] || { echo "--- full output ---" >&2; echo "$out" >&2; exit 1; }
exit 0
