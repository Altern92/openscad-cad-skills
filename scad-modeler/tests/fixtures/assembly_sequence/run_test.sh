#!/usr/bin/env bash
# P35 (wave 1): check_assembly_sequence.py -- greedy straight-line disassembly of positioned meshes.
# (a) open box+block+lid PASS  (b) sealed pin FAIL "trapped" exit 3  (c) same, pin in inserted_before PASS+named
# (d) no build/positioned SKIP  (e) two plates sharing a face slide apart PASS (contact is not collision)
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
C="$SCAD_MODELER_SCRIPTS/check_assembly_sequence.py"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
for c in open closed slide press sealed_overlap thinwall; do mkdir -p "$t/$c/build/positioned"; python3 "$here/make_stls.py" "$t/$c/build/positioned" "$c" || exit 1; done
out=$(python3 "$C" --project-dir "$t/open" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^PASS: assembly_sequence, 3 part" <<< "$out" && grep -q "lid along" <<< "$out" || die "(a) open box: expected PASS with an order, rc=$rc"
out=$(python3 "$C" --project-dir "$t/closed" 2>&1); rc=$?
[ $rc -eq 3 ] && grep -q "part pin is trapped: no straight removal direction" <<< "$out" || die "(b) sealed pin: expected exit 3 'pin is trapped', rc=$rc"
echo '{"inserted_before": [{"part": "pin", "reason": "moulded in before the cap is welded"}]}' > "$t/closed/assembly.json"
out=$(python3 "$C" --project-dir "$t/closed" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^PASS" <<< "$out" && grep -q "pin skipped (inserted_before): moulded" <<< "$out" || die "(c) exception: expected PASS naming pin, rc=$rc"
mkdir "$t/none"
out=$(python3 "$C" --project-dir "$t/none" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^SKIP" <<< "$out" && ! grep -q "^PASS" <<< "$out" || die "(d) no positioned STLs: expected SKIP, rc=$rc"
out=$(python3 "$C" --project-dir "$t/slide" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^PASS: assembly_sequence, 2 part" <<< "$out" || die "(e) touching plates: expected PASS, rc=$rc"
# (f) press fit: undeclared -> exit 2 NOT VERIFIED (never PASS); declared along +-Z -> PASS + INFO
out=$(python3 "$C" --project-dir "$t/press" 2>&1); rc=$?
[ $rc -eq 2 ] && grep -q "^NOT VERIFIED: removal of .* needs overlap" <<< "$out" && ! grep -q "^PASS" <<< "$out" || die "(f) undeclared press fit: expected exit 2 NOT VERIFIED, rc=$rc"
echo '{"press_fit": [{"pair": ["block", "pin"], "direction": [0, 0, 1], "reason": "0.2 mm interference fit"}]}' > "$t/press/assembly.json"
out=$(python3 "$C" --project-dir "$t/press" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^PASS" <<< "$out" && grep -q "^INFO: assembly_sequence, .* leaves through declared press fit" <<< "$out" || die "(f) declared press fit: expected PASS + INFO, rc=$rc"
# sealed pin overlapping its ceiling: must not PASS
out=$(python3 "$C" --project-dir "$t/sealed_overlap" 2>&1); rc=$?
[ $rc -ne 0 ] && ! grep -q "^PASS" <<< "$out" || die "sealed_overlap must not PASS, rc=$rc"
# thin ceiling + multi-shell part: must not tunnel through the 0.4 mm wall
out=$(python3 "$C" --project-dir "$t/thinwall" 2>&1); rc=$?
[ $rc -ne 0 ] && ! grep -q "^PASS" <<< "$out" || die "thinwall must not PASS, rc=$rc"
# exceptions: all parts excepted -> SKIP; unknown name -> exit 4
echo '{"flex": [{"part": "block", "reason": "x"}, {"part": "pin", "reason": "y"}]}' > "$t/press/assembly.json"
out=$(python3 "$C" --project-dir "$t/press" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "^SKIP" <<< "$out" && ! grep -q "^PASS" <<< "$out" || die "all parts excepted: expected SKIP, rc=$rc"
echo '{"flex": [{"part": "nosuch", "reason": "x"}]}' > "$t/press/assembly.json"
python3 "$C" --project-dir "$t/press" >/dev/null 2>&1; [ $? -eq 4 ] || die "unknown exception name: expected exit 4"
# --positioned: a non-default build dir is honoured
mkdir -p "$t/alt"; cp -R "$t/open/build/positioned" "$t/alt/pos"
out=$(python3 "$C" --project-dir "$t/alt" --positioned "$t/alt/pos" 2>&1); [ $? -eq 0 ] && grep -q "^PASS" <<< "$out" || die "--positioned ignored"
rm -f "$t/closed/assembly.json"; out=$(python3 "$C" --project-dir "$t/closed" 2>&1)
! grep -q "initial overlap" <<< "$out" || die "(b) sealed pin wrongly counted as initial overlap"
exit 0
