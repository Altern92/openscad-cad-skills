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
#
# FAILURE POLICY (changed 2026-08-19, see INCIDENTS.md): this script does NOT
# stop at the first failure. An earlier version used `set -e`, so an
# unrelated early failure (e.g. an unresolved Critical assumption in
# calculations.md) aborted the whole run before connectivity, bore-
# reachability or mechanics checks ever executed -- and there was no way to
# tell "this check failed" from "this check never ran" from the exit code
# alone. That produced a real, confirmed failure mode: a model reported
# "R-04/R-09 show FAIL, but I manually verified the geometry separately" --
# an unverified self-assessment standing in for a gate that never actually
# ran, exactly what the whole rules-enforcement design exists to prevent.
# Every independent check below now runs regardless of earlier failures,
# and the script emits one machine-parseable `CHECK_RESULT <name>=STATUS`
# line per independent check (STATUS is PASS, FAIL, or SKIP) so a caller
# (check_rules.py) can determine one specific check's real verdict without
# it being conflated with an unrelated failure elsewhere in the same run.
# The script's own exit code is non-zero if ANYTHING failed, for a human
# running it directly.

set -uo pipefail

OPENSCAD=${OPENSCAD:-openscad}
BUILD_DIR=${BUILD_DIR:-build}
BACKEND=${BACKEND:-Manifold}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE=${1:---all}

OVERALL_FAIL=0

check_openscad() {
    # Fatal, unlike everything below: no check in this script can produce a
    # meaningful result without OpenSCAD, so there is nothing to gain by
    # continuing past this one.
    if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
        echo "ERROR: OpenSCAD not found ($OPENSCAD). Install it first." >&2
        exit 1
    fi
    "$OPENSCAD" --version
}

# validate_file: renders one .scad file and runs its per-part checks.
# Returns 0/1 (does NOT exit) so the caller can continue to the next part
# even if this one fails -- sets PART_CONNECTIVITY_FAIL=1 on a connectivity
# failure specifically (read by the caller to build the aggregate
# CHECK_RESULT connectivity= line).
PART_CONNECTIVITY_FAIL=0

validate_file() {
    local scad="$1"
    local stl="$2"
    local this_failed=0
    echo "--- Validating $scad -> $stl ---"
    mkdir -p "$(dirname "$stl")"
    if ! "$OPENSCAD" --backend="$BACKEND" \
        --hardwarnings \
        --check-parameters=true \
        --check-parameter-ranges=true \
        -o "$stl" "$scad"; then
        echo "ERROR: render failed: $scad" >&2
        return 1
    fi
    if [ ! -s "$stl" ]; then
        echo "ERROR: STL is empty: $stl" >&2
        return 1
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
        if ! python3 "$SCRIPT_DIR/check_connectivity.py" --stl "$stl" --scad "$scad"; then
            PART_CONNECTIVITY_FAIL=1
            this_failed=1
        fi
    fi

    # Bounding-box check: only runs if the part declares an expected size via
    # `// EXPECTED_BBOX: [x, y, z]` -- catches a part that renders fine and
    # *looks* right but is subtly the wrong size (wrong -D override, a units
    # slip, a parameter that didn't thread through correctly).
    if grep -q '^[[:space:]]*//[[:space:]]*EXPECTED_BBOX' "$scad"; then
        python3 "$SCRIPT_DIR/check_dimensions.py" --stl "$stl" --scad "$scad" || this_failed=1
    fi

    # Feature check: a bbox is nearly blind to inscribed-polygon undersizing,
    # which is what actually makes a bore too tight. Any part declaring
    # `// EXPECTED_HOLE: [x, y, z, "Z", d]` gets its bores measured
    # flat-to-flat instead.
    if grep -q '^[[:space:]]*//[[:space:]]*EXPECTED_HOLE' "$scad"; then
        python3 "$SCRIPT_DIR/check_features.py" --stl "$stl" --scad "$scad" || this_failed=1
    fi

    return $this_failed
}

check_openscad

# Analytic pre-flight gate (added 2026-08-21, see INCIDENTS.md): runs FIRST,
# before any part is rendered. Evaluates every assert() in params.scad --
# where declared clearances/interferences should be checked algebraically
# against confirmed parameters (e.g. r1+r2+clearance <= center_distance) --
# at near-zero cost, since no real geometry is rendered. This exists because
# the single most expensive class of defect found this project (a 12-round
# investigation into a hidden collision) was PURELY algebraic: two circular
# features' outer radii summed to more than their actual center distance, a
# one-line assert() away from being caught for free instead of requiring a
# full mesh export + Python collision analysis + human interpretation.
#
# Mechanism: OpenSCAD's assert() failure does NOT change the process exit
# code on its own (confirmed directly) -- only combined with --hardwarnings
# turning the resulting "Current top level object is empty" into a hard
# failure does it become detectable via exit code. But a bare params.scad
# with no geometry ALSO trips that same "empty object" warning even when
# every assert() passes, which would make this gate always fail regardless
# of correctness. Fixed by wrapping params.scad with a trivial placeholder
# solid (cube(1)) that only renders if every assert() above it passed --
# confirmed directly: a passing wrapper renders the cube (exit 0), a failing
# assert halts evaluation before the cube statement is ever reached (exit 1,
# no output file), both verified against real assert-pass/assert-fail cases.
if [ -f params.scad ]; then
    mkdir -p "$BUILD_DIR"
    tmp_wrapper=$(mktemp -t analytic_preflight_XXXXXX.scad)
    trap 'rm -f "$tmp_wrapper"' EXIT
    printf 'include <%s/params.scad>\ncube(1);\n' "$PWD" > "$tmp_wrapper"
    preflight_log=$(mktemp -t analytic_preflight_log_XXXXXX)
    if "$OPENSCAD" --backend="$BACKEND" --hardwarnings \
        -o "$BUILD_DIR/.analytic_preflight.stl" "$tmp_wrapper" > "$preflight_log" 2>&1; then
        echo "CHECK_RESULT analytic_bounds=PASS"
    else
        echo "CHECK_RESULT analytic_bounds=FAIL"
        echo "FAIL: an assert() in params.scad failed -- fix the source parameters" >&2
        echo "before any part is rendered, not after:" >&2
        grep -E "^ERROR: Assertion" "$preflight_log" >&2 || cat "$preflight_log" >&2
        OVERALL_FAIL=1
    fi
    rm -f "$tmp_wrapper" "$preflight_log" "$BUILD_DIR/.analytic_preflight.stl"
else
    echo "CHECK_RESULT analytic_bounds=SKIP"
fi

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
#
# These run and are reported, but -- per the failure policy above -- do NOT
# prevent the geometry checks below from running too.
if [ -f calculations.md ]; then
    if python3 "$SCRIPT_DIR/check_assumptions.py" --calc calculations.md; then
        echo "CHECK_RESULT assumptions=PASS"
    else
        echo "CHECK_RESULT assumptions=FAIL"
        OVERALL_FAIL=1
    fi
else
    echo "CHECK_RESULT assumptions=SKIP"
fi

if python3 "$SCRIPT_DIR/check_service_envelope.py" --envelope service_envelope.md; then
    echo "CHECK_RESULT service_envelope=PASS"
else
    echo "CHECK_RESULT service_envelope=FAIL"
    OVERALL_FAIL=1
fi

# Enforces §0.5 Planning actually happened (>=2 architecture options or a
# declared exemption, a confirmed decision, every layout.scad part present
# in the plan) rather than existing only as prose a model could skip under
# pressure -- the same gap that let the rear_axle incident happen in the
# first place (INCIDENTS.md, 2026-08-18). Opt-in by plan.md's existence.
if python3 "$SCRIPT_DIR/check_plan.py" --plan plan.md \
    $([ -f layout.scad ] && echo --layout layout.scad); then
    echo "CHECK_RESULT plan=PASS"
else
    echo "CHECK_RESULT plan=FAIL"
    OVERALL_FAIL=1
fi

if [[ "$MODE" == "--all" ]]; then
    shopt -s nullglob
    parts=(parts/*.scad)
    shopt -u nullglob
    if [ ${#parts[@]} -eq 0 ]; then
        echo "WARNING: no files found under parts/*.scad" >&2
    fi
    # ${parts[@]+"${parts[@]}"} not "${parts[@]}": bash 3.2 (macOS's default
    # /bin/bash, frozen at GPLv2, no bash 4.4+) treats a plain "${array[@]}"
    # expansion of a declared-but-empty array as an unbound variable under
    # `set -u`, even though ${#parts[@]} correctly reports 0 -- confirmed by
    # hitting this directly (INCIDENTS.md, 2026-08-19). This idiom is the
    # standard cross-version-safe empty-array guard.
    for scad in ${parts[@]+"${parts[@]}"}; do
        base="$(basename "$scad" .scad)"
        validate_file "$scad" "$BUILD_DIR/$base.stl" || OVERALL_FAIL=1
    done
    if [ -f assembly.scad ]; then
        validate_file "assembly.scad" "$BUILD_DIR/assembly.stl" || OVERALL_FAIL=1
    fi

    if [ ${#parts[@]} -eq 0 ]; then
        echo "CHECK_RESULT connectivity=SKIP"
    elif [ "$PART_CONNECTIVITY_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT connectivity=PASS"
    else
        echo "CHECK_RESULT connectivity=FAIL"
    fi

    # Bore-reachability check: opt-in via a project-root bores.json declaring
    # each bearing/shaft/fastener bore's axis segment (see §0.6 in SKILL.md
    # for why -- a sealed bore passes every other check here, since a fully
    # enclosed cavity is still one connected watertight shell). Runs once
    # against every rendered part STL, after the parts loop above so the
    # STLs it needs already exist.
    if [ -f bores.json ]; then
        shopt -s nullglob
        built_stls=("$BUILD_DIR"/*.stl)
        shopt -u nullglob
        if [ ${#built_stls[@]} -gt 0 ]; then
            if python3 "$SCRIPT_DIR/check_bore_reachability.py" --bores bores.json ${built_stls[@]+"${built_stls[@]}"}; then
                echo "CHECK_RESULT bore_reachability=PASS"
            else
                echo "CHECK_RESULT bore_reachability=FAIL"
                OVERALL_FAIL=1
            fi
        else
            echo "CHECK_RESULT bore_reachability=SKIP"
        fi
    fi

    # Mechanics auto-trigger: opt-in via joints.json declaring a non-empty
    # "motion" array (motion_sweep.py's own documented convention -- see its
    # docstring, NOT design_manifest.json.motion, which two of this skill's
    # own reference docs proposed independently and inconsistently with each
    # other and with this already-tested script; joints.json is the one
    # that's real). When present: static collision detection is ALWAYS the
    # precondition of the dynamic sweep (a sweep over geometry that already
    # collides at rest is meaningless -- references/validation_decision_tree.md),
    # so both run here, in that order, automatically -- closing the gap where
    # a moving assembly could pass validate_scad.sh --all without either ever
    # having been run by anyone remembering to.
    #
    # Both checks need each part positioned in the shared assembly coordinate
    # system, not the per-part local-origin STLs the loop above produces
    # (SKILL.md §4) -- so this renders one positioned STL per part via
    # assembly.scad's MODE="part"/PART="<name>" switch (SKILL.md §6) before
    # calling either check.
    mechanics_ran=0
    if [ -f joints.json ] && [ -f assembly.scad ]; then
        has_motion=$(python3 -c "
import json, sys
try:
    d = json.load(open('joints.json'))
except Exception:
    sys.exit(1)
motion = d.get('motion') if isinstance(d, dict) else None
sys.exit(0 if motion else 1)
" && echo yes || echo no)
        if [ "$has_motion" = "yes" ]; then
            mechanics_ran=1
            echo "--- Mechanics: joints.json declares motion -- rendering positioned parts for static+dynamic checks ---"
            mkdir -p "$BUILD_DIR/positioned"
            shopt -s nullglob
            positioned_stls=()
            for scad in ${parts[@]+"${parts[@]}"}; do
                base="$(basename "$scad" .scad)"
                pstl="$BUILD_DIR/positioned/$base.stl"
                if "$OPENSCAD" --backend="$BACKEND" --hardwarnings \
                    -D 'MODE="part"' -D "PART=\"$base\"" \
                    -o "$pstl" assembly.scad && [ -s "$pstl" ]; then
                    positioned_stls+=("$pstl")
                fi
            done
            shopt -u nullglob
            if [ ${#positioned_stls[@]} -ge 2 ]; then
                mech_fail=0
                python3 "$SCRIPT_DIR/check_collisions.py" --expected-contacts joints.json \
                    ${positioned_stls[@]+"${positioned_stls[@]}"} || mech_fail=1
                python3 "$SCRIPT_DIR/motion_sweep.py" --joints joints.json \
                    ${positioned_stls[@]+"${positioned_stls[@]}"} || mech_fail=1
                if [ "$mech_fail" -eq 0 ]; then
                    echo "CHECK_RESULT mechanics=PASS"
                else
                    echo "CHECK_RESULT mechanics=FAIL"
                    OVERALL_FAIL=1
                fi
            else
                echo "WARNING: joints.json declares motion but fewer than 2 parts rendered via MODE=\"part\" -- skipping mechanics checks. Check that assembly.scad's MODE/PART switch matches SKILL.md §6 and that parts/*.scad basenames match layout.scad's part names." >&2
                echo "CHECK_RESULT mechanics=FAIL"
                OVERALL_FAIL=1
            fi
        fi
    fi
    if [ "$mechanics_ran" -eq 0 ]; then
        echo "CHECK_RESULT mechanics=SKIP"
    fi
else
    scad="parts/$MODE.scad"
    if [ ! -f "$scad" ]; then
        echo "ERROR: $scad not found" >&2
        exit 1
    fi
    validate_file "$scad" "$BUILD_DIR/$MODE.stl" || OVERALL_FAIL=1
fi

if [ "$OVERALL_FAIL" -eq 0 ]; then
    echo "All validations passed."
else
    echo "FAIL: at least one check above failed -- see CHECK_RESULT lines for which." >&2
fi
exit "$OVERALL_FAIL"
