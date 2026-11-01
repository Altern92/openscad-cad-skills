#!/usr/bin/env bash
# P9 / AC-6..AC-10 (2026-11-01). Stop hook: a session that edited a .scad file may
# not end until validate_scad.sh has run on that file's CURRENT content
# (sha256 in build/.validation_state.json). 31/95 incidents were a false PASS or a
# check that never ran; this makes "ran on what I'm handing over" a fact, not a claim.
set -uo pipefail
H="$SCAD_MODELER_SCRIPTS/../hooks/scad_stop_gate.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
P="$tmp/proj"; mkdir -p "$P/parts" "$P/build" "$tmp/tests/fixtures/x"
echo 'cube(10);' > "$P/parts/a.scad"
echo 'cube(1);' > "$tmp/tests/fixtures/x/f.scad"
fail=0
transcript() {  # $1 file, rest: paths edited via Write/Edit, then a malformed line
    local t=$1; shift; : > "$t"
    for f in "$@"; do
        printf '{"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"%s"}}]}}\n' "$f" >> "$t"
    done
    echo 'not json {' >> "$t"
}
run() {  # $1 transcript, $2 stop_hook_active -> stdout; exit code must be 0
    local out rc
    out=$(printf '{"transcript_path":"%s","stop_hook_active":%s,"cwd":"%s"}' "$1" "$2" "$P" | python3 "$H"); rc=$?
    [ "$rc" -eq 0 ] || { echo "hook exit $rc" >&2; fail=1; }
    printf '%s' "$out"
}
state() {  # $1 verdict, $2 hash for parts/a.scad
    printf '{"verdict":"%s","sources":{"parts/a.scad":"%s"}}\n' "$1" "$2" > "$P/build/.validation_state.json"
}
blocks() { echo "$1" | grep -q '"decision": *"block"'; }
T="$tmp/t.jsonl"; transcript "$T" "$P/parts/a.scad"
good=$(shasum -a 256 "$P/parts/a.scad" | cut -d' ' -f1)

# AC-6: edited, never validated -> block naming file + command
out=$(run "$T" false)
blocks "$out" && echo "$out" | grep -q 'a.scad' && echo "$out" | grep -q 'validate_scad.sh' \
    || { echo "AC-6 (no state): want block naming a.scad and validate_scad.sh, got: $out" >&2; fail=1; }
# AC-6: validated, then edited again (hash differs)
state PASS 0000; out=$(run "$T" false)
blocks "$out" || { echo "AC-6 (stale hash): want block, got: $out" >&2; fail=1; }
# AC-7: hash matches -> allow, PASS and FAIL alike
for v in PASS FAIL; do
    state $v "$good"; out=$(run "$T" false)
    [ -z "$out" ] || { echo "AC-7 ($v): want no output, got: $out" >&2; fail=1; }
done
# AC-8: no .scad edits
T2="$tmp/t2.jsonl"; transcript "$T2" "$tmp/notes.md"; rm -f "$P/build/.validation_state.json"
out=$(run "$T2" false); [ -z "$out" ] || { echo "AC-8: want no output, got: $out" >&2; fail=1; }
# AC-9: loop guard
out=$(run "$T" true); [ -z "$out" ] || { echo "AC-9: stop_hook_active must not block, got: $out" >&2; fail=1; }
# AC-10: deleted file, fixture path, opt-out, garbage input
T3="$tmp/t3.jsonl"; transcript "$T3" "$tmp/gone.scad" "$tmp/tests/fixtures/x/f.scad"
out=$(run "$T3" false); [ -z "$out" ] || { echo "AC-10 (gone/fixture): got: $out" >&2; fail=1; }
out=$(printf '{"transcript_path":"%s","stop_hook_active":false}' "$T" | SCAD_STOP_GATE=0 python3 "$H"); rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || { echo "AC-10 (opt-out): rc=$rc out=$out" >&2; fail=1; }
out=$(echo 'garbage' | python3 "$H"); rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || { echo "AC-10 (bad input): rc=$rc out=$out" >&2; fail=1; }
out=$(echo '{"transcript_path":"/nonexistent"}' | python3 "$H"); rc=$?
[ "$rc" -eq 0 ] && [ -z "$out" ] || { echo "AC-10 (no transcript): rc=$rc out=$out" >&2; fail=1; }
# P17b: a .scad written through Bash (heredoc, cp, sed -i) counts as edited; one only read does not
bash_t() {  # $1 file, $2 command
    python3 -c 'import json,sys; print(json.dumps({"message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":sys.argv[1]}}]}}))' "$2" > "$1"
}
rm -f "$P/build/.validation_state.json"
for c in "cat > parts/a.scad <<'E'
cube(10);
E" "cp /tmp/x.scad $P/parts/a.scad" "sed -i '' 's/10/12/' parts/a.scad" "printf 'cube(1);' | tee parts/a.scad"; do
    bash_t "$tmp/tb.jsonl" "$c"; out=$(run "$tmp/tb.jsonl" false)
    blocks "$out" || { echo "P17b: Bash write not seen: $c" >&2; fail=1; }
done
for c in "cat parts/a.scad > /tmp/out.txt" "openscad -o build/a.stl parts/a.scad" "grep cube parts/a.scad"; do
    bash_t "$tmp/tb.jsonl" "$c"; out=$(run "$tmp/tb.jsonl" false)
    [ -z "$out" ] || { echo "P17b: read-only Bash blocked: $c" >&2; fail=1; }
done
# P5 / AC-9: an approval recorded this session must quote the user's own words
printf '{"sha256":"x","quote":"taip, tinka","when":"t"}\n' > "$P/acceptance.lock"
appr() {  # $1 file, $2 user text
    python3 - "$1" "$2" <<'PYT'
import json, sys
t, user = sys.argv[1], sys.argv[2]
with open(t, "w") as f:
    f.write(json.dumps({"type": "user", "message": {"role": "user", "content": user}}) + "\n")
    f.write(json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "taip, tinka"}]}}) + "\n")
    f.write(json.dumps({"message": {"content": [{"type": "tool_use", "name": "Bash",
        "input": {"command": "python3 ~/.claude/skills/scad-modeler/scripts/acceptance.py approve --quote 'taip, tinka'"}}]}}) + "\n")
PYT
}
appr "$tmp/ta.jsonl" "padaryk dangtį"; out=$(run "$tmp/ta.jsonl" false)
blocks "$out" && echo "$out" | grep -q 'acceptance' || { echo "AC-9: self-approval not blocked: $out" >&2; fail=1; }
appr "$tmp/ta.jsonl" "Taip,  tinka -- daryk"; out=$(run "$tmp/ta.jsonl" false)
[ -z "$out" ] || { echo "AC-9: user-quoted approval blocked: $out" >&2; fail=1; }
rm -f "$P/acceptance.lock"
# End to end: a real validate_scad.sh run on a lone file satisfies the gate (state format
# written by the script == format read by the hook); editing it afterwards blocks again.
L="$tmp/lone"; mkdir -p "$L"; echo 'cube(3);' > "$L/b.scad"
T4="$tmp/t4.jsonl"; transcript "$T4" "$L/b.scad"
(cd "$L" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" b.scad >/dev/null 2>&1)
out=$(run "$T4" false); [ -z "$out" ] || { echo "e2e: validated file still blocks: $out" >&2; fail=1; }
echo 'cube(4);' > "$L/b.scad"
out=$(run "$T4" false); blocks "$out" || { echo "e2e: edit after validation did not block" >&2; fail=1; }
exit $fail
