#!/usr/bin/env bash
# P18 follow-up (2026-11-01): agents read the whole validator log, and OpenSCAD's cache and
# mesh statistics were ~10 lines per render that no check uses. Default output drops them;
# WARNING/ERROR/ECHO and every CHECK_RESULT stay. SCAD_VERBOSE=1 restores the full log.
set -uo pipefail
V="$SCAD_MODELER_SCRIPTS/validate_scad.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
die() { echo "$1" >&2; echo "$out" | head -40 >&2; exit 1; }
P="$tmp/p"; mkdir -p "$P/parts"
printf '// EXPECTED_BBOX: [10, 10, 5]\n// EXPECTED_THROUGH_HOLES: 0\necho("HELLO_ECHO");\ncube([10, 10, 5]);\n' > "$P/parts/a.scad"
printf 'MODE = is_undef(MODE) ? "assembly" : MODE;\nPART = is_undef(PART) ? "" : PART;\nuse <parts/a.scad>\nif (MODE == "assembly" || PART == "a") include <parts/a.scad>\n' > "$P/assembly.scad"
noise='Geometries in cache|CGAL Polyhedrons in cache|Total rendering time|Genus:|Facets:'
out=$(cd "$P" && bash "$V" --all 2>&1)
echo "$out" | grep -qE "$noise" && die "default log still has OpenSCAD cache/mesh statistics"
echo "$out" | grep -q 'HELLO_ECHO' || die "ECHO line lost"
echo "$out" | grep -q '^CHECK_RESULT render=PASS' || die "render verdict lost"
echo "$out" | grep -q '^CHECK_RESULT dimensions=PASS' || die "dimensions verdict lost"
out=$(cd "$P" && SCAD_VERBOSE=1 bash "$V" --all 2>&1)
echo "$out" | grep -qE "$noise" || die "SCAD_VERBOSE=1 did not restore the full log"
exit 0
