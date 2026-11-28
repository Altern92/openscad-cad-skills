#!/usr/bin/env bash
# P25 / AC-3..AC-6 (2026-11-18). The agent writes the limits the gates check (max_gap, max_deg,
# clearance, safety, BBOX_TOL, NO_* opt-outs), so one edited number turns a FAIL into a PASS
# (2026-11-18: a ball-joint limit of 15 deg chosen by the agent, 25 in params.scad). limits.lock pins
# them with the user's words; check_limits.py fails every loosening, passes a tightening, and lists
# limits whose source is an estimate as OPEN QUESTION instead of letting them be edited.
set -uo pipefail
C="$SCAD_MODELER_SCRIPTS/check_limits.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
fail=0
mk() {  # fresh project in $tmp/p
    rm -rf "$tmp/p"; mkdir -p "$tmp/p/parts"; cd "$tmp/p"
    cat > behavior.json <<'J'
{"joints": [{"a": "arm", "b": "ball", "max_gap": 0.3, "why": "stud",
             "angle": {"echo": "TILT", "max_deg": 15, "source": "estimate: no datasheet value, measure"}},
            {"a": "base", "b": "arm", "max_gap": 0.05, "why": "pin"}],
 "clearance": {"default": 0.0, "pairs": [{"a": "arm", "b": "base", "min": 0.5}]},
 "ground": {"z": 0, "bodies": ["base"], "tol": 0.5}}
J
    echo '{"cases": [{"name": "drop", "part": "arm", "support": [0,0,0], "at": [1,0,0], "force_N": [0,0,-40], "material": "PETG Basic", "safety": 2.0},
 {"name": "pull", "type": "screw_pullout", "part": "arm", "thread_d_mm": 3, "pitch_mm": 0.5, "engagement_mm": 6, "force_N": 50, "material": "PETG Basic", "safety": 2.0},
 {"name": "press", "type": "press_fit", "part": "arm", "shaft_d_mm": 8, "hub_od_mm": 20, "interference_mm": 0.1, "hub_E_mpa": 1500, "hub_nu": 0.35, "shaft_E_mpa": 200000, "shaft_nu": 0.3, "axis": [0,0,1], "material": "PETG Basic", "safety": 2.0}]}' > loads.json
    echo '{"contacts": [{"pair": ["arm", "base"], "expected_interference_mm": [0, 0.05]}], "motion": [{"id": "swing", "min_clearance_mm": 0.2, "drivers": []}]}' > joints.json
    printf '// EXPECTED_BBOX: [10, 10, 10]\n// EXPECTED_BBOX_TOL: 0.01\ncube(10);\n' > parts/a.scad
    echo '[{"name": "arm_boss", "part": "arm", "to": "base", "min_material_mm": 1.5}]' > attachments.json   # bare-list form (RC projects)
}
run() { python3 "$C" "$@" --project-dir "$tmp/p" 2>&1; }
expect() {  # want_exit text...
    local want=$1; shift; o=$(run check); r=$?
    [ "$r" -eq "$want" ] || { echo "[$CASE] want exit $want, got $r: $o" >&2; fail=1; return; }
    for w in "$@"; do grep -qF <<< "$o" -- "$w" || { echo "[$CASE] missing '$w': $o" >&2; fail=1; }; done
}
edit() { python3 - "$@" <<'PY'
import json, sys
f, expr = sys.argv[1], sys.argv[2]
d = json.load(open(f)); exec(expr); json.dump(d, open(f, "w"))
PY
}

CASE=no-lock; mk; expect 2 "not locked" "limits.lock"
CASE=no-quote; o=$(run approve); [ $? -eq 4 ] || { echo "[$CASE] approve without --quote must be exit 4" >&2; fail=1; }
CASE=approved; o=$(run approve --quote "taip, tinka"); [ $? -eq 0 ] && [ -f limits.lock ] || { echo "[$CASE] approve failed: $o" >&2; fail=1; }
expect 0 "OPEN QUESTION" "max_deg = 15"
for c in 'd["joints"][0]["angle"]["max_deg"] = 25|behavior.json|max_deg' \
         'd["joints"][0]["max_gap"] = 0.8|behavior.json|max_gap' \
         'd["clearance"]["pairs"][0]["min"] = 0.2|behavior.json|min' \
         'd["clearance"]["default"] = -0.1|behavior.json|default' \
         'd["ground"]["tol"] = 2|behavior.json|tol' \
         'del d["joints"][1]|behavior.json|removed' \
         'd["cases"][0]["safety"] = 1.5|loads.json|safety' \
         'd["cases"][0]["force_N"] = [0,0,-10]|loads.json|force_N' \
         'd["contacts"][0]["expected_interference_mm"] = [0, 0.5]|joints.json|expected_interference_mm' \
         'd["motion"][0]["min_clearance_mm"] = 0|joints.json|min_clearance_mm' \
         'd["cases"][0]["reach"] = 80|loads.json|reach' \
         'd["cases"][1]["engagement_mm"] = 12|loads.json|engagement_mm' \
         'd["cases"][1]["thread_d_mm"] = 6|loads.json|thread_d_mm' \
         'd[0]["min_material_mm"] = 0.5|attachments.json|min_material_mm'; do
    IFS='|' read -r expr file word <<< "$c"; CASE="loosen $file $word"
    cp limits.lock "$tmp/l"; mk; cp "$tmp/l" limits.lock; edit "$file" "$expr"
    expect 3 "loosened" "$word"
done
CASE="loosen BBOX_TOL"; mk; cp "$tmp/l" limits.lock; sed -i '' 's/BBOX_TOL: 0.01/BBOX_TOL: 0.5/' parts/a.scad; expect 3 "loosened" "EXPECTED_BBOX_TOL"
CASE="new opt-out"; mk; cp "$tmp/l" limits.lock; printf '// NO_JOINT: lazy\n' >> parts/a.scad; expect 3 "loosened" "NO_JOINT"
# P26 / AC-13 (Fable audit e6): opt-outs the gates honour but the lock missed
CASE="bare PREVIEW_FILE"; mk; cp "$tmp/l" limits.lock; printf '// PREVIEW_FILE\n' >> parts/a.scad; expect 3 "loosened" "PREVIEW_FILE"
CASE="LIBRARY_FILE"; mk; cp "$tmp/l" limits.lock; printf '// LIBRARY_FILE: helpers\n' >> parts/a.scad; expect 3 "loosened" "LIBRARY_FILE"
CASE="EXPECTED_BODIES up"; mk; printf '// EXPECTED_BODIES: 1\n' >> parts/a.scad; python3 "$C" approve --quote "taip, tinka" --project-dir "$tmp/p" >/dev/null
sed -i '' 's/EXPECTED_BODIES: 1/EXPECTED_BODIES: 2/' parts/a.scad; expect 3 "loosened" "EXPECTED_BODIES"
for c in 'd["cases"][1]["pitch_mm"] = 0.25|pitch_mm' 'd["cases"][2]["hub_od_mm"] = 30|hub_od_mm' 'd["cases"][2]["axis"] = [1,0,0]|axis' 'd["cases"][2]["hub_nu"] = 0.45|hub_nu' 'd["cases"][0]["material"] = "PLA"|material' 'd["cases"][0]["support"] = [5,0,0]|support' 'd["cases"][0]["print_up"] = [1,0,0]|print_up'; do
    IFS='|' read -r expr word <<< "$c"; CASE="change loads $word"
    mk; cp "$tmp/l" limits.lock; edit loads.json "$expr"; expect 3 "changed" "$word"
done
CASE="lock deleted"; mk; cp "$tmp/l" limits.lock; mkdir -p build; echo '{"mode":"--all","limits_locked":true}' > build/.validation_state.json
rm limits.lock; expect 3 "is gone"
CASE="tighten"; mk; cp "$tmp/l" limits.lock; edit behavior.json 'd["joints"][0]["max_gap"] = 0.1'; expect 0 "tightened"
CASE="bad json"; mk; cp "$tmp/l" limits.lock; echo '{' > loads.json; expect 4 "loads.json"
# validate_scad.sh wiring: a loosened BBOX_TOL turns the run red
CASE=validate; rm -rf "$tmp/v"; mkdir -p "$tmp/v/parts"; cd "$tmp/v"
printf '// EXPECTED_BBOX: [10, 10, 10]\n// EXPECTED_BBOX_TOL: 0.01\n// EXPECTED_THROUGH_HOLES: 0\n// NO_JOINT: single part\ncube(10);\n' > parts/a.scad
python3 "$C" approve --quote "taip" >/dev/null
sed -i '' 's/BBOX_TOL: 0.01/BBOX_TOL: 0.5/' parts/a.scad
o=$(bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all 2>&1); r=$?
[ "$r" -eq 1 ] && grep -q <<< "$o" "CHECK_RESULT limits=FAIL" || { echo "[$CASE] want exit 1 + limits=FAIL, got $r" >&2; echo "$o" | grep CHECK_RESULT >&2; fail=1; }
exit $fail
