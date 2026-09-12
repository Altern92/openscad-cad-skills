#!/usr/bin/env bash
# A joints.json with an EMPTY motion array means "there is no motion" -- the check
# does not apply, and the verdict must be SKIP (not applicable), never INCONCLUSIVE.
#
# INCONCLUSIVE means "ran and could not determine an answer" and it makes the run
# non-green. Applying it to a project that simply has no motion would be a false
# positive, which is the exact failure the 2026-09-12 cross-field review flagged:
# a checker that fires on correct work trains the reader to ignore it.
#
# This was a real regression, not a hypothetical: the INCONCLUSIVE branch was
# added on 2026-09-12 and tested only whether joints.json EXISTS. An agent working
# on an unrelated task shipped such a file, and its own report pointed out that the
# verdict was spurious -- found by the agent, not by the suite, which is why this
# fixture exists now.
set -uo pipefail

proj=$(mktemp -d)
mkdir -p "$proj/parts"
printf '%s\n' '\$fa = 2; \$fs = 0.3;' > "$proj/params.scad"
printf 'cube([10, 10, 10]);\n' > "$proj/parts/box.scad"
# The distinguishing input: joints.json present, motion EMPTY.
cat > "$proj/joints.json" <<'JSON'
{"_comment": "no motion in this project", "contacts": [], "motion": []}
JSON

out=$( cd "$proj" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all 2>&1 )
rm -rf "$proj"

echo "$out" | grep -q "CHECK_RESULT mechanics=INCONCLUSIVE" && {
    echo "empty motion array produced INCONCLUSIVE -- it must be SKIP (not applicable):" >&2
    echo "$out" | grep -E "CHECK_RESULT mechanics|COVERAGE" >&2
    exit 1; }

echo "$out" | grep -q "CHECK_RESULT mechanics=SKIP" || {
    echo "expected mechanics=SKIP for a project with no motion declared, got:" >&2
    echo "$out" | grep -E "CHECK_RESULT mechanics|COVERAGE" >&2
    exit 1; }

# And the SKIP must be counted as not-applicable, not as inconclusive.
echo "$out" | grep "COVERAGE:" | grep -q "0 inconclusive" || {
    echo "COVERAGE counts the empty-motion SKIP as inconclusive:" >&2
    echo "$out" | grep "COVERAGE:" >&2
    exit 1; }

exit 0
