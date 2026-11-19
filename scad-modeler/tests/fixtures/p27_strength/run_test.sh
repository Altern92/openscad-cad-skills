#!/usr/bin/env bash
# P27 (Fable calculation audit): AC-1 oblique bending, AC-2 insert blind depth not rounded up
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; S="$SCAD_MODELER_SCRIPTS/check_strength.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; cd "$tmp"
fail=0
mkdir -p a/build/positioned; cp "$here/s1/bar.stl" a/build/positioned/
st() { cp "$here/s1/$1.json" a/loads.json; o=$(python3 "$S" --project-dir a 2>&1); r=$?; v=$(grep -oE '[0-9.]+ MPa' <<< "$o" | head -1 | cut -d' ' -f1); }
st z; sz=$v; st y; sy=$v; st yz; syz=$v
# corner stresses of a rectangle add: the oblique case must be sigma_z + sigma_y (27.3 + 2.7), not either alone
# hand values, bar 20 (y) x 2 (z), M = 7.3 N x 50 mm: sigma_z = 365 * 1 / (20*2^3/12), sigma_y = 365 * 10 / (2*20^3/12)
{ [ $r -ne 0 ] && python3 -c "import sys; z,y,yz=$sz,$sy,$syz; ok=lambda v,w: abs(v-w) <= 0.02*w; sys.exit(0 if ok(z,27.375) and ok(y,2.7375) and ok(yz,30.1125) else 1)"; } \
    || { echo "AC-1: oblique load $syz MPa != sigma_z $sz + sigma_y $sy (rc $r): $o" >&2; fail=1; }
for h in 655 670; do
    rm -rf b; mkdir -p b/build/positioned; cp "$here/s2/blk_$h.stl" b/build/positioned/blk.stl; cp "$here/s2/fasteners.json" b/
    o=$(python3 "$S" --project-dir b 2>&1); r=$?
    if [ $h = 655 ]; then [ $r -ne 0 ] && grep -q "blind depth" <<< "$o" || { echo "AC-2: 6.55 mm hole passed: $o" >&2; fail=1; }
    else grep -q "blind depth" <<< "$o" && { echo "AC-2: 6.7 mm hole flagged: $o" >&2; fail=1; }; fi
done
exit $fail
