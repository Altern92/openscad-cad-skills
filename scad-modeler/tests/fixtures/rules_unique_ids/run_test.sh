#!/usr/bin/env bash
# 2026-11-18: P23 added a rule as R-23, which already existed (design constraints, manual); nothing failed.
# check_rules.py now refuses a manifest with a repeated id (exit 4); the real manifest must load.
set -uo pipefail
R="$SCAD_MODELER_SCRIPTS/check_rules.py"; M="$SCAD_MODELER_SCRIPTS/../rules_manifest.yaml"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
out=$(python3 "$R" --project-dir "$tmp" --manifest "$M" 2>&1); rc=$?
echo "$out" | grep -q "duplicate rule id" && { echo "real manifest has duplicate ids: $out" >&2; exit 1; }
[ "$rc" -ne 4 ] || { echo "real manifest refused: $out" >&2; exit 1; }
printf 'rules:\n  - {id: R-1, rule: a, applies: always, kind: manual, gate: null}\n  - {id: R-1, rule: b, applies: always, kind: manual, gate: null}\n' > "$tmp/m.yaml"
out=$(python3 "$R" --project-dir "$tmp" --manifest "$tmp/m.yaml" 2>&1); rc=$?
[ "$rc" -eq 4 ] && echo "$out" | grep -q "duplicate rule id(s).*R-1" || { echo "duplicate not refused: rc $rc $out" >&2; exit 1; }
exit 0
