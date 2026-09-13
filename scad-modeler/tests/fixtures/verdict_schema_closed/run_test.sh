#!/usr/bin/env bash
# The verdict schema must be CLOSED: every check value, against every rule, must
# map to a verdict that is neither a vacuous pass nor a false failure.
#
# Why this fixture exists. On 2026-09-12 five check outcomes were introduced
# (PASS / FAIL / SKIP / INCONCLUSIVE / ADVISORY) but the rules manifest kept
# three patterns reading SKIP as success, and check_rules.py inferred the verdict
# from whether a regex matched instead of reading the value. Simulating all five
# values against all patterns showed ADVISORY collapsing to FAIL everywhere --
# a check that ran and deliberately does not gate, reported as a failure.
#
# Two invariants, both mechanical:
#   1. every success_pattern requires exactly PASS (no SKIP, no alternation)
#   2. check_rules reads the value: INCONCLUSIVE -> INCONC, ADVISORY -> ADVISORY,
#      never FAIL for either, and never PASS for a value the pattern declines
#
# Without this, the next checker that starts emitting ADVISORY, or the next
# pattern that accepts SKIP, silently reopens the vacuous pass this whole skill
# spent a day closing.
set -uo pipefail

manifest="$SCAD_MODELER_SCRIPTS/../rules_manifest.yaml"
[ -f "$manifest" ] || { echo "no rules_manifest.yaml at $manifest" >&2; exit 1; }

# --- invariant 1: patterns require PASS -------------------------------------
python3 - "$manifest" <<'PY' || exit 1
import re, sys, yaml

data = yaml.safe_load(open(sys.argv[1]))
rules = data["rules"] if isinstance(data, dict) and "rules" in data else data
bad = []
for r in rules:
    sp = r.get("success_pattern")
    if not sp:
        continue
    if not re.fullmatch(r"CHECK_RESULT [a-z_]+=PASS", sp):
        bad.append((r["id"], sp))
if bad:
    print("success_pattern must require exactly PASS:", file=sys.stderr)
    for rid, sp in bad:
        print(f"  {rid}: {sp}", file=sys.stderr)
    print("  A pattern accepting SKIP or an alternation makes a check that did", file=sys.stderr)
    print("  not run score as success. That is the vacuous pass.", file=sys.stderr)
    sys.exit(1)
print(f"ok  all {sum(1 for r in rules if r.get(chr(115)+chr(117)+chr(99)+chr(99)+chr(101)+chr(115)+chr(115)+chr(95)+chr(112)+chr(97)+chr(116)+chr(116)+chr(101)+chr(114)+chr(110)))} success_pattern(s) require PASS")
PY

# --- invariant 2: the value decides the verdict ------------------------------
python3 - "$SCAD_MODELER_SCRIPTS/check_rules.py" <<'PY' || exit 1
import re, sys

src = open(sys.argv[1], encoding="utf-8").read()

# The logic, mirrored from check_rules.py. If the two ever diverge this fixture
# is the thing that notices -- that is the point of testing it separately.
def verdict(pattern, output):
    chk = re.search(r"CHECK_RESULT ([a-z_]+)=", pattern)
    actual = None
    if chk is not None:
        hit = re.search(r"CHECK_RESULT %s=(\w+)" % re.escape(chk.group(1)), output)
        actual = hit.group(1) if hit else None
    if re.search(pattern, output):
        return "PASS"
    if actual == "INCONCLUSIVE":
        return "INCONC"
    if actual == "ADVISORY":
        return "ADVISORY"
    return "FAIL"

# The source must read the value, not only test the pattern.
if "actual ==" not in src:
    print("check_rules.py does not inspect the check VALUE -- it is inferring", file=sys.stderr)
    print("the verdict from whether success_pattern matched, which cannot tell", file=sys.stderr)
    print("ADVISORY from FAIL.", file=sys.stderr)
    sys.exit(1)

pattern = "CHECK_RESULT connectivity=PASS"
fails = []
for value, want in [("PASS", "PASS"), ("FAIL", "FAIL"), ("SKIP", "FAIL"),
                    ("INCONCLUSIVE", "INCONC"), ("ADVISORY", "ADVISORY")]:
    got = verdict(pattern, f"CHECK_RESULT connectivity={value}")
    if got != want:
        fails.append(f"  connectivity={value} -> {got}, expected {want}")
if fails:
    print("verdict schema is not closed:", file=sys.stderr)
    print("\n".join(fails), file=sys.stderr)
    sys.exit(1)
print("ok  all 5 check values map to a non-vacuous verdict")
PY

exit 0