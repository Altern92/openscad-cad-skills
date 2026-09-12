#!/usr/bin/env bash
# Unit test for scad_tessellation.minkowski_sphere_deficit(), which
# check_dimensions.py now depends on. Added because that module had NO test at
# all -- including after the 2026-09-12 change that made it decide whether a
# part's bounding box is wrong or merely faceted.
#
# The asserted value is not invented: it is the measured shortfall of a real
# part. server_rack_modular_v4/v8 build/node.stl renders 25.9786 against a
# declared 26.0, and 2*r*(1-cos(pi/fn)) with r = fillet_post/2 = 1.25 and
# $fn = 24 gives 0.021390. The rendered mesh differs by 2e-5 mm, which is
# float32 STL storage rounding -- hence the tolerance below.
set -uo pipefail

out=$(python3 - <<'PY' 2>&1
import math, sys
sys.path.insert(0, __import__("os").environ["SCAD_MODELER_SCRIPTS"])
import scad_tessellation as t

expected = 2 * 1.25 * (1 - math.cos(math.pi / 24))   # 0.0213902
got = t.minkowski_sphere_deficit("case_minkowski.scad")
if abs(got - expected) > 1e-4:
    print("FAIL: minkowski term %.6f, expected %.6f" % (got, expected))
    sys.exit(1)

plain = t.minkowski_sphere_deficit("case_plain.scad")
if plain != 0.0:
    print("FAIL: no minkowski() in case_plain.scad but term is %.6f" % plain)
    sys.exit(1)

unres = t.minkowski_sphere_deficit("case_unresolvable.scad")
if unres != 0.0:
    print("FAIL: unresolvable radius must be skipped, got %.6f" % unres)
    sys.exit(1)

print("OK: minkowski term %.6f (expected %.6f); plain=0.0; unresolvable=0.0" % (got, expected))
PY
)
echo "$out"

# The constant must also be what check_dimensions.py actually applies.
python3 - <<'PY' >/dev/null 2>&1
import os, sys
sys.path.insert(0, os.environ["SCAD_MODELER_SCRIPTS"])
src = open(os.path.join(os.environ["SCAD_MODELER_SCRIPTS"], "check_dimensions.py")).read()
assert "minkowski_sphere_deficit" in src, "check_dimensions.py no longer imports the term"
assert "+ mink" in src, "the term is no longer ADDED (max() drops the float32 allowance)"
PY
if [ $? -ne 0 ]; then
    echo "check_dimensions.py no longer applies the minkowski term as required" >&2
    exit 1
fi

echo "$out" | grep -q "^OK:" || exit 1
exit 0
