#!/usr/bin/env bash
# doctor.py asserts what THIS machine can do instead of what the docs claim it
# can. Two things must hold on any machine: it exits with one of its three
# documented codes, and --json emits parseable JSON. A crash here would make
# every "OpenSCAD is installed" claim in the docs unfounded.
set -uo pipefail
out=$(python3 "$SCAD_MODELER_SCRIPTS/doctor.py" --json 2>&1)
actual=$?
case "$actual" in
  0|2|3) : ;;
  *) echo "doctor.py exited $actual, expected 0 (ok), 2 (degraded) or 3 (critical)" >&2
     echo "$out" >&2; exit 1 ;;
esac
echo "$out" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert isinstance(d, dict), 'doctor --json must emit an object'
if not d:
    print('doctor --json returned an empty object'); sys.exit(1)
" || { echo "doctor --json is not valid JSON:" >&2; echo "$out" >&2; exit 1; }
exit 0
