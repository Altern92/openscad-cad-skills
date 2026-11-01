#!/usr/bin/env bash
# P2 / AC-2, AC-4, AC-5 (2026-11-01): literal-only callers, an undef default, the
# exact 44.45, a numeric default every caller overrides (post), a non-standard name and a 44.5 inside a comment/string all pass.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_scad_lint.py" --project-dir . 2>&1); rc=$?
[ "$rc" -eq 0 ] || { echo "want exit 0, got $rc" >&2; echo "$out" >&2; exit 1; }
exit 0
