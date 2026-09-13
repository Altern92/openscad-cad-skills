#!/usr/bin/env bash
# ab_tooling.sh -- run two versions of validate_scad.sh against the same projects
# and write both raw outputs, so the difference can be counted instead of argued
# about.
#
#   ab_tooling.sh <projects_root> <out_dir> [PRE_scripts_dir]
#
# <projects_root> is scanned for assembly.scad (skipping build/), and each
# directory containing one is treated as a project.
#
# POST defaults to this repo's scad-modeler/scripts. PRE, if given, is another
# copy of those scripts (an older revision). With no PRE the script just records
# the current behaviour, which is still useful as a baseline to diff later.
#
# Why this exists: agent-based before/after tests cannot settle whether a change
# helped -- the variance is larger than the effect below roughly 120 tasks per
# arm. Removing the agent removes the variance. See tests/tools/README.md.
set -uo pipefail

ROOT=${1:?usage: ab_tooling.sh <projects_root> <out_dir> [PRE_scripts_dir]}
OUT=${2:?usage: ab_tooling.sh <projects_root> <out_dir> [PRE_scripts_dir]}
MINE=$(cd "$(dirname "$0")/../.." && pwd)          # scad-modeler/
POST=${POST:-$MINE/scripts}
PRE=${3:-}

[ -d "$ROOT" ] || { echo "no such projects root: $ROOT" >&2; exit 2; }
[ -f "$POST/validate_scad.sh" ] || { echo "no validate_scad.sh in POST=$POST" >&2; exit 2; }
if [ -n "$PRE" ] && [ ! -f "$PRE/validate_scad.sh" ]; then
    echo "no validate_scad.sh in PRE=$PRE" >&2; exit 2
fi

mkdir -p "$OUT/post"
[ -n "$PRE" ] && mkdir -p "$OUT/pre"

( cd "$ROOT" && find . -name assembly.scad -not -path "*/build/*" \
    | sed "s|/assembly.scad$||" | sort ) > "$OUT/projects.txt"
n=$(wc -l < "$OUT/projects.txt" | tr -d " ")
[ "$n" -gt 0 ] || { echo "no projects found under $ROOT" >&2; exit 1; }
echo "projects: $n   POST: $POST   PRE: ${PRE:-<none>}"

while read -r d; do
    [ -n "$d" ] || continue
    slug=$(echo "$d" | sed "s|^\./||; s|/|_|g")
    if [ -n "$PRE" ]; then
        ( cd "$ROOT/$d" && bash "$PRE/validate_scad.sh" --all ) > "$OUT/pre/$slug.log" 2>&1
        echo "  pre  $slug exit=$?"
    fi
    ( cd "$ROOT/$d" && bash "$POST/validate_scad.sh" --all ) > "$OUT/post/$slug.log" 2>&1
    echo "  post $slug exit=$?"
done < "$OUT/projects.txt"

echo "wrote $OUT/{pre,post}/*.log  -- now: python3 ab_analyze.py $OUT"