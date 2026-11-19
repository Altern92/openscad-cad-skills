#!/usr/bin/env bash
# P26 / AC-15 (Fable audit e8): validate_scad.sh greps a declaration loosely and runs its checker;
# the checker's strict parser read nothing and printed "skipping" with exit 0, so a placeholder
# `// EXPECTED_BBOX: [L, W, H]` passed as a measured size. An unreadable declaration is a FAIL.
set -uo pipefail
S="$SCAD_MODELER_SCRIPTS"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cd "$tmp"; mkdir -p parts
fail=0
openscad --backend=Manifold -o a.stl <(echo 'cube(10);') 2>/dev/null || openscad -o a.stl /dev/stdin <<< 'cube(10);' 2>/dev/null
[ -s a.stl ] || { echo "setup: could not render a.stl" >&2; exit 1; }
chk() {  # $1 script, $2 decl line, $3 want rc (non-zero) or 0
    printf '%s\ncube(10);\n' "$2" > a.scad
    o=$(python3 "$S/$1" --stl a.stl --scad a.scad 2>&1); r=$?
    if [ "$3" = 0 ]; then
        [ $r -eq 0 ] || { echo "$1 '$2': want pass, got $r: $o" >&2; fail=1; }
    else
        [ $r -ne 0 ] && grep -q <<< "$o" "cannot read declaration" || { echo "$1 '$2': unreadable declaration passed (rc $r): $o" >&2; fail=1; }
    fi
}
chk check_dimensions.py '// EXPECTED_BBOX: [L, W, H]' 1
chk check_dimensions.py '// EXPECTED_BBOX: [10, 10, 10]' 0
chk check_dimensions.py '// EXPECTED_BBOX_TOL: 0.01' 0
chk check_topology.py '// EXPECTED_THROUGH_HOLES: none' 1
chk check_topology.py '// EXPECTED_THROUGH_HOLES: 0' 0
chk check_features.py '// EXPECTED_HOLE: [0, 0, 5, "Z", d]' 1
chk check_sensitivity.py '// SENSITIVE_TO: 3mm' 1
exit $fail
