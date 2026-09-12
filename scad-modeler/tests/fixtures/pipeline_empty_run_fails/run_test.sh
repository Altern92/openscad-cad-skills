#!/usr/bin/env bash
# A validation run that rendered nothing must not report success.
#
# Measured 2026-09-12 (adversarial review): a project laid out exactly as
# templates/README.md then instructed -- files under scad/ -- produced
#   WARNING: no files found under parts/*.scad
#   COVERAGE: 4 passed, 0 failed, 13 skipped (17 checks reported).
#   All validations passed.
# exit 0, with zero parts rendered, measured or checked. The README and
# SKILL.md also disagreed about where the files go, which is what made the
# layout look correct.
#
# Both halves are asserted: the run fails, AND it says what is wrong.
set -uo pipefail

proj=$(mktemp -d)
mkdir -p "$proj/scad/parts"
printf '%s\n' '\$fa = 2; \$fs = 0.3;' > "$proj/scad/params.scad"
printf 'cube([10, 10, 10]);\n' > "$proj/scad/parts/panel.scad"

( cd "$proj" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all > out 2>&1 )
code=$?
out=$(cat "$proj/out")
rm -rf "$proj"

if [ "$code" -eq 0 ]; then
    echo "a run that checked nothing exited 0:" >&2
    echo "$out" >&2
    exit 1
fi
echo "$out" | grep -q "NOTHING was rendered or checked" || {
    echo "expected an explicit nothing-was-checked error, got:" >&2
    echo "$out" >&2
    exit 1; }
echo "$out" | grep -q "scad/parts/" || {
    echo "expected the error to name the scad/parts/ layout it found instead:" >&2
    echo "$out" >&2
    exit 1; }
exit 0
