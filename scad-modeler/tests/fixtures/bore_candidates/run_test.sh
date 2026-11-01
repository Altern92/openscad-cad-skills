#!/usr/bin/env bash
# P3 (2026-11-01): bores.json was written by hand or not at all (bore_reachability SKIP
# on 10 of 11 real projects, B class 22 incidents). bore_candidates.py reads the CSG
# tree and lists every subtracted cylinder as a bores.json entry, in part-local
# coordinates, for a human to keep or delete. A later union that refills a cut is then
# caught by check_bore_reachability on the generated file.
set -uo pipefail
G="$SCAD_MODELER_SCRIPTS/bore_candidates.py"; B="$SCAD_MODELER_SCRIPTS/check_bore_reachability.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" >&2; exit 1; }
cat > "$tmp/plate.scad" <<'S'
$fn=32;
difference(){
  union(){ cube([40,20,5]); translate([0,0,5]) cylinder(d=4,h=3); }      // added cylinder: not a bore
  translate([10,10,-1]) cylinder(d=5,h=7);                                 // vertical through
  translate([30,10,2.5]) rotate([0,90,0]) cylinder(d=3,h=20,center=true);  // horizontal, centered
}
S
out=$(python3 "$G" --scad "$tmp/plate.scad" 2>&1) || die "generator failed"
echo "$out" > "$tmp/bores.json"
python3 - "$tmp/bores.json" <<'PY' || exit 1
import json, sys
c = json.load(open(sys.argv[1]))
assert len(c) == 2, f"want 2 candidates, got {len(c)}: {c}"
def near(a, b): return all(abs(x - y) < 1e-6 for x, y in zip(a, b))
v = [e for e in c if near(e["start"], [10, 10, -0.95])]
assert v and near(v[0]["end"], [10, 10, 5.95]) and abs(v[0]["diameter"] - 5) < 1e-9, c
h = [e for e in c if abs(e["diameter"] - 3) < 1e-9]
assert h and {tuple(round(x, 6) for x in h[0]["start"]), tuple(round(x, 6) for x in h[0]["end"])} == {(39.95, 10.0, 2.5), (20.05, 10.0, 2.5)}, c
assert all(e["part"] == "plate" for e in c), c
PY
openscad -q -o "$tmp/plate.stl" "$tmp/plate.scad"
out=$(python3 "$B" --bores "$tmp/bores.json" "$tmp/plate.stl" 2>&1) || die "open bores reported blocked"
# a later union refills the vertical bore with a 0.4 mm skin
sed 's#^}$#}\ntranslate([7,7,4.6]) cube([6,6,0.4]);#' "$tmp/plate.scad" > "$tmp/sealed.scad"
openscad -q -o "$tmp/plate_sealed.stl" "$tmp/sealed.scad"
out=$(python3 "$B" --bores "$tmp/bores.json" "$tmp/plate_sealed.stl" 2>&1); rc=$?
[ "$rc" -eq 3 ] || die "sealed bore not caught (exit $rc)"
exit 0
