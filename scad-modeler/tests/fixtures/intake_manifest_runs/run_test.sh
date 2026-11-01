#!/usr/bin/env bash
# S-4 (GenKit handoff docs/12, 2026-11-01): intake=SKIP was printed unconditionally, even
# with a design_manifest.json present, so the Stage-0 gate never gated. With a manifest the
# verdict must come from check_intake.py. requirements.json alone stays SKIP: GenKit uses that
# name for its generator input, a different schema.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "${out:-}" | grep -E "intake|CHECK_RESULT" | head >&2; exit 1; }
P="$tmp/p"; mkdir -p "$P/parts"
printf '// EXPECTED_BBOX: [5, 5, 5]\n// EXPECTED_THROUGH_HOLES: 0\ncube(5);\n' > "$P/parts/a.scad"
m() { printf '{"goal": "cube", "envelope": {"max_bounds_xyz_mm": [10, 10, 10], "is_strict": true}, "interfaces": [], "motion": {"has_kinematics": false}, "parameters": [{"name": "side", "value": 5, "unit": "mm", "status": "%s"}], "dependencies": {}}\n' "$1"; }
run() { out=$(cd "$P" && bash "$V" --all 2>&1); }
m confirmed > "$P/design_manifest.json"; run
echo "$out" | grep -q '^CHECK_RESULT intake=PASS' || die "valid manifest: not intake=PASS"
m unknown > "$P/design_manifest.json"; run
echo "$out" | grep -q '^CHECK_RESULT intake=FAIL' || die "unknown parameter: not intake=FAIL"
rm "$P/design_manifest.json"; echo '{"kind": "plate"}' > "$P/requirements.json"; run
echo "$out" | grep -q '^CHECK_RESULT intake=SKIP' || die "requirements.json only: not SKIP"
exit 0
