#!/usr/bin/env bash
# P8 agent eval (2026-11-01): a hinge declared in joints.json "contacts" was exempt at every
# angle, so a sweep whose only moving pair is declared checked 0 positions and said PASS
# (chain-12 class: a declared contact masks a real collision). The declared range bounds the
# overlap; a lid swinging INTO the box must FAIL, the same lid swinging up must PASS.
set -uo pipefail
M="$SCAD_MODELER_SCRIPTS/motion_sweep.py"
PY=$(bash "$SCAD_MODELER_SCRIPTS/resolve_python.sh" --print 2>/dev/null || echo python3)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" | tail -20 >&2; exit 1; }
cd "$tmp"
echo 'difference() { cube([40, 20, 10]); translate([2, 2, 2]) cube([36, 16, 10]); }' > box.scad
echo 'translate([0, 0, 10]) cube([40, 20, 2]);' > lid.scad
openscad -q -o box.stl box.scad && openscad -q -o lid.stl lid.scad || die "render failed"
j() { printf '{"contacts": [{"pair": ["box", "lid"], "joint_type": "hinge", "expected_interference_mm": [0, 0.05], "derivation": "lid rests on rim"}], "motion": [{"id": "open", "drivers": [{"part": "lid", "type": "revolute", "axis": [%s, 0, 0], "origin": [0, 20, 10], "ratio": 1.0}], "range_deg": [0, 110], "step_deg": 10}]}\n' "$1" > joints.json; }
j 1;  out=$("$PY" "$M" --joints joints.json box.stl lid.stl 2>&1); [ $? -ne 0 ] || die "lid swinging into the box: PASS"
j -1; out=$("$PY" "$M" --joints joints.json box.stl lid.stl 2>&1); [ $? -eq 0 ] || die "lid swinging up: not PASS"
echo "$out" | grep -q "nothing to check" && die "declared pair skipped instead of swept"
exit 0
