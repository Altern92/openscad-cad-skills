#!/usr/bin/env bash
# P10 / AC-1, AC-2, AC-3 (2026-11-01). One validation path for a lone part too:
# openscad-cad used to run check_dimensions.py / check_features.py by hand, which
# skipped connectivity and left no build/.validation_state.json for the stop gate.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/ok" "$tmp/bad"
printf '// EXPECTED_BBOX: [20, 10, 5]\n// EXPECTED_THROUGH_HOLES: 0\ncube([20,10,5]);\n' > "$tmp/ok/bracket.scad"
printf '// EXPECTED_BBOX: [30, 10, 5]\ncube([20,10,5]);\n' > "$tmp/bad/bracket.scad"
die() { echo "$1" >&2; echo "$out" >&2; exit 1; }

# AC-1
out=$(cd "$tmp/ok" && bash "$V" bracket.scad 2>&1); rc=$?
[ "$rc" -eq 0 ] || die "AC-1: exit $rc"
[ -s "$tmp/ok/build/bracket.stl" ] || die "AC-1: no build/bracket.stl"
for c in env connectivity dimensions features; do
    echo "$out" | grep -q "^CHECK_RESULT $c=" || die "AC-1: no CHECK_RESULT $c"
done
echo "$out" | grep -q '^COVERAGE:' || die "AC-1: no COVERAGE line"
h=$(shasum -a 256 "$tmp/ok/bracket.scad" | cut -d' ' -f1)
grep -q "\"bracket.scad\":\"$h\"" "$tmp/ok/build/.validation_state.json" || die "AC-1: state lacks bracket.scad hash"

# AC-2
out=$(cd "$tmp/bad" && bash "$V" bracket.scad 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "AC-2: exit $rc, want 1"
echo "$out" | grep -q '^CHECK_RESULT dimensions=FAIL' || die "AC-2: no dimensions=FAIL"
grep -q '"verdict":"FAIL"' "$tmp/bad/build/.validation_state.json" || die "AC-2: state verdict not FAIL"

# AC-3
out=$(cd "$tmp/ok" && bash "$V" missing.scad 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "AC-3: exit $rc, want 1"
echo "$out" | grep -q 'ERROR: missing.scad not found' || die "AC-3: no not-found error"
exit 0
