#!/usr/bin/env bash
# H5 (2026-11-14): install.sh installs only a commit on origin/main. Builds a throwaway repo from the
# CURRENT working tree (so an uncommitted install.sh is what gets tested), with a local bare repo as
# its "GitHub", and checks: clean clone installs (GenKit included), a dirty tracked file and an
# unpushed commit are refused with an empty target, --dev overrides, and the no-clone path
# (piped from curl) clones from the repo URL.
set -uo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
rsync -a --exclude .git --exclude __pycache__ --exclude build "$SRC/" "$t/work/"
git init -q --bare "$t/bare.git"
( cd "$t/work" && git init -q -b main && git add -A && git -c user.name=t -c user.email=t@t commit -qm init \
  && git remote add origin "$t/bare.git" && git push -q origin main ) || { echo "test_install: setup failed" >&2; exit 1; }
export SCAD_SKILLS_REPO="$t/bare.git"
fail() { echo "test_install: $*" >&2; exit 1; }

bash "$t/work/install.sh" --no-test "$t/a" >/dev/null 2>&1 || fail "clean clone: install failed"
[ -f "$t/a/scad-modeler/kit/lib.scad" ] && [ -f "$t/a/scad-modeler/tests/genkit/run_all.sh" ] \
    && [ -f "$t/a/scad-modeler/gen/emit_part.py" ] || fail "clean clone: GenKit not installed"
grep -q "^disable-model-invocation" "$t/a/openscad-cad/SKILL.md" && fail "plain install must not add disable-model-invocation"
bash "$t/work/install.sh" --no-test --manual-only "$t/m" >/dev/null 2>&1 && grep -q "^disable-model-invocation: true" "$t/m/openscad-cad/SKILL.md" \
    || fail "--manual-only did not mark openscad-cad"

echo "# dirty" >> "$t/work/scad-modeler/SKILL.md"
bash "$t/work/install.sh" --no-test "$t/b" >/dev/null 2>&1 && fail "dirty tree: install did not refuse"
[ -e "$t/b" ] && fail "dirty tree: target was written"
o=$(bash "$t/work/install.sh" --no-test --dev "$t/d" 2>&1)
echo "$o" | grep -q 'WARNING: deploying unpushed dev tree' || fail "--dev: no WARNING: $o"
[ -f "$t/d/scad-modeler/SKILL.md" ] || fail "--dev: nothing installed"

( cd "$t/work" && git -c user.name=t -c user.email=t@t commit -qam local ) || fail "setup commit"
bash "$t/work/install.sh" --no-test "$t/c" >/dev/null 2>&1 && fail "unpushed commit: install did not refuse"
[ -e "$t/c" ] && fail "unpushed commit: target was written"

SCAD_SKILLS_SRC="$t/managed" bash -s -- --no-test "$t/p" < "$t/work/install.sh" >/dev/null 2>&1 || fail "piped install failed"
[ -f "$t/p/scad-modeler/kit/lib.scad" ] && [ -d "$t/managed/.git" ] || fail "piped install did not clone from the repo URL"
grep -q '# dirty' "$t/p/scad-modeler/SKILL.md" && fail "piped install took the local tree, not origin/main"
echo "test_install: 6/6 OK"
