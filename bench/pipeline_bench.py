#!/usr/bin/env python3
"""Pipeline benchmark: does validate_scad.sh catch seeded defects, and only those? (P7, 2026-11-01)

The old golden set asked an agent 10 retrieval questions and scored 100 % before and after
every change, so it measured nothing (NEXT.md §1). This one needs no LLM and no money:
a clean 2-part project (plate + holed lid resting on it) and one mutation per case, each
from an incident class. A defect counts as CAUGHT only when the run is not green AND the
named check reports FAIL (or the run is NOT VERIFIED, exit 2, where that is the point).
Controls must stay green -- they measure false alarms (e.g. the P16 coplanar lid).

Usage:
    python3 bench/pipeline_bench.py [--scripts DIR] [--only NAME] [--keep DIR]
Prints one row per case, then recall over defects and false alarms over controls.
Exit 0 when every defect is caught and every control passes, else 1.
"""
import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SCRIPTS = os.path.join(HERE, "..", "scad-modeler", "scripts")

PARAMS = """$fn = 32;
plate_l = 40; plate_w = 20; plate_t = 5; hole_d = 4; cover_t = 2;
"""
BASE = """include <../params.scad>
// EXPECTED_BBOX: [40, 20, 5]
// EXPECTED_THROUGH_HOLES: 2
// SENSITIVE_TO: plate_t
module base() {
    difference() {
        cube([plate_l, plate_w, plate_t]);
        for (x = [10, 30]) translate([x, 10, -1]) cylinder(d = hole_d, h = plate_t + 2);
    }
}
base();
"""
COVER = """include <../params.scad>
// EXPECTED_BBOX: [40, 20, 2]
// EXPECTED_THROUGH_HOLES: 2
module cover() {
    difference() {
        cube([plate_l, plate_w, cover_t]);
        for (x = [10, 30]) translate([x, 10, -1]) cylinder(d = hole_d, h = cover_t + 2);
    }
}
cover();
"""
ASSEMBLY = """include <params.scad>
use <parts/base.scad>
use <parts/cover.scad>
MODE = is_undef(MODE) ? "assembly" : MODE;
PART = is_undef(PART) ? "" : PART;
COVER_Z = plate_t;
module place(n) {
    if (n == "base") base();
    else if (n == "cover") translate([0, 0, COVER_Z]) cover();
    else assert(false, str("unknown part ", n));
}
if (MODE == "assembly") { place("base"); place("cover"); }
else if (MODE == "part") place(PART);
"""
JOINTS = {"contacts": [{"pair": ["base", "cover"], "joint_type": "resting",
                        "expected_interference_mm": [0.0, 0.05], "multi_region_ok": True,
                        "derivation": "cover rests on the plate's top face, face contact only"}]}
CLEAN = {"params.scad": PARAMS, "parts/base.scad": BASE, "parts/cover.scad": COVER,
         "assembly.scad": ASSEMBLY, "joints.json": json.dumps(JOINTS)}


def sub(path, old, new):
    def f(p):
        assert old in p[path], (path, old)
        p[path] = p[path].replace(old, new, 1)
    return f


def put(path, text):
    def f(p):
        p[path] = text
    return f


def drop(path):
    def f(p):
        p.pop(path, None)
    return f


def seq(*fs):
    def f(p):
        for g in fs:
            g(p)
    return f


PLAN3 = """# Plan
## Architecture options
| Option | Description |
|---|---|
| Datum | plate with a resting cover |
| Alt A | one-piece box |
## Decision
| ID | Type | Criticality | Statement | Status | Evidence |
|---|---|---|---|---|---|
| D1 | Decision | Ordinary | Datum: cover lifts off | Confirmed | bench |
## Parts and dependency order
| Part | Depends on | Notes |
|---|---|---|
| base | - | |
| cover | base | |
| clip | - | spare |
"""
THIRD = "include <../params.scad>\n// EXPECTED_BBOX: [10, 10, 2]\n// EXPECTED_THROUGH_HOLES: 0\ncube([10, 10, 2]);\n"
ACC = json.dumps({"parts": {"base": {"bbox": [40, 20, 5], "through_holes": 2}}})

# (name, incident class, mutation, expected check that must FAIL, or None for a control)
CASES = [
    ("clean", "control", None, None),
    ("thinner_plate", "M4 / wrong size", sub("params.scad", "plate_t = 5", "plate_t = 3"), "dimensions"),
    ("wider_plate", "wrong size", sub("params.scad", "plate_w = 20", "plate_w = 24"), "dimensions"),
    ("longer_plate", "wrong size", sub("params.scad", "plate_l = 40", "plate_l = 41"), "dimensions"),
    ("blind_hole_short_cutter", "B blind bore", sub("parts/base.scad", "h = plate_t + 2", "h = plate_t - 1"), "topology"),
    ("hole_sealed_by_skin", "B sealed bore", sub("parts/base.scad", "base();\n",
        "base();\ntranslate([7, 7, 4.6]) cube([6, 6, 0.4]);\n"), "topology"),
    ("extra_through_hole", "unintended opening", sub("parts/base.scad", "x = [10, 30]", "x = [10, 20, 30]"), "topology"),
    ("floating_boss", "C disconnected", sub("parts/base.scad", "base();\n",
        "base();\ntranslate([50, 0, 0]) cube(3);\n"), "connectivity"),
    ("cover_sunk_1mm", "E collision", sub("assembly.scad", "COVER_Z = plate_t;", "COVER_Z = plate_t - 1;"), "collisions"),
    ("cover_shifted_into_plate", "E collision", sub("assembly.scad", "translate([0, 0, COVER_Z])",
        "translate([5, 0, COVER_Z - 1.5])"), "collisions"),
    ("unjoined_third_part", "D unattached", seq(put("parts/clip.scad", THIRD),
        sub("assembly.scad", 'else assert', 'else if (n == "clip") translate([60, 0, 0]) cube([10, 10, 2]);\n    else assert'),
        put("plan.md", "x")), "joints"),
    ("no_bbox_declaration", "F1 opt-in gap", sub("parts/cover.scad", "// EXPECTED_BBOX: [40, 20, 2]\n", ""), "declarations"),
    ("no_holes_declaration", "F1 opt-in gap", sub("parts/cover.scad", "// EXPECTED_THROUGH_HOLES: 2\n", ""), "declarations"),
    ("empty_no_bbox_reason", "F1 escape abuse", sub("parts/cover.scad", "// EXPECTED_BBOX: [40, 20, 2]", "// NO_BBOX:"), "declarations"),
    ("hardcoded_thickness", "hard-coded constant", sub("parts/base.scad", "cube([plate_l, plate_w, plate_t]);",
        "cube([plate_l, plate_w, 5]);"), "sensitivity"),
    ("rounded_1u", "rounded standard", sub("params.scad", "cover_t = 2;", "cover_t = 2;\nunit_1U = 44.5;"), "scad_lint"),
    ("computed_default_omitted", "computed default", seq(
        sub("parts/cover.scad", "module cover() {", "module cover(t = 2) {"),
        sub("parts/cover.scad", "cover();\n", "cover();\nmodule twin() { cover(t = cover_t * 1); }\n")), "scad_lint"),
    ("three_parts_no_plan", "§0.5 skipped", seq(put("parts/clip.scad", THIRD),
        sub("assembly.scad", 'else assert', 'else if (n == "clip") translate([60, 0, 0]) cube([10, 10, 2]);\n    else assert'),
        put("joints.json", json.dumps({"contacts": JOINTS["contacts"] + [{"pair": ["clip", "base"], "joint_type": "glued"}]}))), "plan"),
    ("acceptance_weakened_part", "P5 self-weakening", seq(put("acceptance.json", ACC),
        put("acceptance.lock", "LOCK"), sub("params.scad", "plate_t = 5", "plate_t = 3"),
        sub("parts/base.scad", "[40, 20, 5]", "[40, 20, 3]")), "acceptance"),
    ("acceptance_unapproved", "P5 unapproved", put("acceptance.json", ACC), "acceptance"),
    ("acceptance_spec_edited", "P5 spec edited", seq(put("acceptance.json", ACC), put("acceptance.lock", "LOCK"),
        put("acceptance.json", ACC.replace("[40, 20, 5]", "[40, 20, 3]"))), "acceptance"),
    ("bore_refilled", "B refilled cut", seq(put("bores.json", json.dumps([{"name": "b1", "part": "base",
        "start": [10, 10, -0.95], "end": [10, 10, 5.95], "step_mm": 0.25}])),
        sub("parts/base.scad", "base();\n", "base();\ntranslate([8, 8, 2]) cube([4, 4, 1]);\n"),
        sub("parts/base.scad", "THROUGH_HOLES: 2", "THROUGH_HOLES: 1")), "bore_reachability"),
    ("assert_fails", "analytic preflight", sub("params.scad", "cover_t = 2;", "cover_t = 2;\nassert(cover_t > 3, \"cover too thin\");"), "analytic_bounds"),
    ("syntax_error", "render", sub("parts/cover.scad", "cover();\n", "cover(;\n"), "render"),
    ("hole_too_small", "fit", seq(sub("parts/base.scad", "// SENSITIVE_TO", '// EXPECTED_HOLE: [10, 10, 2.5, "Z", 5.0]\n// SENSITIVE_TO')), "features"),
    ("attachment_in_air", "retention", put("attachments.json", json.dumps([{"name": "a1", "part": "cover", "to": "base",
        "at": [20, 10, 10], "feature": "m3 boss", "min_material_mm": 2}])), "attachment"),
    ("motion_without_assembly", "unverifiable", seq(drop("assembly.scad"), put("joints.json", json.dumps(
        dict(JOINTS, motion=[{"part": "cover", "axis": [0, 0, 1], "pivot": [0, 0, 0], "range_deg": [0, 90], "step_deg": 30}])))), "mechanics"),
    ("wrong_library_version", "P14 library drift", seq(put("libs.lock", "BOSL2 2.0.1\n"),
        sub("parts/cover.scad", "include <../params.scad>", "include <../params.scad>\ninclude <BOSL2/std.scad>")), "env"),
    ("unknown_part_in_dispatch", "assembly dispatch", sub("assembly.scad", 'if (n == "base") base();', 'if (n == "bse") base();'), "collisions"),
    ("critical_assumption_open", "unverified input", put("calculations.md",
        "## Decisions log\n\n| Decision | Value | Basis | Criticality | Status |\n|---|---|---|---|---|\n| bolt load | 200 N | guess | Critical | open |\n"), "assumptions"),
    # P8 (2026-11-01): real failures from the training records / SSD sweep, one case each
    ("standoff_caps_hole", "SSD board_shelf: standoffs after difference()", seq(
        sub("parts/base.scad", "base();\n", "base();\nfor (x = [10, 30]) translate([x, 10, plate_t]) cylinder(d = 7, h = 3);\n"),
        sub("parts/base.scad", "[40, 20, 5]", "[40, 20, 8]")), "topology"),
    ("pocket_not_through", "chain-20 / board_shelf: centered cut at z=-1", seq(
        sub("parts/base.scad", "for (x = [10, 30])", "translate([20, 10, -1]) cube([6, 6, plate_t + 2], center = true);\n        for (x = [10, 30])"),
        sub("parts/base.scad", "THROUGH_HOLES: 2", "THROUGH_HOLES: 3")), "topology"),
    ("louver_slots_merged", "cnc_v2_fc_louver: pitch < slot length", seq(
        sub("parts/cover.scad", "for (x = [10, 30])", "for (i = [0:2]) translate([14 + i * 4, 3, -1]) cube([6, 2, cover_t + 2]);\n        for (x = [10, 30])"),
        sub("parts/cover.scad", "THROUGH_HOLES: 2", "THROUGH_HOLES: 5")), "topology"),
    ("peg_narrows_hole", "fc-004: feature blocks part of a hole", seq(
        sub("parts/base.scad", "// SENSITIVE_TO", '// EXPECTED_HOLE: [30, 10, 2.5, "Z", 4.0]\n// SENSITIVE_TO'),
        sub("parts/base.scad", "base();\n", "base();\ntranslate([30.5, 8, 0]) cube([2, 4, plate_t]);\n")), "features"),
    ("negative_height_cube", "chain-19: cube with z_hi < z_lo", seq(
        sub("parts/base.scad", "base();\n", "base();\ntranslate([0, 0, plate_t]) cube([5, 5, -2]);\n")), "render"),
    ("missing_mirrored_part", "chain-25: mirrored half never built", put("acceptance.json", json.dumps(
        {"parts": {"base": {"bbox": [40, 20, 5], "through_holes": 2}, "base_mirror": {"bbox": [40, 20, 5], "through_holes": 2}}})), "acceptance"),
    # controls: must stay green
    ("ctl_no_joint_excused", "control", seq(put("parts/clip.scad", "// NO_JOINT: spare, ships loose\n" + THIRD), put("plan.md", PLAN3)), None),
    ("ctl_blind_hole_declared", "control", seq(sub("parts/base.scad", "for (x = [10, 30]) translate([x, 10, -1]) cylinder(d = hole_d, h = plate_t + 2);",
        "translate([10, 10, -1]) cylinder(d = hole_d, h = plate_t + 2); translate([30, 10, 2]) cylinder(d = hole_d, h = plate_t);"),
        sub("parts/base.scad", "THROUGH_HOLES: 2", "THROUGH_HOLES: 1")), None),
    ("ctl_acceptance_approved", "control", seq(put("acceptance.json", ACC), put("acceptance.lock", "LOCK")), None),
    ("ctl_bores_open", "control", put("bores.json", json.dumps([{"name": "b1", "part": "base",
        "start": [10, 10, -0.95], "end": [10, 10, 5.95], "step_mm": 0.25}])), None),
    ("ctl_attachment_on_material", "control", put("attachments.json", json.dumps([{"name": "a1", "part": "base", "to": "cover",
        "at": [5, 5, 2.5], "feature": "m3 thread", "min_material_mm": 1}])), None),
    ("ctl_hole_declared_true", "control", sub("parts/base.scad", "// SENSITIVE_TO", '// EXPECTED_HOLE: [30, 10, 2.5, "Z", 4.0]\n// SENSITIVE_TO'), None),
    ("ctl_stale_stl_in_build", "control (chain-03)", put("build/base.stl", "solid stale\nendsolid stale\n"), None),
    ("ctl_no_bbox_with_reason", "control", sub("parts/cover.scad", "// EXPECTED_BBOX: [40, 20, 2]", "// NO_BBOX: lid size follows the plate, checked there"), None),
]


def build(case_dir, files, scripts):
    for rel, text in files.items():
        p = os.path.join(case_dir, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scripts", default=DEFAULT_SCRIPTS)
    ap.add_argument("--only", default=None)
    ap.add_argument("--keep", default=None, help="keep case directories here")
    a = ap.parse_args()
    scripts = os.path.abspath(a.scripts)
    root = a.keep or tempfile.mkdtemp(prefix="scad-bench-")
    rows, t0 = [], time.time()
    for name, cls, mut, want in CASES:
        if a.only and a.only != name:
            continue
        files = copy.deepcopy(CLEAN)
        if mut:
            mut(files)
        d = os.path.join(root, name)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        if "acceptance.lock" in files:  # approve the spec as first written (ACC), then apply edits
            build(d, {"acceptance.json": ACC}, scripts)
            subprocess.run([sys.executable, os.path.join(scripts, "acceptance.py"), "approve",
                            "--quote", "bench"], cwd=d, capture_output=True)
            lock = open(os.path.join(d, "acceptance.lock")).read()
            files = dict(files, **{"acceptance.lock": lock})
        build(d, files, scripts)
        r = subprocess.run(["bash", os.path.join(scripts, "validate_scad.sh"), "--all"], cwd=d,
                           capture_output=True, text=True, timeout=900)
        out = r.stdout + r.stderr
        verdicts = dict(re.findall(r"^CHECK_RESULT (\w+)=(\w+)", out, re.M))
        if want is None:
            ok = r.returncode == 0
            got = "green" if ok else "FALSE ALARM: " + ", ".join(k for k, v in verdicts.items() if v in ("FAIL", "INCONCLUSIVE")) + f" (exit {r.returncode})"
        else:
            v = verdicts.get(want)
            ok = r.returncode != 0 and v in ("FAIL", "INCONCLUSIVE")
            got = f"{want}={v} exit {r.returncode}" + ("" if ok else "  MISSED, other: " +
                  ", ".join(k for k, x in verdicts.items() if x == "FAIL"))
        rows.append((name, cls, want, ok, got))
        print(f"{'ok  ' if ok else 'MISS'} {name:28} {cls:22} {got}", flush=True)
    defects = [r for r in rows if r[2] is not None]
    controls = [r for r in rows if r[2] is None]
    caught = sum(r[3] for r in defects)
    alarms = sum(not r[3] for r in controls)
    print(f"\nrecall {caught}/{len(defects)} defects caught by the named check; "
          f"false alarms {alarms}/{len(controls)} controls; {time.time() - t0:.0f} s")
    if not a.keep:
        shutil.rmtree(root, ignore_errors=True)
    return 0 if caught == len(defects) and alarms == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
