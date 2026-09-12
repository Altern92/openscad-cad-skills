#!/usr/bin/env bash
# Two vacuous-PASS classes, both measured on 2026-09-12 by an adversarial review
# of the skill's own claims. A vacuous PASS is the one verdict worse than a
# FAIL: it reports success for work that never happened.
#
#   R-04 (fixed earlier the same day): a rule declared 'applies: always' whose
#        success_pattern accepted SKIP scored [PASS] on an EMPTY project.
#
#   R-09 (this fixture): joints.json DECLARES motion, there is no assembly.scad,
#        so validate_scad.sh can never render positioned parts and motion_sweep.py
#        never runs -- it printed 'mechanics=SKIP' with the summary "no joints.json
#        motion declared", which is false, and R-09's pattern accepted SKIP.
#        check_rules.py therefore returned exit 0 and "every applicable automated
#        rule passed" while the sweep had never executed even once.
set -uo pipefail

proj=$(mktemp -d)
mkdir -p "$proj/parts"
printf '%s\n' '\$fa = 2; \$fs = 0.3;' > "$proj/params.scad"
printf 'cube([10, 10, 10]);\n' > "$proj/parts/box.scad"
cat > "$proj/joints.json" <<'JSON'
{
  "contacts": [],
  "motion": [
    {"id": "spin", "drivers": [
      {"part": "box", "type": "revolute", "axis": [0, 0, 1], "origin": [0, 0, 0], "ratio": 1.0}
    ]}
  ]
}
JSON

( cd "$proj" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all > vout 2>&1 )
vout=$(cat "$proj/vout")

# 1. mechanics must NOT be PASS -- the sweep did not run.
echo "$vout" | grep -q "^CHECK_RESULT mechanics=PASS" && {
    echo "VACUOUS PASS: mechanics=PASS with no assembly.scad and no sweep" >&2
    exit 1; }

# 2. and the SKIP reason must be TRUE. joints.json DOES declare motion.
if echo "$vout" | grep -q "^CHECK_RESULT mechanics=SKIP"; then
    echo "$vout" | grep -qi "no assembly.scad" || {
        echo "the mechanics SKIP reason is false -- it blames a missing motion array:" >&2
        echo "$vout" | grep -A1 "mechanics=SKIP" >&2
        exit 1; }
fi

# 3. the rules gate must not call it a pass either.
( cd "$proj" && python3 "$SCAD_MODELER_SCRIPTS/check_rules.py" --project-dir . > rout 2>&1 )
rcode=$?
rout=$(cat "$proj/rout")
if [ "$rcode" -eq 0 ]; then
    echo "check_rules returned 0 while motion_sweep.py never ran:" >&2
    echo "$rout" | grep "R-09" >&2
    rm -rf "$proj"; exit 1
fi
# INCONC, not FAIL. The check RAN and could not determine an answer, which is
# a third outcome: FAIL means fix the model, INCONC means fix the checker or its
# inputs (here: add assembly.scad). Reporting INCONC as FAIL is the two-valued
# collapse the adversarial cross-field review flagged -- SARIF separates
# notApplicable from open, TTCN-3 makes inconc and none first-class verdicts,
# ISA 705 wants a DISCLAIMER rather than an adverse opinion. Either way it must
# make the run non-green, which the exit-code check above already asserts.
echo "$rout" | grep -qE "\[(FAIL|INCONC)[^]]*\] R-09" || {
    echo "expected R-09 to be FAIL or INCONC when the sweep could not run, got:" >&2
    echo "$rout" | grep "R-09" >&2
    rm -rf "$proj"; exit 1; }

rm -rf "$proj"
exit 0
