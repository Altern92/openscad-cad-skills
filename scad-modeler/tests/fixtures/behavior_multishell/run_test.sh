#!/usr/bin/env bash
# P28 (2026-11-27, wave1 AC-A1..A3): a body of 4 balls with the top ball pulled 5 mm off its cup FAILs
# "separate piece"; seated = PASS. The angle echo may live in a joint body's own scad (read, and over
# max_deg FAILs); an echo in neither file keeps the "printed no ECHO" FAIL.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
cp "$here"/*.scad "$here"/*.json "$t/"
expect() {   # case exit text... [-- extra args]
    local c=$1 want=$2; shift 2; local args=()
    while [ $# -gt 0 ] && [ "$1" != -D ]; do args+=("$1"); shift; done
    o=$(python3 "$SCAD_MODELER_SCRIPTS/check_behavior.py" --project-dir "$t" --behavior "$c.json" "$@" 2>&1); r=$?
    [ "$r" -eq "$want" ] || { echo "$c: expected exit $want, got $r"; echo "$o"; exit 1; }
    for w in "${args[@]}"; do grep -qF <<< "$o" "$w" || { echo "$c: missing '$w'"; echo "$o"; exit 1; }; done
}
expect balls 0 "HOLDS: PASS"
expect balls 3 "balls: separate piece" "reaches none of its joint partners" -D TOP=5
expect joint_echo 0 "KINEMATICS: PASS"
expect joint_echo_over 3 "ARM_TILT = 20.0 deg > 10"
expect no_echo 3 "printed no \`ECHO: NOPE"
exit 0
