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

# Best-effort validation-run logging (added 2026-08-21, see INCIDENTS.md):
# appends one JSON line per CHECK_RESULT to a machine-local log (see
# scripts/validation_log.py for why and where). Never blocks or fails the
# actual validation run -- stderr/exit are swallowed.
# Coverage counters. log_check() is the single place every check already
# reports through, so counting here covers all of them without touching 30
# call sites. "validate_scad_all" is the run's own verdict, not a check, and
# is excluded. A run that passed while half the surface was SKIP is a
# different claim from one that passed with everything exercised
# (INCIDENTS.md, 2026-09-12) -- and until now nothing told them apart.
CHK_PASS=0
CHK_FAIL=0
CHK_SKIP=0
log_check() {
    if [ "$1" != "validate_scad_all" ]; then
        case "$4" in
            SKIP:*) CHK_SKIP=$((CHK_SKIP + 1)) ;;
            *) if [ "$2" -eq 0 ]; then CHK_PASS=$((CHK_PASS + 1)); else CHK_FAIL=$((CHK_FAIL + 1)); fi ;;
        esac
    fi
    python3 "$SCRIPT_DIR/validation_log.py" --checker "$1" --exit "$2" \
        --command "$3" --summary "$4" --project "$PWD" >/dev/null 2>&1 || true
}

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

# Per-check coverage counters (added 2026-09-12, INCIDENTS.md). 4 checkers were
# never invoked by this script and 3 more ran silently, so "All validations
# passed." could be printed while most of the check surface had not executed --
# a project with exit 0 was not an auditable statement. Every check below now
# emits a CHECK_RESULT line even when it did not run, so the caller can count
# what actually happened instead of assuming it.
DIM_DECLARED=0
DIM_FAIL=0
FEAT_DECLARED=0
FEAT_FAIL=0
PREVIEW_COUNT=0
RENDER_FAIL=0
RENDER_FAILED_FILES=""
LIB_COUNT=0
LIB_SKIPPED=""

validate_file() {
    local scad="$1"
    local stl="$2"
    local this_failed=0
    echo "--- Validating $scad -> $stl ---"

    # A preview file renders several variants side by side so a human can
    # compare them; it is NOT one printable part. Its bbox is the bounding box
    # of the whole arrangement and its "bodies" are the loose variants -- so
    # connectivity, EXPECTED_BBOX and EXPECTED_HOLE are all meaningless on it,
    # and running them anyway produced a standing false FAIL on every run
    # (INCIDENTS.md, 2026-09-12: post.scad renders a 2U and a 1U post 12mm
    # apart, 47.979 x 17.979 x 96.389 against a declared 18 x 18 x 88.9, and
    # reported "2 disconnected bodies"). A check that cries wolf every run is
    # how a FAIL gets trained into background noise, so declare the file and
    # the geometry checks below step aside -- but the render above still runs,
    # and a preview that stops compiling is still an error.
    #
    # Same opt-in shape as the three markers already in use (EXPECTED_BBOX,
    # EXPECTED_HOLE, EXPECTED_BODIES): an explicit written statement in the
    # part file, never a silent guess.
    local is_preview=0
    if grep -q '^[[:space:]]*//[[:space:]]*PREVIEW_FILE' "$scad"; then
        is_preview=1
        PREVIEW_COUNT=$((PREVIEW_COUNT + 1))
        echo "SKIP: $scad declares PREVIEW_FILE -- geometry checks (connectivity/bbox/features) do not apply to a multi-variant preview."
    fi

    mkdir -p "$(dirname "$stl")"
    # A part that does not render was never checked. That used to leave NO
    # trace beyond an ERROR line and the generic summary, which meant
    # connectivity could still print PASS while a part had never been built
    # (INCIDENTS.md, 2026-09-12: front_swerve_module/parts/a_arm.scad renders
    # an empty top level -- "Current top level object is empty." -- and openscad
    # still exits 0, so only the missing STL reveals it). A false PASS is worse
    # than a false FAIL: it is a check that claims to have looked and did not.
    # openscad's own words for "the file defines things but instantiates
    # nothing". Captured rather than streamed so the two very different causes
    # below can be told apart; still echoed in full either way.
    render_out="$(mktemp)"
    "$OPENSCAD" --backend="$BACKEND" \
        --hardwarnings \
        --check-parameters=true \
        --check-parameter-ranges=true \
        -o "$stl" "$scad" >"$render_out" 2>&1
    render_rc=$?
    cat "$render_out"

    # A shared module library renders nothing by construction -- see the long
    # note on the empty-STL branch below. openscad reports it as "Current top
    # level object is empty." AND exits non-zero, so this has to be tested
    # before the generic render failure, not after it.
    if grep -qi "top level object is empty" "$render_out" \
        && grep -qE '^[[:space:]]*module[[:space:]]' "$scad"; then
        rm -f "$render_out"
        LIB_COUNT=$((LIB_COUNT + 1))
        echo "SKIP: $scad defines module(s) but instantiates none, so it renders no geometry -- a shared library file, not a printable part. If it was meant to be printable, its top-level call is missing."
        return 0
    fi
    rm -f "$render_out"

    if [ "$render_rc" -ne 0 ]; then
        echo "ERROR: render failed: $scad" >&2
        RENDER_FAIL=1
        RENDER_FAILED_FILES="$RENDER_FAILED_FILES $scad"
        return 1
    fi
    if [ ! -s "$stl" ]; then
        # No STL means the geometry checks below cannot run. Two very different
        # reasons produce that, and only one of them is a defect:
        #
        #   shared module library -- defines module(s), calls none, so it
        #     renders nothing by construction. 8 files across 5 projects are
        #     this: rack_v4/parts/{peg_joint,plate}.scad, v4/v8's
        #     plate_common.scad, front_swerve_module/parts/a_arm.scad -- each
        #     with 2-5 modules and 0 top-level calls. Reporting these as a
        #     failure would put a standing FAIL on 5 of 11 projects, and a FAIL
        #     that fires on a file that is CORRECT is how FAILs stop being read.
        #
        #   a part whose top-level call is missing or whose boolean cancels
        #     everything -- a real defect, and the reason this branch exists.
        #
        # Library files are SKIPPED with the reason spelled out rather than
        # silently passing: they are still named in the run, so a file that was
        # MEANT to be printable and lost its top-level call shows up as SKIP
        # instead of vanishing (INCIDENTS.md, 2026-09-12).
        echo "ERROR: STL is empty: $stl (the file rendered no geometry -- check for a missing top-level module call)" >&2
        RENDER_FAIL=1
        RENDER_FAILED_FILES="$RENDER_FAILED_FILES $scad"
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
    if [[ "$scad" == parts/* ]] && [ "$is_preview" -eq 0 ]; then
        if ! python3 "$SCRIPT_DIR/check_connectivity.py" --stl "$stl" --scad "$scad"; then
            PART_CONNECTIVITY_FAIL=1
            this_failed=1
        fi
    fi

    # Bounding-box check: only runs if the part declares an expected size via
    # `// EXPECTED_BBOX: [x, y, z]` -- catches a part that renders fine and
    # *looks* right but is subtly the wrong size (wrong -D override, a units
    # slip, a parameter that didn't thread through correctly).
    if [ "$is_preview" -eq 0 ] && grep -q '^[[:space:]]*//[[:space:]]*EXPECTED_BBOX' "$scad"; then
        DIM_DECLARED=$((DIM_DECLARED + 1))
        if ! python3 "$SCRIPT_DIR/check_dimensions.py" --stl "$stl" --scad "$scad"; then
            this_failed=1
            DIM_FAIL=1
        fi
    fi

    # Feature check: a bbox is nearly blind to inscribed-polygon undersizing,
    # which is what actually makes a bore too tight. Any part declaring
    # `// EXPECTED_HOLE: [x, y, z, "Z", d]` gets its bores measured
    # flat-to-flat instead.
    if [ "$is_preview" -eq 0 ] && grep -q '^[[:space:]]*//[[:space:]]*EXPECTED_HOLE' "$scad"; then
        FEAT_DECLARED=$((FEAT_DECLARED + 1))
        if ! python3 "$SCRIPT_DIR/check_features.py" --stl "$stl" --scad "$scad"; then
            this_failed=1
            FEAT_FAIL=1
        fi
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
        log_check "analytic_bounds" 0 "openscad --hardwarnings params.scad preflight" "PASS"
    else
        echo "CHECK_RESULT analytic_bounds=FAIL"
        echo "FAIL: an assert() in params.scad failed -- fix the source parameters" >&2
        echo "before any part is rendered, not after:" >&2
        grep -E "^ERROR: Assertion" "$preflight_log" >&2 || cat "$preflight_log" >&2
        OVERALL_FAIL=1
        log_check "analytic_bounds" 1 "openscad --hardwarnings params.scad preflight" \
            "FAIL: assert() failed in params.scad ($(grep -m1 -E "^ERROR: Assertion" "$preflight_log" || echo 'see stderr'))"
    fi
    rm -f "$tmp_wrapper" "$preflight_log" "$BUILD_DIR/.analytic_preflight.stl"
else
    echo "CHECK_RESULT analytic_bounds=SKIP"
    log_check "analytic_bounds" 0 "n/a" "SKIP: no params.scad"
fi

# Margin-provenance guard (added 2026-08-22, see INCIDENTS.md, Phase-2
# Pattern 1): catches a params.scad assert() whose "safe" verdict omits a
# clearance term the real geometry applies separately -- runs right after
# the analytic pre-flight gate, since it's the same near-zero-cost,
# no-rendering-needed class of check.
if [ -f params.scad ]; then
    if python3 "$SCRIPT_DIR/check_margin_provenance.py" --scad params.scad --parts-dir parts; then
        echo "CHECK_RESULT margin_provenance=PASS"
        log_check "margin_provenance" 0 "check_margin_provenance.py --scad params.scad" "PASS"
    else
        echo "CHECK_RESULT margin_provenance=FAIL"
        OVERALL_FAIL=1
        log_check "margin_provenance" 1 "check_margin_provenance.py --scad params.scad" "FAIL"
    fi
else
    echo "CHECK_RESULT margin_provenance=SKIP"
    log_check "margin_provenance" 0 "n/a" "SKIP: no params.scad"
fi

# Parameter-context manifest guard (added 2026-08-22, see INCIDENTS.md,
# Phase-2 Pattern 3): opt-in via use_param() declarations anywhere in the
# project; a no-op if none are present, so a project that hasn't adopted
# this convention isn't affected.
if python3 "$SCRIPT_DIR/check_param_context.py" --project-dir .; then
    echo "CHECK_RESULT param_context=PASS"
    log_check "param_context" 0 "check_param_context.py --project-dir ." "PASS"
else
    echo "CHECK_RESULT param_context=FAIL"
    OVERALL_FAIL=1
    log_check "param_context" 1 "check_param_context.py --project-dir ." "FAIL"
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
        log_check "assumptions" 0 "check_assumptions.py --calc calculations.md" "PASS"
    else
        echo "CHECK_RESULT assumptions=FAIL"
        OVERALL_FAIL=1
        log_check "assumptions" 1 "check_assumptions.py --calc calculations.md" "FAIL"
    fi
else
    echo "CHECK_RESULT assumptions=SKIP"
    log_check "assumptions" 0 "n/a" "SKIP: no calculations.md"
fi

if python3 "$SCRIPT_DIR/check_service_envelope.py" --envelope service_envelope.md; then
    echo "CHECK_RESULT service_envelope=PASS"
    log_check "service_envelope" 0 "check_service_envelope.py --envelope service_envelope.md" "PASS"
else
    echo "CHECK_RESULT service_envelope=FAIL"
    OVERALL_FAIL=1
    log_check "service_envelope" 1 "check_service_envelope.py --envelope service_envelope.md" "FAIL"
fi

# Enforces §0.5 Planning actually happened (>=2 architecture options or a
# declared exemption, a confirmed decision, every layout.scad part present
# in the plan) rather than existing only as prose a model could skip under
# pressure -- the same gap that let the rear_axle incident happen in the
# first place (INCIDENTS.md, 2026-08-18). Opt-in by plan.md's existence.
if python3 "$SCRIPT_DIR/check_plan.py" --plan plan.md \
    $([ -f layout.scad ] && echo --layout layout.scad); then
    echo "CHECK_RESULT plan=PASS"
    log_check "plan" 0 "check_plan.py --plan plan.md" "PASS"
else
    echo "CHECK_RESULT plan=FAIL"
    OVERALL_FAIL=1
    log_check "plan" 1 "check_plan.py --plan plan.md" "FAIL"
fi

if [[ "$MODE" == "--all" ]]; then
    shopt -s nullglob
    parts=(parts/*.scad)
    shopt -u nullglob
    if [ ${#parts[@]} -eq 0 ]; then
        # A run that rendered nothing is not a pass. Following the skill's own
        # templates used to land here: templates/README.md said to copy files to
        # scad/, the gate globs parts/ relative to the CURRENT directory, and the
        # result was 'WARNING: no files found under parts/*.scad' followed by
        # 'All validations passed.' with nothing rendered, measured or checked
        # (INCIDENTS.md 2026-09-12, found by an adversarial review). Measured on
        # that exact layout today: exit 0, 17 checks reported, 0 parts.
        echo "ERROR: no parts/*.scad found under $(pwd) -- NOTHING was rendered or checked. Either run this from the project root (the directory that contains parts/ and assembly.scad), or the project has no parts yet. Reporting this as a failure, because a green run that examined nothing is the one verdict worse than a red one." >&2
        if [ ! -d parts ] && [ -d scad/parts ]; then
            echo "  -> found scad/parts/ instead. validate_scad.sh operates on the project ROOT: cd scad && bash .../validate_scad.sh --all" >&2
        fi
        OVERALL_FAIL=1
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

    # Render is the precondition of every geometry check below: a part that
    # produced no STL was never examined by any of them, so it gets its own
    # check and it vetoes connectivity=PASS below (INCIDENTS.md, 2026-09-12).
    if [ "$RENDER_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT render=PASS"
        if [ "$LIB_COUNT" -gt 0 ]; then
            echo "INFO: $LIB_COUNT file(s) are shared module libraries (define modules, instantiate none) -- skipped, not printable parts."
            log_check "render" 0 "validate_scad.sh --all" "PASS: every printable parts/*.scad produced a non-empty STL; $LIB_COUNT library file(s) skipped"
        else
            log_check "render" 0 "validate_scad.sh --all" "PASS: every parts/*.scad produced a non-empty STL"
        fi
    else
        echo "CHECK_RESULT render=FAIL"
        OVERALL_FAIL=1
        echo "  - no STL produced for:" >&2
        for f in $RENDER_FAILED_FILES; do echo "      $f" >&2; done
        log_check "render" 1 "validate_scad.sh --all" "FAIL: no STL for$RENDER_FAILED_FILES"
    fi

    if [ ${#parts[@]} -eq 0 ]; then
        echo "CHECK_RESULT connectivity=SKIP"
        log_check "connectivity" 0 "validate_scad.sh --all" "SKIP: no parts/*.scad"
    elif [ "$RENDER_FAIL" -ne 0 ]; then
        echo "CHECK_RESULT connectivity=FAIL"
        log_check "connectivity" 1 "validate_scad.sh --all" "FAIL:$RENDER_FAILED_FILES never rendered, so connectivity was never measured"
    elif [ "$PART_CONNECTIVITY_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT connectivity=PASS"
        log_check "connectivity" 0 "validate_scad.sh --all" "PASS (${#parts[@]} part(s), $PREVIEW_COUNT preview file(s) excluded)"
    else
        echo "CHECK_RESULT connectivity=FAIL"
        log_check "connectivity" 1 "validate_scad.sh --all" "FAIL: see part-level check_connectivity.py output above"
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
                log_check "bore_reachability" 0 "check_bore_reachability.py --bores bores.json (via validate_scad.sh)" "PASS"
            else
                echo "CHECK_RESULT bore_reachability=FAIL"
                OVERALL_FAIL=1
                log_check "bore_reachability" 1 "check_bore_reachability.py --bores bores.json (via validate_scad.sh)" "FAIL"
            fi
        else
            echo "CHECK_RESULT bore_reachability=SKIP"
            log_check "bore_reachability" 0 "n/a" "SKIP: bores.json present but no built STLs"
        fi
    else
        # Absent declaration used to mean NO line at all -- indistinguishable
        # from "this check does not exist" (INCIDENTS.md, 2026-09-12).
        echo "CHECK_RESULT bore_reachability=SKIP"
        log_check "bore_reachability" 0 "n/a" "SKIP: no bores.json -- copy templates/bores.json to the project root and fill it in; until then no bore is checked for reachability"
    fi

    # Attachment-point check: opt-in via a project-root attachments.json
    # declaring where each part is fastened to another part. Every other
    # check here asks whether a part is correct; none asks whether it has
    # anything on it to attach WITH. A bare platform with no bosses, flanges
    # or holes passes connectivity (one solid) and dimensions (right size)
    # while being impossible to fasten to anything -- confirmed live
    # (INCIDENTS.md 2026-09-11, side panels). Runs against the rendered part
    # STLs, after the parts loop above so they already exist.
    if [ -f attachments.json ]; then
        shopt -s nullglob
        attach_stls=("$BUILD_DIR"/*.stl)
        shopt -u nullglob
        if [ ${#attach_stls[@]} -gt 0 ]; then
            if python3 "$SCRIPT_DIR/check_attachment.py" --attachments attachments.json ${attach_stls[@]+"${attach_stls[@]}"}; then
                echo "CHECK_RESULT attachment=PASS"
                log_check "attachment" 0 "check_attachment.py --attachments attachments.json (via validate_scad.sh)" "PASS"
            else
                echo "CHECK_RESULT attachment=FAIL"
                OVERALL_FAIL=1
                log_check "attachment" 1 "check_attachment.py --attachments attachments.json (via validate_scad.sh)" "FAIL"
            fi
        else
            echo "CHECK_RESULT attachment=SKIP"
            log_check "attachment" 0 "n/a" "SKIP: attachments.json present but no built STLs"
        fi
    else
        echo "CHECK_RESULT attachment=SKIP"
        log_check "attachment" 0 "n/a" "SKIP: no attachments.json -- copy templates/attachments.json to the project root and fill it in; until then no part is checked for having anything to fasten WITH"
    fi

    # Sub-feature overlap: opt-in via a `// SUBFEATURES: a, b, c` line in a part
    # file (2+ names). Each named sub-feature is rendered SOLO through the part
    # file's own guarded SUBFEATURE switch (see templates/part_template.scad)
    # and compared before union(). Once union()ed the overlap is invisible:
    # union() of two overlapping solids is still one valid watertight single-
    # body shell, so connectivity and dimensions both stay clean -- real
    # incident, a bearing tower overlapped a motor cradle by 419mm3 inside one
    # part (INCIDENTS.md, 2026-08-19).
    #
    # Run PER PART, never across parts: each part's sub-features live in that
    # part's LOCAL coordinates, so comparing sub-features of two different
    # parts would compare two unrelated origins and report meaningless overlap
    # (measured: 196779 mm3 between base.stl and frame_module.stl that way).
    SUBFEAT_PARTS=0
    SUBFEAT_STLS=0
    SUBFEAT_FAIL=0
    for scad in ${parts[@]+"${parts[@]}"}; do
        sf_line=$(grep -m1 '^[[:space:]]*//[[:space:]]*SUBFEATURES:' "$scad" || true)
        [ -n "$sf_line" ] || continue
        sf_names=$(printf '%s' "$sf_line" | sed 's/^[^:]*://' | tr ',' ' ')
        sf_n=0
        for x in $sf_names; do sf_n=$((sf_n + 1)); done
        [ "$sf_n" -ge 2 ] || continue
        SUBFEAT_PARTS=$((SUBFEAT_PARTS + 1))
        sf_base=$(basename "$scad" .scad)
        mkdir -p "$BUILD_DIR/subfeatures"
        sf_stls=()
        for x in $sf_names; do
            sf_out="$BUILD_DIR/subfeatures/${sf_base}__${x}.stl"
            if $OPENSCAD --backend="$BACKEND" --hardwarnings \
                -D "SUBFEATURE=\"$x\"" -o "$sf_out" "$scad" >/dev/null 2>&1 \
                && [ -s "$sf_out" ]; then
                sf_stls+=("$sf_out")
            else
                echo "WARNING: $sf_base declares // SUBFEATURES but sub-feature '$x' did not render solo -- check the SUBFEATURE dispatch in the part file." >&2
            fi
        done
        if [ ${#sf_stls[@]} -ge 2 ]; then
            SUBFEAT_STLS=$((SUBFEAT_STLS + ${#sf_stls[@]}))
            # fusions.json declares sub-features that are MEANT to overlap (a
            # boss blending into its tower). The checker takes --exempt for
            # exactly that, but validate_scad.sh never passed it, so a project
            # that declared an intentional fusion still got a hard FAIL -- the
            # declaration was a no-op in the only automated path (found by an
            # adversarial review, INCIDENTS.md 2026-09-12).
            sf_exempt=""
            [ -f fusions.json ] && sf_exempt="--exempt fusions.json"
            if ! python3 "$SCRIPT_DIR/check_subfeature_overlap.py" $sf_exempt ${sf_stls[@]+"${sf_stls[@]}"}; then
                SUBFEAT_FAIL=1
            fi
        fi
    done
    # The reason goes on STDOUT as well as to the log: a bare SKIP line tells a
    # reader that something did not run but not how to make it run, which is
    # how this check sat unused across every project (INCIDENTS.md,
    # 2026-09-12).
    if [ "$SUBFEAT_PARTS" -eq 0 ]; then
        echo "CHECK_RESULT subfeature_overlap=SKIP"
        echo "  -> no part declares '// SUBFEATURES: a, b, c' (2+ names), so no sub-feature was compared. Add the line and give each name its own module; see templates/part_template.scad. Until then an overlap inside one part's own union() is invisible to every other check."
        log_check "subfeature_overlap" 0 "n/a" "SKIP: no part declares // SUBFEATURES with 2+ names -- see templates/part_template.scad"
    elif [ "$SUBFEAT_STLS" -lt 2 ]; then
        echo "CHECK_RESULT subfeature_overlap=SKIP"
        echo "  -> SUBFEATURES declared but fewer than 2 sub-features rendered solo -- check the guarded SUBFEATURE dispatch in the part file (templates/part_template.scad)."
        log_check "subfeature_overlap" 0 "n/a" "SKIP: SUBFEATURES declared but fewer than 2 sub-features rendered solo"
    elif [ "$SUBFEAT_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT subfeature_overlap=PASS"
        log_check "subfeature_overlap" 0 "check_subfeature_overlap.py (via validate_scad.sh)" "PASS ($SUBFEAT_PARTS part(s), $SUBFEAT_STLS sub-feature STL(s))"
    else
        echo "CHECK_RESULT subfeature_overlap=FAIL"
        OVERALL_FAIL=1
        log_check "subfeature_overlap" 1 "check_subfeature_overlap.py (via validate_scad.sh)" "FAIL"
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
    # The positioned render is gated on assembly.scad, NOT on joints.json.
    # Joints.json is a declaration of what is MEANT to touch; collisions do not
    # need it to FIND an overlap -- check_collisions.py takes --expected-contacts
    # as optional and, without it, reports unintended interference plus a
    # paste-ready stub. Gating the whole block on joints.json was a
    # chicken-and-egg: the check that would have produced the first declaration
    # never ran because the declaration did not exist (INCIDENTS.md, 2026-09-12).
    if [ -f assembly.scad ]; then
        has_motion=$(python3 -c "
import json, sys
import os
if not os.path.isfile('joints.json'):
    sys.exit(1)
try:
    d = json.load(open('joints.json'))
except Exception:
    sys.exit(1)
motion = d.get('motion') if isinstance(d, dict) else None
sys.exit(0 if motion else 1)
" && echo yes || echo no)
        if [ "$has_motion" = "yes" ]; then
            mechanics_ran=1
        fi
        {
            echo "--- Rendering positioned parts (assembly coordinates) for the collisions check ---"
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

            # A positioned part is supposed to be ONE part sitting in assembly
            # coordinates (SKILL.md 6: -D 'MODE="part"' -D 'PART="name"').
            # That only works if assembly.scad guards its own default, with
            #   MODE = is_undef(MODE) ? "assembly" : MODE;
            # A plain `MODE = 1;` REASSIGNS the variable and defeats -D
            # entirely, so every "part" render silently produces the WHOLE
            # ASSEMBLY. Measured on server_rack_modular_v4 (2026-09-12): 17
            # positioned STLs of ~12.5MB each, every pair then reporting
            # "penetration depth 170.000 mm" -- 136 meaningless collisions out
            # of 17 identical copies. Collisions on garbage are worse than no
            # collisions, because they look like a result.
            #
            # Tripwire: an STL's byte size is 84 + 50*triangles, so a positioned
            # part at >= 80% of the full assembly's size is not a part. This has
            # to run BEFORE any checker consumes them.
            # Compare BOUNDING BOXES, not file sizes. Size was the first
            # attempt and it produced a false positive on the very first
            # complete test project (2026-09-12): a base plate with four screw
            # holes plus a centre bore carries more triangles than the small
            # assembly it belongs to, so an 80%-of-assembly-size rule called
            # it "the whole assembly". A part equals the assembly's bbox only
            # if it IS the assembly.
            positioned_bogus=0
            if [ -s "$BUILD_DIR/assembly.stl" ]; then
                positioned_bogus=$(python3 -c '
import struct, sys
def extent(p):
    f = open(p, "rb")
    f.read(80)
    n = struct.unpack("<I", f.read(4))[0]
    lo = [1e30] * 3; hi = [-1e30] * 3
    for _ in range(n):
        b = f.read(50)
        for k in range(3):
            v = struct.unpack_from("<3f", b, 12 + 12 * k)
            for a in range(3):
                lo[a] = min(lo[a], v[a]); hi[a] = max(hi[a], v[a])
    f.close()
    return [hi[a] - lo[a] for a in range(3)]
asm = extent(sys.argv[1])
bogus = 0
for p in sys.argv[2:]:
    e = extent(p)
    if all(abs(e[a] - asm[a]) < 0.01 for a in range(3)):
        bogus += 1
print(bogus)
' "$BUILD_DIR/assembly.stl" ${positioned_stls[@]+"${positioned_stls[@]}"} 2>/dev/null || echo 0)
            fi
            if [ "$positioned_bogus" -gt 0 ]; then
                echo "ERROR: $positioned_bogus of ${#positioned_stls[@]} positioned part(s) have exactly the assembly's bounding box -- assembly.scad's MODE/PART switch did not take effect, so every 'part' is a copy of the full assembly. Fix assembly.scad to guard its default (SKILL.md §6): MODE = is_undef(MODE) ? \"assembly\" : MODE; -- a plain MODE = 1; reassigns the variable and defeats -D. Collision checks are skipped: running them on N copies of the assembly produces N*(N-1)/2 meaningless overlaps." >&2
                echo "CHECK_RESULT collisions=SKIP"
                log_check "collisions" 0 "n/a" "SKIP: assembly.scad MODE/PART switch not working ($positioned_bogus part(s) sized as the whole assembly)"
                echo "CHECK_RESULT mechanics=FAIL"
                OVERALL_FAIL=1
                log_check "mechanics" 1 "validate_scad.sh --all" "FAIL: positioned render produced the whole assembly, not parts"
                mechanics_ran=1
            fi

            if [ ${#positioned_stls[@]} -ge 2 ] && [ "$positioned_bogus" -eq 0 ]; then
                # Static collisions ALWAYS run on positioned parts. The
                # declaration is optional: without it check_collisions.py still
                # finds unintended interference and prints a stub to paste.
                contacts_arg=""
                [ -f joints.json ] && contacts_arg="--expected-contacts joints.json"
                if python3 "$SCRIPT_DIR/check_collisions.py" $contacts_arg \
                    ${positioned_stls[@]+"${positioned_stls[@]}"} ; then
                    echo "CHECK_RESULT collisions=PASS"
                    log_check "collisions" 0 "check_collisions.py (via validate_scad.sh)" "PASS"
                else
                    echo "CHECK_RESULT collisions=FAIL"
                    OVERALL_FAIL=1
                    log_check "collisions" 1 "check_collisions.py (via validate_scad.sh)" "FAIL"
                fi
                if [ "$has_motion" = "yes" ]; then
                    if python3 "$SCRIPT_DIR/motion_sweep.py" --joints joints.json \
                        ${positioned_stls[@]+"${positioned_stls[@]}"} ; then
                        echo "CHECK_RESULT mechanics=PASS"
                        log_check "mechanics" 0 "motion_sweep.py (via validate_scad.sh)" "PASS"
                    else
                        echo "CHECK_RESULT mechanics=FAIL"
                        OVERALL_FAIL=1
                        log_check "mechanics" 1 "motion_sweep.py (via validate_scad.sh)" "FAIL"
                    fi
                fi
            elif [ "$positioned_bogus" -eq 0 ]; then
                echo "WARNING: fewer than 2 parts rendered via MODE=\"part\" -- collisions cannot run. Check that assembly.scad's MODE/PART switch matches SKILL.md §6 and that parts/*.scad basenames match layout.scad's part names." >&2
                echo "CHECK_RESULT collisions=SKIP"
                log_check "collisions" 0 "n/a" "SKIP: fewer than 2 positioned parts rendered"
                if [ "$has_motion" = "yes" ]; then
                    echo "CHECK_RESULT mechanics=FAIL"
                    OVERALL_FAIL=1
                    log_check "mechanics" 1 "validate_scad.sh --all" "FAIL: fewer than 2 positioned parts rendered"
                fi
            fi
        }
    fi
    if [ "$mechanics_ran" -eq 0 ]; then
        # collisions is NOT skipped here any more: it runs on positioned parts
        # whenever assembly.scad exists, declaration or not. Only the dynamic
        # sweep needs a motion block.
        echo "CHECK_RESULT mechanics=SKIP"
        # Two different causes, and they were reported with one sentence.
        if [ -f joints.json ] && [ ! -f assembly.scad ]; then
            echo "  -> joints.json declares motion but there is no assembly.scad, so positioned parts cannot be rendered and the sweep was NOT run. R-09 in rules_manifest.yaml treats this as a failure for exactly that reason."
            log_check "mechanics" 0 "n/a" "SKIP: joints.json declares motion but assembly.scad is missing -- positioned parts cannot be rendered"
        else
            log_check "mechanics" 0 "n/a" "SKIP: no joints.json motion declared"
        fi
    fi

    # dimensions/features are opt-in PER PART (// EXPECTED_BBOX / EXPECTED_HOLE),
    # and previously said nothing when no part declared them. Same silent-gap
    # class as above.
    if [ "$PREVIEW_COUNT" -gt 0 ]; then
        echo "INFO: $PREVIEW_COUNT file(s) declared PREVIEW_FILE -- connectivity/bbox/features skipped for those, by declaration."
    fi

    if [ "$DIM_DECLARED" -eq 0 ]; then
        echo "CHECK_RESULT dimensions=SKIP"
        log_check "dimensions" 0 "n/a" "SKIP: no part declares // EXPECTED_BBOX"
    elif [ "$DIM_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT dimensions=PASS"
        log_check "dimensions" 0 "validate_scad.sh --all" "PASS ($DIM_DECLARED part(s) declared)"
    else
        echo "CHECK_RESULT dimensions=FAIL"
        log_check "dimensions" 1 "validate_scad.sh --all" "FAIL: see check_dimensions.py output above"
    fi

    if [ "$FEAT_DECLARED" -eq 0 ]; then
        echo "CHECK_RESULT features=SKIP"
        log_check "features" 0 "n/a" "SKIP: no part declares // EXPECTED_HOLE"
    elif [ "$FEAT_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT features=PASS"
        log_check "features" 0 "validate_scad.sh --all" "PASS ($FEAT_DECLARED part(s) declared)"
    else
        echo "CHECK_RESULT features=FAIL"
        log_check "features" 1 "validate_scad.sh --all" "FAIL: see check_features.py output above"
    fi

    # --- Checkers that exist in scripts/ but are NOT gates here -------------
    # Named explicitly so the absence of a check is a written statement rather
    # than an omission nobody can see (INCIDENTS.md, 2026-09-12). Each one is
    # deliberately NOT wired as a pass/fail gate, with the reason recorded:
    #
    # printability   -- runs on any STL, but on 2026-09-12 it FAILED 4/4 real
    #                   parts of server_rack_modular (overhang area > 0 on any
    #                   FDM part with a fillet or a hole; minimum wall read
    #                   0.014mm, a degenerate-sliver measurement, not a wall).
    #                   As a gate it would fail every project, which is noise,
    #                   not signal. Needs threshold work first.
    # subfeature_overlap -- IS wired (see the // SUBFEATURES block above); it
    #                   reports SKIP from there when no part declares names,
    #                   which is the honest verdict rather than a second line.
    # intake         -- opt-in Stage 0 manifest; no manifest = nothing to check.
    # dependencies   -- change-propagation engine, run on demand with --change;
    #                   it answers "what must be recomputed", it is not a gate.
    echo "CHECK_RESULT printability=SKIP"
    log_check "printability" 0 "n/a" "SKIP: not a gate -- fails 4/4 real parts, needs threshold work first (run scripts/check_printability.py --stl <stl> manually)"

    echo "CHECK_RESULT intake=SKIP"
    # The reason must be true. It said "no design_manifest.json" unconditionally,
    # including in a project that HAD one -- a SKIP whose stated cause is false
    # is worse than a bare SKIP, because it sends the reader to fix something
    # that is not broken (adversarial review, INCIDENTS.md 2026-09-12).
    if [ -f design_manifest.json ] || [ -f requirements.json ]; then
        log_check "intake" 0 "n/a" "SKIP: a manifest exists but validate_scad.sh does not run check_intake.py -- run it directly, or 'bash {skill_dir}/scripts/check_rules.py --project-dir .' for rule R-01"
    else
        log_check "intake" 0 "n/a" "SKIP: no design_manifest.json -- the Stage-0 requirement spec was never produced; see references/intake_and_analysis.md"
    fi
    echo "CHECK_RESULT dependencies=SKIP"
    log_check "dependencies" 0 "n/a" "SKIP: on-demand analysis (--change), not a gate"
else
    scad="parts/$MODE.scad"
    if [ ! -f "$scad" ]; then
        echo "ERROR: $scad not found" >&2
        exit 1
    fi
    validate_file "$scad" "$BUILD_DIR/$MODE.stl" || OVERALL_FAIL=1
    # Single-part mode must report like every other run. SKILL.md tells the
    # reader to trust the CHECK_RESULT lines and the COVERAGE line, and this
    # mode used to print NEITHER for the per-part checks -- it emitted only the
    # project-level gates above, so a part whose connectivity or bbox was wrong
    # still ended in "All validations passed." with no verdict line naming it
    # (adversarial review, INCIDENTS.md 2026-09-12).
    if [ "$PART_CONNECTIVITY_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT connectivity=PASS"
        log_check "connectivity" 0 "validate_scad.sh $MODE" "PASS (single part)"
    else
        echo "CHECK_RESULT connectivity=FAIL"
        log_check "connectivity" 1 "validate_scad.sh $MODE" "FAIL (single part)"
    fi
    if [ "$DIM_DECLARED" -eq 0 ]; then
        echo "CHECK_RESULT dimensions=SKIP"
        log_check "dimensions" 0 "n/a" "SKIP: no // EXPECTED_BBOX in parts/$MODE.scad"
    elif [ "$DIM_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT dimensions=PASS"
        log_check "dimensions" 0 "validate_scad.sh $MODE" "PASS"
    else
        echo "CHECK_RESULT dimensions=FAIL"
        log_check "dimensions" 1 "validate_scad.sh $MODE" "FAIL"
    fi
    if [ "$FEAT_DECLARED" -eq 0 ]; then
        echo "CHECK_RESULT features=SKIP"
        log_check "features" 0 "n/a" "SKIP: no // EXPECTED_HOLE in parts/$MODE.scad"
    elif [ "$FEAT_FAIL" -eq 0 ]; then
        echo "CHECK_RESULT features=PASS"
        log_check "features" 0 "validate_scad.sh $MODE" "PASS"
    else
        echo "CHECK_RESULT features=FAIL"
        log_check "features" 1 "validate_scad.sh $MODE" "FAIL"
    fi
    echo "INFO: single-part mode ($MODE) runs the per-part geometry checks and the project-level
  gates above. It does NOT render the assembly, so collisions / mechanics / sub-feature
  overlap are not evaluated -- run validate_scad.sh --all from the project root for those."
fi

if [[ "$MODE" == "--all" ]]; then
    echo "COVERAGE: $CHK_PASS passed, $CHK_FAIL failed, $CHK_SKIP skipped ($((CHK_PASS + CHK_FAIL + CHK_SKIP)) checks reported)."
    if [ "$CHK_SKIP" -gt 0 ]; then
        echo "  $CHK_SKIP check(s) did NOT run -- each SKIP above names what it needs. A green run with a large SKIP count has verified less than it looks."
    fi
fi

if [[ "$MODE" != "--all" ]]; then
    echo "COVERAGE: $CHK_PASS passed, $CHK_FAIL failed, $CHK_SKIP skipped ($((CHK_PASS + CHK_FAIL + CHK_SKIP)) checks reported, single-part mode)."
fi

if [ "$OVERALL_FAIL" -eq 0 ]; then
    echo "All validations passed."
    log_check "validate_scad_all" 0 "validate_scad.sh $MODE" "all checks passed"
else
    echo "FAIL: at least one check above failed -- see CHECK_RESULT lines for which." >&2
    log_check "validate_scad_all" 1 "validate_scad.sh $MODE" "at least one CHECK_RESULT above is FAIL"
fi
exit "$OVERALL_FAIL"
