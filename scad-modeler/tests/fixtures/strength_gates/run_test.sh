#!/usr/bin/env bash
# P24 strength gate (INC-2026-11-18-07): insert hole at the knurl OD / too shallow / thin wall FAIL,
# the datasheet hole PASSes; a beam over its X-Y strength FAILs, the same beam stressed across its
# layers FAILs on the Z value where X-Y passes; a broken load path FAILs. Stress values are the hand
# result sigma = F (0.95 L) c / I: 15 N x 47.5 mm x 3 / 108 = 19.8 MPa (6x6), 158.3 MPa (3x3).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/make_stls.py" "$t/build/positioned" || exit 1
cp "$here/fasteners.json" "$here/loads.json" "$t/"
o=$(python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir "$t" 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
want=("OK   insert M3 good" "FAIL insert M3 knurl" "knurls nothing to grip" "FAIL insert M3 shallow"
      "blind depth 6.00 mm < L + 1" "FAIL insert M3 wall" "wall under 1.6 mm"
      "OK   load x6_xy on bar_x6: 19.8 MPa (allow 21.5, X-Y)" "FAIL load x3_thin on bar_x3: 158.3 MPa"
      "FAIL load z6_layers on bar_z6: 19.8 MPa (allow 18.0, Z)" "FAIL load gap" "does not connect the support"
      "STRENGTH: 4 insert(s), 4 load case(s), 6 failure(s)")
for w in "${want[@]}"; do grep -qF <<< "$o" "$w" || { echo "missing: $w"; echo "$o"; exit 1; }; done
# unknown material -> usage error, never a pass
sed 's/PETG Basic/Unobtainium/' "$here/loads.json" > "$t/loads.json"
python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir "$t" >/dev/null 2>&1; r=$?
[ "$r" -eq 4 ] || { echo "unknown material: expected exit 4, got $r"; exit 1; }
# nothing declared -> 2 (validate reports SKIP), not 0
rm "$t/loads.json" "$t/fasteners.json"
python3 "$SCAD_MODELER_SCRIPTS/check_strength.py" --project-dir "$t" >/dev/null 2>&1; r=$?
[ "$r" -eq 2 ] || { echo "nothing declared: expected exit 2, got $r"; exit 1; }
exit 0
