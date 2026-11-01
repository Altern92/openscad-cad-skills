# Pipeline benchmark 2026-11-01 (P7, deterministic part)

Command: `python3 bench/pipeline_bench.py` (dev scripts, mini, OpenSCAD + BOSL2 92d697c).
One clean 2-part project; each case seeds one defect (or a legitimate exception = control) and asks whether `validate_scad.sh --all` flags it under the expected check.

Result: **recall 29/29**, **false alarms 0/7 controls**, 158 s.

Fix on the way: control `ctl_no_joint_excused` first wrote `plan.md` = "x" (an invalid plan, so a real defect) and was flagged by `plan`; it now writes a valid plan. Not a validator bug.

Not covered: P6 organic checks (proportions/silhouette, covered by tests/fixtures/organic_checks), agent behaviour (golden-set agent QA v2 needs paid model runs, not run without permission).

```
ok   clean                        control                green
ok   thinner_plate                M4 / wrong size        dimensions=FAIL exit 1
ok   wider_plate                  wrong size             dimensions=FAIL exit 1
ok   longer_plate                 wrong size             dimensions=FAIL exit 1
ok   blind_hole_short_cutter      B blind bore           topology=FAIL exit 1
ok   hole_sealed_by_skin          B sealed bore          topology=FAIL exit 1
ok   extra_through_hole           unintended opening     topology=FAIL exit 1
ok   floating_boss                C disconnected         connectivity=FAIL exit 1
ok   cover_sunk_1mm               E collision            collisions=FAIL exit 1
ok   cover_shifted_into_plate     E collision            collisions=FAIL exit 1
ok   unjoined_third_part          D unattached           joints=FAIL exit 1
ok   no_bbox_declaration          F1 opt-in gap          declarations=FAIL exit 1
ok   no_holes_declaration         F1 opt-in gap          declarations=FAIL exit 1
ok   empty_no_bbox_reason         F1 escape abuse        declarations=FAIL exit 1
ok   hardcoded_thickness          hard-coded constant    sensitivity=FAIL exit 1
ok   rounded_1u                   rounded standard       scad_lint=FAIL exit 1
ok   computed_default_omitted     computed default       scad_lint=FAIL exit 1
ok   three_parts_no_plan          §0.5 skipped           plan=FAIL exit 1
ok   acceptance_weakened_part     P5 self-weakening      acceptance=FAIL exit 1
ok   acceptance_unapproved        P5 unapproved          acceptance=FAIL exit 1
ok   acceptance_spec_edited       P5 spec edited         acceptance=FAIL exit 1
ok   bore_refilled                B refilled cut         bore_reachability=FAIL exit 1
ok   assert_fails                 analytic preflight     analytic_bounds=FAIL exit 1
ok   syntax_error                 render                 render=FAIL exit 1
ok   hole_too_small               fit                    features=FAIL exit 1
ok   attachment_in_air            retention              attachment=FAIL exit 1
ok   motion_without_assembly      unverifiable           mechanics=INCONCLUSIVE exit 2
ok   wrong_library_version        P14 library drift      env=FAIL exit 5
ok   unknown_part_in_dispatch     assembly dispatch      collisions=INCONCLUSIVE exit 2
ok   critical_assumption_open     unverified input       assumptions=FAIL exit 1
ok   ctl_no_joint_excused         control                green
ok   ctl_blind_hole_declared      control                green
ok   ctl_acceptance_approved      control                green
ok   ctl_bores_open               control                green
ok   ctl_attachment_on_material   control                green
ok   ctl_no_bbox_with_reason      control                green

recall 29/29 defects caught by the named check; false alarms 0/7 controls; 158 s
```

## Rerun after P8 (2026-11-01, later)

6 real-failure cases (training records + SSD board_shelf) and 2 controls added; validator fixes from the agent eval in place.

```
ok   clean                        control                green
ok   thinner_plate                M4 / wrong size        dimensions=FAIL exit 1
ok   wider_plate                  wrong size             dimensions=FAIL exit 1
ok   longer_plate                 wrong size             dimensions=FAIL exit 1
ok   blind_hole_short_cutter      B blind bore           topology=FAIL exit 1
ok   hole_sealed_by_skin          B sealed bore          topology=FAIL exit 1
ok   extra_through_hole           unintended opening     topology=FAIL exit 1
ok   floating_boss                C disconnected         connectivity=FAIL exit 1
ok   cover_sunk_1mm               E collision            collisions=FAIL exit 1
ok   cover_shifted_into_plate     E collision            collisions=FAIL exit 1
ok   unjoined_third_part          D unattached           joints=FAIL exit 1
ok   no_bbox_declaration          F1 opt-in gap          declarations=FAIL exit 1
ok   no_holes_declaration         F1 opt-in gap          declarations=FAIL exit 1
ok   empty_no_bbox_reason         F1 escape abuse        declarations=FAIL exit 1
ok   hardcoded_thickness          hard-coded constant    sensitivity=FAIL exit 1
ok   rounded_1u                   rounded standard       scad_lint=FAIL exit 1
ok   computed_default_omitted     computed default       scad_lint=FAIL exit 1
ok   three_parts_no_plan          §0.5 skipped           plan=FAIL exit 1
ok   acceptance_weakened_part     P5 self-weakening      acceptance=FAIL exit 1
ok   acceptance_unapproved        P5 unapproved          acceptance=FAIL exit 1
ok   acceptance_spec_edited       P5 spec edited         acceptance=FAIL exit 1
ok   bore_refilled                B refilled cut         bore_reachability=FAIL exit 1
ok   assert_fails                 analytic preflight     analytic_bounds=FAIL exit 1
ok   syntax_error                 render                 render=FAIL exit 1
ok   hole_too_small               fit                    features=FAIL exit 1
ok   attachment_in_air            retention              attachment=FAIL exit 1
ok   motion_without_assembly      unverifiable           mechanics=INCONCLUSIVE exit 2
ok   wrong_library_version        P14 library drift      env=FAIL exit 5
ok   unknown_part_in_dispatch     assembly dispatch      collisions=INCONCLUSIVE exit 2
ok   critical_assumption_open     unverified input       assumptions=FAIL exit 1
ok   standoff_caps_hole           SSD board_shelf: standoffs after difference() topology=FAIL exit 1
ok   pocket_not_through           chain-20 / board_shelf: centered cut at z=-1 topology=FAIL exit 1
ok   louver_slots_merged          cnc_v2_fc_louver: pitch < slot length topology=FAIL exit 1
ok   peg_narrows_hole             fc-004: feature blocks part of a hole features=FAIL exit 1
ok   negative_height_cube         chain-19: cube with z_hi < z_lo render=FAIL exit 1
ok   missing_mirrored_part        chain-25: mirrored half never built acceptance=FAIL exit 1
ok   ctl_no_joint_excused         control                green
ok   ctl_blind_hole_declared      control                green
ok   ctl_acceptance_approved      control                green
ok   ctl_bores_open               control                green
ok   ctl_attachment_on_material   control                green
ok   ctl_hole_declared_true       control                green
ok   ctl_stale_stl_in_build       control (chain-03)     green
ok   ctl_no_bbox_with_reason      control                green

recall 35/35 defects caught by the named check; false alarms 0/9 controls; 197 s
```
