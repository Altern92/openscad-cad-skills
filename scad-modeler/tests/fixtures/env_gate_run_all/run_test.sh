#!/usr/bin/env bash
# P1 / AC-7 (2026-11-01): with the mesh libraries missing, run_all.sh reported
# "16 passed, 32 failed" (MBP, 2026-11-01) -- a tool problem shown as 32 broken
# checkers. It must stop before any fixture with the same env message.
set -uo pipefail
[ -n "${SCAD_RUN_ALL_META:-}" ] && exit 0      # the inner run must not recurse into this fixture
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
python3 -m venv --without-pip "$tmp/bare" || exit 1
out=$(SCAD_RUN_ALL_META=1 SCAD_PYTHON="$tmp/bare/bin/python" bash "$SCAD_MODELER_SCRIPTS/../tests/run_all.sh" 2>&1); rc=$?
[ "$rc" -ne 0 ] || { echo "run_all.sh exited 0 with no mesh libraries" >&2; exit 1; }
echo "$out" | grep -q '^CHECK_RESULT env=FAIL' || { echo "no env=FAIL line" >&2; echo "$out" | tail -20 >&2; exit 1; }
echo "$out" | grep -q 'setup_env.sh' || { echo "no fix command" >&2; exit 1; }
echo "$out" | grep -q -- '^--- ' && { echo "fixtures ran despite the failed gate" >&2; echo "$out" | grep -- '^--- ' | head -3 >&2; exit 1; }
exit 0
