#!/usr/bin/env bash
# P1 / AC-6 (2026-11-01): one command makes the interpreter the env gate asks
# for. It installs exactly what doctor.py checks (no second list to drift),
# and a second run changes nothing. SCAD_VENV redirects the target for the test.
set -uo pipefail
command -v uv >/dev/null || { echo "uv not installed -- cannot test setup_env.sh" >&2; exit 1; }
S="$SCAD_MODELER_SCRIPTS"
[ -f "$S/setup_env.sh" ] || { echo "missing $S/setup_env.sh" >&2; exit 1; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
v="$tmp/venv"

out=$(SCAD_VENV="$v" bash "$S/setup_env.sh" 2>&1); rc=$?
[ "$rc" -eq 0 ] || { echo "first run exit $rc" >&2; echo "$out" >&2; exit 1; }
miss=$("$v/bin/python" -c "
import json,subprocess,sys
r=json.loads(subprocess.run([sys.executable,'$S/doctor.py','--json'],capture_output=True,text=True).stdout)
print(' '.join(m for m,d in r['python'].items() if d['status']!='ok'))")
[ -z "$miss" ] || { echo "after setup, doctor still reports missing: $miss" >&2; exit 1; }

before=$(ls -i "$v/pyvenv.cfg" | awk '{print $1}')
out=$(SCAD_VENV="$v" bash "$S/setup_env.sh" 2>&1); rc=$?
[ "$rc" -eq 0 ] || { echo "second run exit $rc" >&2; echo "$out" >&2; exit 1; }
after=$(ls -i "$v/pyvenv.cfg" | awk '{print $1}')
[ "$before" = "$after" ] || { echo "second run recreated the venv" >&2; exit 1; }
echo "$out" | grep -qi 'already' || { echo "second run did not say the env was already complete" >&2; echo "$out" >&2; exit 1; }
exit 0
