#!/usr/bin/env bash
# Render/validate every part under parts/ plus assembly.scad, in one call.
# Auto-discovers files (globs parts/*.scad) rather than a hand-maintained list,
# so it can't silently skip a part someone forgot to register.
#
# Usage:
#   scripts/validate_scad.sh --all              # every part + assembly.scad
#   scripts/validate_scad.sh <part_basename>     # just parts/<name>.scad
#
# Flags used below (--hardwarnings, --check-parameters, --check-parameter-ranges)
# were confirmed present via `openscad --help` on 2026-08-16 -- see
# references/setup-notes.md in this skill if that ever needs re-checking.

set -euo pipefail

OPENSCAD=${OPENSCAD:-openscad}
BUILD_DIR=${BUILD_DIR:-build}
BACKEND=${BACKEND:-Manifold}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=${1:---all}

check_openscad() {
    if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
        echo "ERROR: OpenSCAD not found ($OPENSCAD). Install it first." >&2
        exit 1
    fi
    "$OPENSCAD" --version
}

validate_file() {
    local scad="$1"
    local stl="$2"
    echo "--- Validating $scad -> $stl ---"
    mkdir -p "$(dirname "$stl")"
    "$OPENSCAD" --backend="$BACKEND" \
        --hardwarnings \
        --check-parameters=true \
        --check-parameter-ranges=true \
        -o "$stl" "$scad"
    if [ ! -s "$stl" ]; then
        echo "ERROR: STL is empty: $stl" >&2
        exit 1
    fi
    echo "OK: $(du -h "$stl" | cut -f1)"

    # Connectivity check: MANDATORY by default for parts/*.scad (not
    # assembly.scad, which is legitimately many disconnected printed parts
    # in one coordinate space). Unlike EXPECTED_BBOX/EXPECTED_HOLE this is
    # not opt-in -- a single printed part silently rendering as two
    # unconnected islands is a real, previously-uncaught failure mode
    # (INCIDENTS.md, 2026-08-19: a leg-radius fix for one collision broke
    # the legs' contact with the disc they were supposed to hold up, and
    # nothing checked for it because no check looked for it). Declare
    # `// EXPECTED_BODIES: N` in the part file for the rare intentional case.
    if [[ "$scad" == parts/* ]]; then
        python3 "$SCRIPT_DIR/check_connectivity.py" --stl "$stl" --scad "$scad"
    fi

    # Bounding-box check: only runs if the part declares an expected size via
    # `// EXPECTED_BBOX: [x, y, z]` -- catches a part that renders fine and
    # *looks* right but is subtly the wrong size (wrong -D override, a units
    # slip, a parameter that didn't thread through correctly).
    if grep -q '^[[:space:]]*//[[:space:]]*EXPECTED_BBOX' "$scad"; then
        python3 "$SCRIPT_DIR/check_dimensions.py" --stl "$stl" --scad "$scad"
    fi

    # Feature check: a bbox is nearly blind to inscribed-polygon undersizing,
    # which is what actually makes a bore too tight. Any part declaring
    # `// EXPECTED_HOLE: [x, y, z, "Z", d]` gets its bores measured
    # flat-to-flat instead.
    if grep -q '^[[:space:]]*//[[:space:]]*EXPECTED_HOLE' "$scad"; then
        python3 "$SCRIPT_DIR/check_features.py" --stl "$stl" --scad "$scad"
    fi
}

check_openscad

# Project-level checks (run once, not per part) -- both opt-in by existence,
# so a project that hasn't adopted these conventions yet isn't broken by
# them. See references/planning.md for the decisions-log Criticality
# convention and templates/service_envelope.md for the envelope fields.
# These target "wrong/unverified initial assumptions" and "service-load
# mismatch" specifically -- the two failure categories a 2026-08-19
# Perplexity failure-analysis research pass found to have the strongest
# real-world evidence as root causes, which nothing else in this chain
# checks (every other check validates geometry against the calculation
# table, not whether the calculation table's own inputs were right).
if [ -f calculations.md ]; then
    python3 "$SCRIPT_DIR/check_assumptions.py" --calc calculations.md
fi
python3 "$SCRIPT_DIR/check_service_envelope.py" --envelope service_envelope.md

# Enforces §0.5 Planning actually happened (>=2 architecture options or a
# declared exemption, a confirmed decision, every layout.scad part present
# in the plan) rather than existing only as prose a model could skip under
# pressure -- the same gap that let the rear_axle incident happen in the
# first place (INCIDENTS.md, 2026-08-18). Opt-in by plan.md's existence.
python3 "$SCRIPT_DIR/check_plan.py" --plan plan.md \
    $([ -f layout.scad ] && echo --layout layout.scad)

if [[ "$MODE" == "--all" ]]; then
    shopt -s nullglob
    parts=(parts/*.scad)
    shopt -u nullglob
    if [ ${#parts[@]} -eq 0 ]; then
        echo "WARNING: no files found under parts/*.scad" >&2
    fi
    for scad in "${parts[@]}"; do
        base="$(basename "$scad" .scad)"
        validate_file "$scad" "$BUILD_DIR/$base.stl"
    done
    if [ -f assembly.scad ]; then
        validate_file "assembly.scad" "$BUILD_DIR/assembly.stl"
    fi
else
    scad="parts/$MODE.scad"
    if [ ! -f "$scad" ]; then
        echo "ERROR: $scad not found" >&2
        exit 1
    fi
    validate_file "$scad" "$BUILD_DIR/$MODE.stl"
fi

echo "All validations passed."
