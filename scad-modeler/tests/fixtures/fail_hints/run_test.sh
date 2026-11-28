#!/usr/bin/env bash
# P39: every checker FAIL block carries "Hint: <what to change>" (text-to-cad: "a fit is named, never inferred").
# Runs the fixtures that produce FAILs with every check_*.py / motion_sweep.py wrapped by a shim
# (tests/tools/hint_audit.py) that logs each FAIL block lacking "Hint:". Fails on any hint-less block, and
# on fewer than 50 blocks seen (a shim that sees nothing must not pass). Not in the list on purpose:
# semantic_mutants / mutant_coverage (recursion), fixtures that grep the scripts' source (skill_docs_match_code,
# tessellation_minkowski_sphere, verdict_schema_closed) and fixtures that print no FAIL. Add a new fixture that
# prints FAIL to the list, or name it *_fail* (picked up by the glob). ~5 min; under the semantic-mutant runner
# (SCAD_MUTANT_INNER) only `fits` runs, enough to kill a mutant that strips a check_fits hint.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; F="$here/.."
T="$F/../tools/hint_audit.py"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
export HINT_AUDIT_LOG="$tmp/log"; : > "$HINT_AUDIT_LOG"
# the audit itself can fail: a hint-less block is logged, a hinted one and a non-FAIL line are not
python3 - "$T" "$tmp" <<'PY' || exit 1
import importlib.util, sys
s = importlib.util.spec_from_file_location("ha", sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
log = sys.argv[2] + "/selftest"
m.audit("x", "FAIL a\n  detail\nPASS b\n  FAIL c -- Hint: do it\n    more\nFAIL d\n\n  not part of d\nFAIL: e Hint: y", log)
t = open(log).read()
assert t.count("SEEN") == 4 and t.count("MISSING") == 2 and "FAIL a\n  detail" in t and "FAIL d" in t, t
PY
shim=$(python3 "$T" make "$SCAD_MODELER_SCRIPTS" "$tmp/shim") || exit 1
if [ -n "${SCAD_MUTANT_INNER:-}" ]; then list="fits"; min=1; else
    list="acceptance_lock assembly_sequence assumptions_critical_open_fail attachment_missing_fail behavior_gates behavior_multishell bore_candidates bore_reachability_sealed_fail collisions_candidate_touch collisions_coplanar_contact collisions_sunk_plate collisions_two_face_tenon connectivity_cavity_declared connectivity_disconnected_fail connectivity_shattered_fail contact_geometry declarations_unparsed dimensions_bbox_fail dimensions_declared_tol_fail empty_part_and_lone_file fasteners_aluminum_alias_fail fasteners_bottom_out_fail fasteners_empty_space fasteners_engage_short_alu_fail fasteners_head_cross_fail fasteners_insert_short_fail fasteners_mount fasteners_mount_covers_host_hole_fail fasteners_mount_two_plane_fail fasteners_mount_unfastened_fail fasteners_position_tol fasteners_purchased features_axis_offset_fail features_coarse_fn_fail fits fits_seat_depth collisions_tilted_contact honest_verdict intake_manifest_runs joint_graph kinematics_gates layout_instances limits_lock margin_provenance_fail margin_wrong_variable_fail metamorphic_checks motion_declared_pair_still_swept motion_entry_without_drivers motion_groups motion_groups_unassigned_fail motion_sign_fail organic_checks p27_behavior p27_fasteners p27_features_dims p27_limits p27_motion p27_strength p29_gear_axes p32_gear_kinds param_context_fail pipeline_catches_three_defects plan_no_decision_fail positioned_tripwire_single_part printability_bed_volume printability_bridge printability_overhang_fail printability_overhang_region printability_support_volume printability_wall_fail retention rules_cover_and_pervasive rules_gate_fails_unchecked_project rules_ignore_echoed_verdict rules_no_vacuous_pass scad_lint_computed_default_fail scad_lint_rounded_standard_fail sensitivity service_envelope_blank_fail strength_formulas strength_gates strength_single_piece subfeature_overlap_fail subfeature_overlap_wired topology_cases topology_sealed_hole_fail validate_lint_topology_wired validate_single_file "
    for d in "$F"/*_fail*/; do list="$list $(basename "$d")"; done
    list=$(tr ' ' '\n' <<< "$list" | grep -v '^$' | sort -u); min=51
fi
bad=0
for n in $list; do
    [ -f "$F/$n/run_test.sh" ] || { echo "fail_hints: no fixture $n" >&2; bad=1; continue; }
    (cd "$F/$n" && SCAD_MODELER_SCRIPTS="$shim" bash run_test.sh >"$tmp/out_$n" 2>&1) || { echo "fail_hints: fixture $n fails under the shims:" >&2; tail -5 "$tmp/out_$n" >&2; bad=1; }
done
seen=$(grep -c '^SEEN' "$HINT_AUDIT_LOG"); miss=$(grep -c '^MISSING' "$HINT_AUDIT_LOG")
echo "fail_hints: $seen FAIL block(s) seen, $miss without a Hint:"
[ "$seen" -ge "$min" ] || { echo "fail_hints: saw only $seen FAIL blocks (need >= $min): the shim sees nothing" >&2; bad=1; }
if [ "$miss" -gt 0 ]; then grep -v '^SEEN' "$HINT_AUDIT_LOG" | head -60 >&2; bad=1; fi
exit $bad
