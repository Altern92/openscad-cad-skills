#!/usr/bin/env bash
# P24 kinematics (check_behavior.py): a hinged arm has 1 DOF and its tilt echo stays under the limit
# (PASS); the same tilt over a tighter limit, a link held by one ball (3 extra DOF, named), a second pin
# that locks the hinge, an anchor point off the parts, a two-piece body in a ball joint, typed joints
# without "dof" all FAIL; an angle limit without a source is a usage error (exit 4).
# P28: geometric angle cases at the end.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
cp "$here"/*.scad "$here"/*.json "$t/"
run() { python3 "$SCAD_MODELER_SCRIPTS/check_behavior.py" --project-dir "$t" --behavior "$1.json" 2>&1; }
expect() {   # case exit text...
    local c=$1 want=$2; shift 2
    o=$(run "$c"); r=$?
    [ "$r" -eq "$want" ] || { echo "$c: expected exit $want, got $r"; echo "$o"; exit 1; }
    for w in "$@"; do grep -qF <<< "$o" "$w" || { echo "$c: missing '$w'"; echo "$o"; exit 1; }; done
}
expect good 0 "DOF: computed 1, declared 1" "KINEMATICS: PASS" "worst   20.0 deg (limit 25.0)"
expect subset_at 0 "DOF: computed 1, declared 1 + 0 idle (A) at A=0 B=0"   # P26 / AC-16: dof.at {A: 0} on an A x B grid resolves to a full pose (old: fell back to the last pose)
expect angle_over 3 "ARM_TILT = 20.0 deg > 10" "KINEMATICS: FAIL"
expect angle_second 3 "ARM_TWIN = -30.0 deg > 25"   # 2nd name in one echo line
expect loose 3 "4 DOF > declared 1" "link (3 DOF)"
expect locked 3 "0 DOF < declared 1: the mechanism locks"
expect anchor_far 3 "anchor (0, 0, 60)" "not on the parts"
expect multi_piece 3 "twin: 2 separate pieces in a ball joint"
expect no_dof 3 "has no \"dof\""
expect no_source 4 "angle needs max_deg and a non-empty source"
# P28: the angle is also measured from the parts (rotation between the dof pose and each pose, from
# the rendered vertices). The geometry only gives a lower bound, so it can catch an echo that
# understates the turn but never fails a true one.
expect echo_lies 3 "ARM_LIE = 5.0 deg, but the parts turn 20.0 deg" "KINEMATICS: FAIL"
expect geom_only 0 "worst   20.0 deg (limit 25.0)" "KINEMATICS: PASS"
expect geom_only_over 3 "measured from the parts: 20.0 deg > 10" "KINEMATICS: FAIL"
expect axis_pin 0 "worst    0.0 deg (limit 10.0)"   # turning about the pin axis does not tilt the pin
expect morph 3 "morph changes shape between poses"
expect no_geom 4 "angle without echo needs a revolute joint or angle.axis"
# Audit A3 (2026-11-28): dof.idle used to add to the count only, so 3 idle entries absorbed the loose link
# even when they named the static base or the held arm. Each idle body must itself have that many free DOF.
expect idle_ok 0 "DOF: computed 4, declared 1 + 3 idle"
expect idle_static 3 "dof.idle names base, but base is static"
expect idle_wrong 3 "dof.idle: arm declared 3 idle DOF, but with every other body held it has 0"
exit 0
