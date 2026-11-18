#!/usr/bin/env bash
# P24 kinematics (check_behavior.py): a hinged arm has 1 DOF and its tilt echo stays under the limit
# (PASS); the same tilt over a tighter limit, a link held by one ball (3 extra DOF, named), a second pin
# that locks the hinge, an anchor point off the parts, a two-piece body in a ball joint, typed joints
# without "dof" all FAIL; an angle limit without a source is a usage error (exit 4).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
cp "$here"/*.scad "$here"/*.json "$t/"
run() { python3 "$SCAD_MODELER_SCRIPTS/check_behavior.py" --project-dir "$t" --behavior "$1.json" 2>&1; }
expect() {   # case exit text...
    local c=$1 want=$2; shift 2
    o=$(run "$c"); r=$?
    [ "$r" -eq "$want" ] || { echo "$c: expected exit $want, got $r"; echo "$o"; exit 1; }
    for w in "$@"; do echo "$o" | grep -qF "$w" || { echo "$c: missing '$w'"; echo "$o"; exit 1; }; done
}
expect good 0 "DOF: computed 1, declared 1" "KINEMATICS: PASS" "worst   20.0 deg (limit 25.0)"
expect angle_over 3 "ARM_TILT = 20.0 deg > 10" "KINEMATICS: FAIL"
expect angle_second 3 "ARM_TWIN = -30.0 deg > 25"   # 2nd name in one echo line
expect loose 3 "4 DOF > declared 1" "link (3 DOF)"
expect locked 3 "0 DOF < declared 1: the mechanism locks"
expect anchor_far 3 "anchor (0, 0, 60)" "not on the parts"
expect multi_piece 3 "twin: 2 separate pieces in a ball joint"
expect no_dof 3 "has no \"dof\""
expect no_source 4 "angle needs echo, max_deg and a non-empty source"
exit 0
