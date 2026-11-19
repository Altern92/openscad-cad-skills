#!/usr/bin/env bash
# P27 / AC-12 (Fable calculation audit): a limit written AFTER approval that overrides a locked or implicit
# default, a changed force direction, a coarser motion step or narrower range all FAIL as loosened
set -uo pipefail
L="$SCAD_MODELER_SCRIPTS/check_limits.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"
fail=0
base() {
echo '{"bodies": {"a": {"render": [{"MODE": "part", "PART": "a"}]}, "b": {"render": [{"MODE": "part", "PART": "b"}]}, "c": {"render": [{"MODE": "part", "PART": "c"}]}}, "joints": [{"a": "a", "b": "b", "max_gap": 0.3, "why": "x"}], "clearance": {"default": 1.5}, "ground": {"z": 0, "bodies": ["a"]}}' > behavior.json
echo '{"contacts": [{"pair": ["a", "b"], "joint_type": "touching"}], "motion": [{"id": "m", "range_deg": [0, 90], "step_deg": 2, "drivers": [{"part": "a", "axis": [0, 0, 1], "origin": [0, 0, 0], "ratio": -1.0}, {"part": "b", "ratio": 1.0}]}]}' > joints.json
echo '{"cases": [{"name": "c", "part": "bar", "support": [0, 0, 0], "at": [50, 0, 0], "force_N": [0, 0, 45]}]}' > loads.json
}
base; python3 "$L" approve --quote "test approval" >/dev/null 2>&1 || { echo "approve failed" >&2; exit 1; }
o=$(python3 "$L" check 2>&1); [ $? -eq 0 ] || { echo "baseline: unchanged project must pass: $o" >&2; fail=1; }
t() {   # $1 label, $2 python edit on file $3
    base; python3 - "$3" <<P
import json, sys; f = sys.argv[1]; d = json.load(open(f)); $2; json.dump(d, open(f, "w"))
P
    o=$(python3 "$L" check 2>&1); r=$?
    [ $r -eq 3 ] || { echo "AC-12: $1 not caught (rc $r): $o" >&2; fail=1; }
}
t "clearance pair below the locked default" 'd["clearance"]["pairs"] = [{"a": "a", "b": "c", "min": 0.0}]' behavior.json
t "ground.tol above the implicit 0.5" 'd["ground"]["tol"] = 50' behavior.json
t "interference hi above the implicit 0" 'd["contacts"][0]["expected_interference_mm"] = [0, 5.0]' joints.json
t "force direction changed" 'd["cases"][0]["force_N"] = [45, 0, 0]' loads.json
t "coarser motion step" 'd["motion"][0]["step_deg"] = 90' joints.json
t "narrower motion range" 'd["motion"][0]["range_deg"] = [0, 1]' joints.json
# P27b (Fable review of P27): driver and contact loosenings
t "teeth added" 'd["motion"][0]["drivers"][0]["teeth"] = 20' joints.json
t "ratio made tiny" 'd["motion"][0]["drivers"][0]["ratio"] = -0.001' joints.json
t "driver dropped" 'd["motion"][0]["drivers"].pop(1)' joints.json
t "axis moved" 'd["motion"][0]["drivers"][0]["axis"] = [1, 0, 0]' joints.json
t "new contact" 'd["contacts"].append({"pair": ["a", "c"]})' joints.json
base; python3 -c 'import json; d=json.load(open("joints.json")); d["motion"][0]["min_clearance_mm"]=0.5; json.dump(d, open("joints.json","w"))'
python3 "$L" approve --quote "test approval" >/dev/null 2>&1
python3 -c 'import json; d=json.load(open("joints.json")); d["contacts"][0]["min_clearance_mm"]=0.0; json.dump(d, open("joints.json","w"))'
o=$(python3 "$L" check 2>&1); [ $? -eq 3 ] || { echo "P27b: contact clearance 0 under an approved 0.5 not caught: $o" >&2; fail=1; }
base; python3 "$L" approve --quote "test approval" >/dev/null 2>&1
base; python3 -c 'import json; d=json.load(open("loads.json")); d["cases"][0]["force_N"]=[0.0,-0.0,45]; json.dump(d, open("loads.json","w"))'
o=$(python3 "$L" check 2>&1); [ $? -eq 0 ] || { echo "P27b: -0.0 read as a new force direction: $o" >&2; fail=1; }
base; python3 -c 'import json; d=json.load(open("limits.lock")); d.pop("schema"); json.dump(d, open("limits.lock","w"))'
o=$(python3 "$L" check 2>&1); grep -q "approved before schema" <<< "$o" || { echo "P27b: old lock not flagged: $o" >&2; fail=1; }
python3 "$L" approve --quote "test approval" >/dev/null 2>&1
base; python3 - <<'P'
import json; d = json.load(open("behavior.json")); d["clearance"]["pairs"] = [{"a": "a", "b": "c", "min": 3.0}]; json.dump(d, open("behavior.json", "w"))
P
o=$(python3 "$L" check 2>&1); [ $? -eq 0 ] || { echo "AC-12: a TIGHTER new pair (3.0 > 1.5) was failed: $o" >&2; fail=1; }
exit $fail
