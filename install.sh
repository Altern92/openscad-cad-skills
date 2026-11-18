#!/usr/bin/env bash
# Install the OpenSCAD skills (openscad-cad, scad-modeler incl. GenKit kit/gen/tests, openscad-organic)
# from GitHub -- the only source. What gets installed is exactly a commit on origin/main.
#
#   git clone https://github.com/Altern92/openscad-cad-skills.git && bash openscad-cad-skills/install.sh
#   curl -fsSL https://raw.githubusercontent.com/Altern92/openscad-cad-skills/main/install.sh | bash
#
# Usage: install.sh [--dev] [--manual-only] [--no-test] [TARGET]   (TARGET default ~/.claude/skills)
#   --dev          allow uncommitted / unpushed changes (development only; prints a WARNING)
#   --manual-only  add `disable-model-invocation: true` to openscad-cad and scad-modeler SKILL.md
#   --no-test      skip the installed regression suite
# Run from outside a clone (e.g. piped from curl), it clones/updates ${SCAD_SKILLS_SRC:-~/.local/share/openscad-cad-skills}.
# Why GitHub only: 2026-11-13 a second local copy (SSD GenKit) was synced over newer code and rolled a fix back
# (INC-2026-11-13-09).
set -euo pipefail
REPO="${SCAD_SKILLS_REPO:-https://github.com/Altern92/openscad-cad-skills.git}"
DEV=0; MANUAL=0; TEST=1; TARGET=""
for a in "$@"; do
    case "$a" in
        --dev) DEV=1 ;; --manual-only) MANUAL=1 ;; --no-test) TEST=0 ;;
        -h|--help) sed -n '2,14p' "${BASH_SOURCE[0]}"; exit 0 ;;
        -*) echo "ERROR: unknown option $a" >&2; exit 2 ;;
        *) TARGET="$a" ;;
    esac
done
TARGET="${TARGET:-$HOME/.claude/skills}"
norm() { local u="${1%.git}"; u="${u#https://}"; u="${u#git@}"; echo "${u/://}"; }

# 1. Source: this clone if its origin is $REPO, otherwise a managed clone of $REPO.
SELF=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; fi
if [ -n "$SELF" ] && git -C "$SELF" rev-parse --git-dir >/dev/null 2>&1 \
   && [ "$(norm "$(git -C "$SELF" remote get-url origin 2>/dev/null || true)")" = "$(norm "$REPO")" ]; then
    SRC="$(git -C "$SELF" rev-parse --show-toplevel)"
else
    SRC="${SCAD_SKILLS_SRC:-$HOME/.local/share/openscad-cad-skills}"
    if [ -d "$SRC/.git" ]; then
        git -C "$SRC" fetch -q origin
        if [ "$DEV" -eq 0 ]; then
            git -C "$SRC" diff --quiet HEAD || { echo "ERROR: $SRC has local changes; not installing over them" >&2; exit 1; }
            git -C "$SRC" checkout -q --detach origin/main
        fi
    else
        mkdir -p "$(dirname "$SRC")"
        git clone -q "$REPO" "$SRC"
    fi
fi

# 2. Guard: install only what is on GitHub (origin/main).
git -C "$SRC" fetch -q origin 2>/dev/null || echo "WARNING: cannot reach origin; checking against the last fetched origin/main" >&2
dirty=$(git -C "$SRC" status --porcelain --untracked-files=no)
if ! git -C "$SRC" merge-base --is-ancestor HEAD origin/main 2>/dev/null; then unpushed=1; else unpushed=0; fi
if [ -n "$dirty" ] || [ "$unpushed" -eq 1 ]; then
    if [ "$DEV" -eq 0 ]; then
        echo "ERROR: $SRC is not a commit on origin/main (uncommitted tracked changes or unpushed commits)." >&2
        [ -n "$dirty" ] && printf '%s\n' "$dirty" >&2
        echo "Commit and push first, or pass --dev for a development install." >&2
        exit 1
    fi
    echo "WARNING: deploying unpushed dev tree ($SRC) -- this is not what GitHub has" >&2
fi
for d in openscad-cad scad-modeler openscad-organic scad-modeler/kit scad-modeler/gen scad-modeler/tests/genkit; do
    [ -d "$SRC/$d" ] || { echo "ERROR: $SRC/$d missing -- not a complete checkout" >&2; exit 1; }
done

# 3. Copy.
mkdir -p "$TARGET"
for s in openscad-cad scad-modeler openscad-organic; do
    rsync -a --delete --exclude __pycache__ --exclude build --exclude SKILL.md "$SRC/$s/" "$TARGET/$s/"
    if [ "$MANUAL" -eq 1 ] && [ "$s" != openscad-organic ]; then
        awk 'NR==1{print; print "disable-model-invocation: true"; next} /^disable-model-invocation:/{next} 1' \
            "$SRC/$s/SKILL.md" > "$TARGET/$s/SKILL.md"
    else
        cp "$SRC/$s/SKILL.md" "$TARGET/$s/SKILL.md"
    fi
done
cp "$SRC/INCIDENTS.json" "$TARGET/INCIDENTS.json"
rm -f "$TARGET/INCIDENTS.md"
git -C "$SRC" rev-parse --short HEAD > "$TARGET/scad-modeler/INSTALLED_COMMIT"   # P25: validate receipts name the skill version
mkdir -p "$TARGET/references" && cp "$SRC/references/retrieval.md" "$TARGET/references/retrieval.md"   # skills read ../references/retrieval.md
echo "installed $(git -C "$SRC" rev-parse --short HEAD) from $REPO into $TARGET"

# 4. Prove it works where it was installed (includes the GenKit suite).
if [ "$TEST" -eq 1 ]; then
    out="$(cd "$TARGET/scad-modeler" && bash tests/run_all.sh 2>&1)" && rc=0 || rc=$?
    line="$(printf '%s\n' "$out" | grep '^Regression suite:' | tail -1)"
    if [ "$rc" -eq 5 ]; then
        echo "ERROR: environment gate failed (OpenSCAD or Python mesh libraries missing). Run: bash $TARGET/scad-modeler/scripts/setup_env.sh" >&2
        exit 5
    elif [ "$rc" -ne 0 ]; then
        printf '%s\n' "$out" | tail -30 >&2
        echo "ERROR: installed suite failed: ${line:-no summary}" >&2
        exit 1
    fi
    echo "installed suite: ${line#Regression suite: }"
fi
