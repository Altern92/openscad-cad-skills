#!/usr/bin/env bash
# Radius forms scad_tessellation.minkowski_sphere_deficit() resolves beyond
# 'r = name/number' (NEXT.md 3b item 3), and forms it must still SKIP. Every
# expected value is the module's own formula 2*r*(1-cos(pi/n)) evaluated by
# hand; a skipped form must give exactly 0.0, never a guessed radius.
set -uo pipefail

out=$(python3 - <<'PY' 2>&1
import math, os, sys
sys.path.insert(0, os.environ["SCAD_MODELER_SCRIPTS"])
import scad_tessellation as t

def term(r, n):
    return 2 * r * (1 - math.cos(math.pi / n))

# global_fafs: $fa = 12 (file), $fs = 0.5 (sphere), r = 1
# -> ceil(max(min(360/12, 2*pi*1/0.5), 5)) = ceil(12.566) = 13 facets.
cases = {
    "literal_arith.scad": term(0.75, 16),
    "diameter.scad":      term(1.25, 24),
    "positional.scad":    term(1.5, 48),
    "scalar_arith.scad":  term(0.95, 20),
    "include_expr.scad":  term(0.75, 12),
    "global_fafs.scad":   term(1.0, 13),
    "skip_module_param.scad": 0.0,
    "skip_module_no_fn.scad": 0.0,
    "skip_function.scad":     0.0,
    "skip_use.scad":          0.0,
}
bad = 0
for f, want in cases.items():
    got = t.minkowski_sphere_deficit(f)
    if abs(got - want) > 1e-6:
        print("FAIL: %s term %.7f, expected %.7f" % (f, got, want))
        bad += 1
if bad:
    sys.exit(1)
print("OK: %d radius forms (6 resolved, 4 skipped)" % len(cases))
PY
)
echo "$out"
grep -q <<< "$out" "^OK:" || exit 1
exit 0
