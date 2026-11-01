#!/usr/bin/env bash
# P1 / AC-3, AC-4, AC-5 (2026-11-01). Without the mesh libraries, validate_scad.sh
# used to report connectivity=FAIL, mechanics=FAIL, collisions=INCONCLUSIVE and
# without BOSL2 render=FAIL -- tool problems that read as geometry verdicts. The
# env gate must stop first: one `CHECK_RESULT env=FAIL`, the reason, the fix
# command, no other CHECK_RESULT line, exit 5.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
GOOD_PY=$(bash "$SCAD_MODELER_SCRIPTS/resolve_python.sh" --print)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
mkdir -p "$tmp/plain/parts" "$tmp/bosl/parts" "$tmp/home"
echo 'cube(10);' > "$tmp/plain/parts/cube.scad"
printf 'include <BOSL2/std.scad>\ncuboid(10);\n' > "$tmp/bosl/parts/box.scad"
python3 -m venv --without-pip "$tmp/bare" || { echo "cannot make bare venv" >&2; exit 1; }

expect_gate_fail() {  # $1 label, $2 output, $3 rc, $4.. words that must appear
    local label=$1 out=$2 rc=$3; shift 3
    [ "$rc" -eq 5 ] || { echo "$label: expected exit 5, got $rc" >&2; echo "$out" >&2; exit 1; }
    echo "$out" | grep -q '^CHECK_RESULT env=FAIL' || { echo "$label: no env=FAIL line" >&2; echo "$out" >&2; exit 1; }
    n=$(echo "$out" | grep -c '^CHECK_RESULT ')
    [ "$n" -eq 1 ] || { echo "$label: $n CHECK_RESULT lines, want only env" >&2; echo "$out" >&2; exit 1; }
    for w in "$@"; do echo "$out" | grep -q -- "$w" || { echo "$label: output lacks '$w'" >&2; echo "$out" >&2; exit 1; }; done
}

# AC-3: interpreter without trimesh & co.
out=$(cd "$tmp/plain" && SCAD_PYTHON="$tmp/bare/bin/python" bash "$V" --all 2>&1); rc=$?
expect_gate_fail AC-3 "$out" $rc trimesh shapely setup_env.sh

# AC-4: no OpenSCAD
out=$(cd "$tmp/plain" && SCAD_PYTHON="$GOOD_PY" OPENSCAD=/nonexistent/openscad bash "$V" --all 2>&1); rc=$?
expect_gate_fail AC-4 "$out" $rc OpenSCAD /nonexistent/openscad

# AC-5: project includes BOSL2, none installed (empty HOME, no OPENSCADPATH)
out=$(cd "$tmp/bosl" && SCAD_PYTHON="$GOOD_PY" HOME="$tmp/home" OPENSCADPATH= bash "$V" --all 2>&1); rc=$?
expect_gate_fail AC-5 "$out" $rc BOSL2 parts/box.scad

# AC-5 boundary: a missing library the project does NOT include must not stop the run
out=$(cd "$tmp/plain" && SCAD_PYTHON="$GOOD_PY" HOME="$tmp/home" OPENSCADPATH= bash "$V" --all 2>&1); rc=$?
[ "$rc" -ne 5 ] || { echo "boundary: gate stopped a project that includes no library" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q '^CHECK_RESULT env=PASS' || { echo "boundary: no env=PASS line" >&2; echo "$out" >&2; exit 1; }
echo "$out" | grep -q "^ENV python=$GOOD_PY" || { echo "AC-2: no 'ENV python=' line" >&2; echo "$out" >&2; exit 1; }
exit 0
