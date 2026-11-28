#!/usr/bin/env bash
# P25 / AC-9, AC-10 (2026-11-18): metamorphic tests. A checker's verdict is a property of the assembly,
# not of where it sits: moving and turning the whole thing (meshes AND declared coordinates) must give
# the same lines and numbers (3 seeds). Moving only the meshes must change them, or the comparison
# proves nothing. Section properties must match the closed forms (bh^3/12, pi(D^4-d^4)/64).
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; M="$here/meta.py"; S="$SCAD_MODELER_SCRIPTS"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
fail=0
# strength: inserts + loads (the strength_gates set)
mkdir -p "$t/s0"; python3 "$here/../strength_gates/make_stls.py" "$t/s0/build/positioned" || exit 1
cp "$here/../strength_gates/fasteners.json" "$here/../strength_gates/loads.json" "$t/s0/"
python3 "$S/check_strength.py" --project-dir "$t/s0" > "$t/s0.txt" 2>&1
grep -q "STRENGTH: 6 insert" "$t/s0.txt" || { echo "baseline strength run broken"; cat "$t/s0.txt"; exit 1; }
# fasteners: the head-crossing block/cover pair (one FAIL) and the clean pair (PASS)
for fx in fasteners_head_cross_fail fasteners_pass; do
    mkdir -p "$t/$fx"; cp "$here/../$fx"/*.scad "$here/../$fx/fasteners.json" "$t/$fx/"
    ( cd "$t/$fx"; openscad --backend=Manifold --render -o block.stl block.scad >/dev/null 2>&1
      [ $fx = fasteners_pass ] && h="-D HEAD_HOLE=true" || h=""
      openscad --backend=Manifold --render $h -o cover.stl cover.scad >/dev/null 2>&1; rm -f *.scad )
done
fast() { ( cd "$1" && python3 "$S/check_fasteners.py" --fasteners fasteners.json block.stl cover.stl 2>&1 ); }
for fx in fasteners_head_cross_fail fasteners_pass; do fast "$t/$fx" > "$t/$fx.txt"; done
for seed in 1 2 3; do
    python3 "$M" transform "$t/s0" "$t/s$seed" $seed
    python3 "$S/check_strength.py" --project-dir "$t/s$seed" > "$t/s$seed.txt" 2>&1
    python3 "$M" compare "$t/s0.txt" "$t/s$seed.txt" >/dev/null || { echo "AC-9 strength, seed $seed:"; python3 "$M" compare "$t/s0.txt" "$t/s$seed.txt"; fail=1; }
    for fx in fasteners_head_cross_fail fasteners_pass; do
        python3 "$M" transform "$t/$fx" "$t/$fx.$seed" $seed
        fast "$t/$fx.$seed" > "$t/$fx.$seed.txt"
        python3 "$M" compare "$t/$fx.txt" "$t/$fx.$seed.txt" >/dev/null || { echo "AC-9 $fx, seed $seed:"; python3 "$M" compare "$t/$fx.txt" "$t/$fx.$seed.txt"; fail=1; }
    done
done
# negative: meshes moved, declarations not -> the verdicts must change
python3 "$M" transform "$t/s0" "$t/neg" 1 --geometry-only
python3 "$S/check_strength.py" --project-dir "$t/neg" > "$t/neg.txt" 2>&1
python3 "$M" compare "$t/s0.txt" "$t/neg.txt" >/dev/null && { echo "AC-9: geometry-only move gave the same result -- the comparison cannot fail"; fail=1; }
python3 "$M" sections "$S" || fail=1
exit $fail
