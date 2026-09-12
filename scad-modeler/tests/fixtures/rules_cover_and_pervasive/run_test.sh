#!/usr/bin/env bash
# The rule surface must report what it did NOT exercise, and it must say so even
# when the run also fails a rule.
#
# Formal verification pairs every implication with a COVER PROPERTY on its
# antecedent and requires the cover to hit: a property whose trigger never fires
# is a verification gap, not a success. Measured 2026-09-12 across 11 real
# projects, 6 of 18 rules had NEVER had their antecedent fire -- each run
# honestly said "N/A" and the accumulation was invisible, so the rule surface was
# largely decorative while every individual report looked correct.
#
# ISA 705 is the second half: when evidence cannot be obtained and the effects
# could be material and pervasive, the auditor DISCLAIMS an opinion rather than
# giving a clean one. So the qualification has to print on both the pass and the
# fail path -- the first version put it after the early return and it never
# appeared on a failing project, which is exactly where it matters most.
set -uo pipefail

proj=$(mktemp -d)
mkdir -p "$proj/parts"
printf '%s\n' '\$fa = 2; \$fs = 0.3;' > "$proj/params.scad"
printf 'cube([10, 10, 10]);\n' > "$proj/parts/box.scad"
# An empty manifest is enough to make SOME rules applicable while most are not.
printf '{}\n' > "$proj/joints.json"

( cd "$proj" && python3 "$SCAD_MODELER_SCRIPTS/check_rules.py" --project-dir . > out 2>&1 )
code=$?
out=$(cat "$proj/out")
rm -rf "$proj"

echo "$out" | grep -q "COVER:" || {
    echo "no COVER report -- unexercised rules are invisible:" >&2
    echo "$out" >&2
    exit 1; }

# The COVER line must name the rules, not just count them: a bare number tells a
# reader nothing about which part of the surface is decoration.
echo "$out" | grep "COVER:" | grep -qE "R-[0-9]+" || {
    echo "COVER does not name the unexercised rules:" >&2
    echo "$out" | grep "COVER:" >&2
    exit 1; }

# With most rules unexercised the run has to qualify itself, and the exit code
# must not silently turn that into a pass.
if echo "$out" | grep -q "PERVASIVE:"; then
    if [ "$code" -eq 0 ]; then
        # A clean exit alongside a pervasive warning is allowed ONLY if the OK
        # line carries the count too.
        echo "$out" | grep -q "only .* of .* automated rules had their antecedent fire" || {
            echo "PERVASIVE reported but the OK line does not carry the count:" >&2
            echo "$out" | tail -4 >&2
            exit 1; }
    fi
else
    echo "expected PERVASIVE for a project where most rules never fire:" >&2
    echo "$out" | grep "COVER:" >&2
    exit 1
fi
exit 0
