#!/usr/bin/env bash
# check_rules.py is the last gate before the final report, so its verdicts have
# to mean what they say. Two invariants, both of which were false on
# 2026-09-12:
#
#   1. A rule whose gate CANNOT RUN must be N/A, never PASS. R-04 (connectivity)
#      was declared 'applies: always' with success_pattern '=(PASS|SKIP)', so an
#      EMPTY project directory scored
#          [PASS  ] R-04: Connectivity: every printed part renders as one connected body
#      with no parts in it. A vacuous PASS claims work that never happened.
#
#   2. Exit code 3 means "a rule did not pass", and 4 means "the checker was
#      invoked wrongly". Conflating them turns a real gap into a tooling error.
#
# The exit-3 half needs a project that HAS parts, so this fixture builds both
# cases rather than asserting against whatever the runner directory happens to
# contain.
set -uo pipefail

# --- case 1: nothing to check -> N/A, not PASS, and exit 0 ----------------
empty=$(mktemp -d)
( cd "$empty" && python3 "$SCAD_MODELER_SCRIPTS/check_rules.py" --project-dir . > out 2>&1 )
empty_code=$?
empty_out=$(cat "$empty/out")
rm -rf "$empty"

if [ "$empty_code" -ne 0 ]; then
    echo "an empty project should exit 0 (every rule N/A), got $empty_code" >&2
    echo "$empty_out" >&2
    exit 1
fi
echo "$empty_out" | grep -qE "\[PASS[^]]*\] R-04" && {
    echo "VACUOUS PASS: R-04 reported PASS for a project with no parts" >&2
    echo "$empty_out" >&2
    exit 1
}
echo "$empty_out" | grep -qE "\[N/A[^]]*\] R-04" || {
    echo "expected R-04 to be N/A when there is nothing to render, got:" >&2
    echo "$empty_out" >&2
    exit 1
}

# --- case 2: a project with parts that fail connectivity -> exit 3 --------
proj=$(mktemp -d)
mkdir -p "$proj/parts"
cat > "$proj/parts/two_islands.scad" <<'SCAD'
// two cubes that do not touch: one printed part must be one connected body
cube([10, 10, 10], center = true);
translate([40, 0, 0]) cube([10, 10, 10], center = true);
SCAD
( cd "$proj" && python3 "$SCAD_MODELER_SCRIPTS/check_rules.py" --project-dir . > out 2>&1 )
proj_code=$?
proj_out=$(cat "$proj/out")
rm -rf "$proj"

if [ "$proj_code" -ne 3 ]; then
    echo "expected exit 3 when a rule does not pass, got $proj_code" >&2
    echo "$proj_out" >&2
    exit 1
fi
echo "$proj_out" | grep -qE "\[FAIL[^]]*\] R-04" || {
    echo "expected R-04 to be FAIL for a project with disconnected parts, got:" >&2
    echo "$proj_out" >&2
    exit 1
}

# --- every rule must carry a status --------------------------------------
echo "$proj_out" | grep -qE "\[N/A|\[MANUAL|\[PASS|\[FAIL" || {
    echo "expected per-rule statuses in the output:" >&2; echo "$proj_out" >&2; exit 1; }
exit 0
