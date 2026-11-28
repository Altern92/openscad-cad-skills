#!/usr/bin/env bash
# P31 / wave2 AC-E1..E4: screw thread strip-out, press-fit hoop stress (Lame), beam transverse shear.
# Hand-computed references (checker must agree within 1 %):
#  E1 M3x0.5, Le 6, internal thread: n = 2, Ds - En = 0.649519*0.5 = 0.32476; bracket = 1/4 + 0.57735*0.32476 = 0.4375;
#     A = pi n Le Ds * bracket = pi*2*6*3*0.4375 = 49.480 mm2 (= 0.875 pi D Le); tau = F/A: 100 N 2.021, 300 N 6.063, 600 N 12.126 MPa.
#     shear_mpa 10 / safety 2 -> allow 5.0 (so 100 N OK, 300 N FAIL); no shear_mpa -> 0.6 * min(43, 36) = 21.6 / 2 = 10.8 (derived, WARN only).
#  E2 d 10, D 20, E_hub 2000 nu .35, steel 200000 / .3: k = (400+100)/(400-100) = 1.66667;
#     p = delta / (d ((k + .35)/2000 + .7/200000)) = 0.1 / 0.0101183 = 9.883 MPa; hoop at the bore = p k = 16.472 MPa (delta .1);
#     delta .12 -> hoop 19.766 (allow X-Y 43/2 = 21.5 OK; Z 36/2 = 18.0 FAIL when the axis is horizontal); delta .2 -> 32.94 FAIL.
#  E3 stub 20 x 20 x 4, V = F: tau = 1.5 V / A = 1.5 F / 400: 2000 N 7.5 MPa (allow 20/2 = 10 OK), 3000 N 11.25 FAIL; bending stays under 21.5.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/make_stls.py" "$t/build/positioned" || exit 1
cp "$here/loads.json" "$t/"
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir "$t" 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
want=("OK   screw_pullout pull_ok: tau 2.02 MPa (allow 5.0" "FAIL screw_pullout pull_fail: tau 6.06 MPa (allow 5.0"
      "WARN screw_pullout pull_warn: tau 12.13 MPa (allow 10.8" "not a datasheet value"
      "OK   press_fit pf_ok: contact 9.88 MPa, hoop 16.5 MPa (allow 21.5, X-Y)" "FAIL press_fit pf_fail: contact 19.77 MPa, hoop 32.9 MPa (allow 21.5, X-Y)"
      "OK   press_fit pf_layers_ok: contact 11.86 MPa, hoop 19.8 MPa (allow 21.5, X-Y)"
      "FAIL press_fit pf_layers_fail: contact 11.86 MPa, hoop 19.8 MPa (allow 18.0, Z)"
      "OK   load shear_ok on blk_shear:" "shear 7.5 MPa (allow 10.0)" "FAIL load shear_fail on blk_shear:" "shear 11.2 MPa (allow 10.0)"
      "STRENGTH: 0 insert(s), 9 load case(s), 4 failure(s)")
for w in "${want[@]}"; do grep -qF <<< "$o" "$w" || { echo "missing: $w"; echo "$o"; exit 1; }; done
# a press fit without the hub modulus is a usage error, never a pass
sed 's/"hub_E_mpa": 2000, //' "$here/loads.json" > "$t/loads.json"
python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir "$t" >/dev/null 2>&1; r=$?
[ "$r" -eq 4 ] || { echo "missing hub_E_mpa: expected exit 4, got $r"; exit 1; }
# only analytic cases: no positioned STL needed
python3 - "$t" "$here/loads.json" <<'P'
import json, sys
d = sys.argv[1]; c = json.load(open(sys.argv[2]))
json.dump({"cases": [x for x in c["cases"] if x.get("type")]}, open(d + "/loads.json", "w"))
P
rm -r "$t/build"
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir "$t" 2>&1); r=$?
[ "$r" -eq 3 ] && grep -qF <<< "$o" "STRENGTH: 0 insert(s), 7 load case(s), 3 failure(s)" || { echo "analytic-only: got $r"; echo "$o"; exit 1; }
exit 0
