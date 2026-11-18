#!/usr/bin/env bash
# P23 AC-5 (2026-11-18, INC-2026-11-18-01): an enclosed cavity was a note nobody read.
# Undeclared = FAIL; `// EXPECTED_CAVITIES: N` with the right count = PASS; wrong count = FAIL.
set -uo pipefail
C="$SCAD_MODELER_SCRIPTS/check_connectivity.py"; OS="${OPENSCAD:-openscad}"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
printf 'difference() { cube(20, center=true); sphere(d=6, $fn=24); }\n' > "$tmp/p.scad"
"$OS" --backend=Manifold -o "$tmp/p.stl" "$tmp/p.scad" >/dev/null 2>&1 || die "render failed"
out=$(python3 "$C" --stl "$tmp/p.stl" --scad "$tmp/p.scad" 2>&1); rc=$?
[ "$rc" -eq 1 ] && grep -q <<< "$out" 'EXPECTED_CAVITIES: 1' || die "undeclared cavity: exit $rc, want 1 + hint"
sed -i '' '1i\
// EXPECTED_CAVITIES: 1
' "$tmp/p.scad"
out=$(python3 "$C" --stl "$tmp/p.stl" --scad "$tmp/p.scad" 2>&1); rc=$?
[ "$rc" -eq 0 ] || die "declared cavity: exit $rc, want 0"
sed -i '' 's/EXPECTED_CAVITIES: 1/EXPECTED_CAVITIES: 2/' "$tmp/p.scad"
out=$(python3 "$C" --stl "$tmp/p.stl" --scad "$tmp/p.scad" 2>&1); rc=$?
[ "$rc" -eq 1 ] || die "wrong cavity count: exit $rc, want 1"
exit 0
