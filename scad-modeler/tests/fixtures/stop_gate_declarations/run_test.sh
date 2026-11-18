#!/usr/bin/env bash
# P25 / AC-1, AC-2 (2026-11-18). The stop gate guarded .scad only: behavior.json, loads.json,
# fasteners.json could change after validate (a limit loosened, a joint dropped) and the session
# still ended "validated". validate --all now records a sha256 per root *.json ("declarations")
# and the gate blocks when a declaration of a touched project differs from that record.
set -uo pipefail
H="$SCAD_MODELER_SCRIPTS/../hooks/scad_stop_gate.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
P="$tmp/proj"; mkdir -p "$P/parts" "$P/build"
echo 'cube(10);' > "$P/parts/a.scad"
echo '{"joints": [{"a": "x", "b": "y", "max_gap": 0.3}]}' > "$P/behavior.json"
fail=0
edit() { printf '{"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"%s"}}]}}\n' "$1" > "$2"; }
run() { printf '{"transcript_path":"%s","stop_hook_active":false,"cwd":"%s"}' "$1" "$P" | python3 "$H"; }
sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
state() {  # $1 = declarations json object
    printf '{"verdict":"PASS","sources":{"parts/a.scad":"%s"},"declarations":%s}\n' "$(sha "$P/parts/a.scad")" "$1" \
        > "$P/build/.validation_state.json"
}
blocks() { echo "$1" | grep -q '"decision": *"block"'; }
T="$tmp/t.jsonl"; edit "$P/behavior.json" "$T"

# AC-2 negative: declaration unchanged since validate -> no block
state "{\"behavior.json\":\"$(sha "$P/behavior.json")\"}"
out=$(run "$T"); [ -z "$out" ] || { echo "AC-2: unchanged declaration blocked: $out" >&2; fail=1; }
# AC-2: limit loosened after validate -> block naming the file and validate --all
echo '{"joints": [{"a": "x", "b": "y", "max_gap": 0.8}]}' > "$P/behavior.json"
out=$(run "$T")
blocks "$out" && grep -q <<< "$out" 'behavior.json' && grep -q <<< "$out" 'validate_scad.sh.*--all' \
    || { echo "AC-2: changed declaration not blocked: $out" >&2; fail=1; }
# AC-2: a new declaration file the last run never saw, in a project touched via its .scad
T2="$tmp/t2.jsonl"; edit "$P/parts/a.scad" "$T2"
state "{\"behavior.json\":\"$(sha "$P/behavior.json")\"}"; echo '{"cases": []}' > "$P/loads.json"
out=$(run "$T2"); blocks "$out" && grep -q <<< "$out" 'loads.json' \
    || { echo "AC-2: new declaration not blocked: $out" >&2; fail=1; }
rm "$P/loads.json"
# AC-2: state from before P25 (no "declarations") + an edited declaration -> block (re-run --all)
printf '{"verdict":"PASS","sources":{"parts/a.scad":"%s"}}\n' "$(sha "$P/parts/a.scad")" > "$P/build/.validation_state.json"
out=$(run "$T"); blocks "$out" || { echo "AC-2: pre-P25 state not blocked: $out" >&2; fail=1; }
# a .json outside any SCAD project is not a declaration
mkdir -p "$tmp/other"; echo '{}' > "$tmp/other/x.json"; edit "$tmp/other/x.json" "$tmp/t3.jsonl"
out=$(run "$tmp/t3.jsonl"); [ -z "$out" ] || { echo "AC-2: non-project json blocked: $out" >&2; fail=1; }

# AC-1: validate --all writes declarations + skill
[ -n "${SCAD_MUTANT_INNER:-}" ] && exit $fail
Q="$tmp/q"; mkdir -p "$Q/parts"
printf '// EXPECTED_BBOX: [10, 10, 10]\n// EXPECTED_THROUGH_HOLES: 0\n// NO_JOINT: single part\ncube(10);\n' > "$Q/parts/a.scad"
echo '{"cases": []}' > "$Q/loads.json"
(cd "$Q" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all >/dev/null 2>&1)
python3 - "$Q" <<'PY' || fail=1
import hashlib, json, sys
q = sys.argv[1]; s = json.load(open(q + "/build/.validation_state.json"))
d = s.get("declarations")
want = hashlib.sha256(open(q + "/loads.json", "rb").read()).hexdigest()
assert d and d.get("loads.json") == want, f"AC-1: declarations missing/wrong: {d}"
assert s.get("skill"), f"AC-1: no skill version in {sorted(s)}"
PY
exit $fail
