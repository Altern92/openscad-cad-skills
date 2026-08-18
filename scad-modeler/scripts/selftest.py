#!/usr/bin/env python3
"""End-to-end acceptance test: build a known part, then check the checkers.

Everything in these skills was developed where no OpenSCAD binary was
available, so the Python side is well tested and the OpenSCAD side -- the
Pattern 0 functions in patterns.scad, and whether the whole render → export →
verify chain actually runs -- was only reasoned about. This script closes that
gap in one command on a machine that has OpenSCAD.

It builds a plate with one bore whose correct answers are known in advance,
runs the real toolchain over it, and checks that each tool reaches the right
verdict -- including that check_features.py FAILS on a deliberately
uncompensated bore. A checker that never fails proves nothing.

It also settles two questions the skills carry as open:
  * whether `openscad --summary` reports a bounding box directly, which would
    make the STL round-trip in check_dimensions.py unnecessary;
  * whether true_hole() from patterns.scad parses and renders at all.

Usage:
    python3 selftest.py             # uses a temp dir, cleans up
    python3 selftest.py --keep      # leave the generated project for inspection

Exit codes:
    0  everything passed
    1  a check reached the wrong verdict -- read the output, something is broken
    3  no OpenSCAD binary; nothing could be tested
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doctor import find_openscad, probe_openscad  # noqa: E402
from scad_tessellation import fragments_for_r  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXIT_OK, EXIT_FAIL, EXIT_NO_SCAD = 0, 1, 3

PLATE_W, PLATE_D, PLATE_H = 40.0, 20.0, 10.0
BORE_D = 8.0
FA, FS = 2.0, 0.3


def find_patterns():
    """patterns.scad lives in the sibling skill, which may be installed
    separately rather than as part of this repo."""
    for cand in (
        os.path.join(HERE, "..", "..", "openscad-cad", "references", "patterns.scad"),
        os.path.expanduser("~/.claude/skills/openscad-cad/references/patterns.scad"),
    ):
        if os.path.isfile(cand):
            return os.path.abspath(cand)
    return None


def write_project(d, patterns):
    """A plate with two bores: one compensated, one deliberately not."""
    shutil.copy(patterns, os.path.join(d, "patterns.scad"))
    scad = f"""// selftest plate -- generated, do not edit
use <patterns.scad>
$fa = {FA}; $fs = {FS};

plate_w = {PLATE_W}; plate_d = {PLATE_D}; plate_h = {PLATE_H};
bore_d  = {BORE_D};

// EXPECTED_BBOX: [{PLATE_W}, {PLATE_D}, {PLATE_H}]
// EXPECTED_HOLE: [-10, 0, 5, "Z", {BORE_D}]

difference() {{
    translate([-plate_w/2, -plate_d/2, 0]) cube([plate_w, plate_d, plate_h]);
    // Compensated: should measure bore_d across flats.
    translate([-10, 0, -1]) true_hole(d = bore_d, h = plate_h + 2);
    // Uncompensated: should measure short. Its declaration lives in the
    // bad-bore file so the good run stays clean.
    translate([10, 0, -1]) cylinder(d = bore_d, h = plate_h + 2);
}}
"""
    open(os.path.join(d, "plate.scad"), "w").write(scad)
    # Same geometry, but declaring the UNcompensated bore -- check_features.py
    # must fail on this one.
    open(os.path.join(d, "plate_badbore.scad"), "w").write(
        scad.replace(f'// EXPECTED_HOLE: [-10, 0, 5, "Z", {BORE_D}]',
                     f'// EXPECTED_HOLE: [10, 0, 5, "Z", {BORE_D}]'))


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600, **kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    scad_bin = find_openscad()
    if not scad_bin:
        print("No OpenSCAD binary found -- this test needs one. See doctor.py.")
        return EXIT_NO_SCAD
    info = probe_openscad(scad_bin)
    print(f"OpenSCAD: {info['version']}\n")

    patterns = find_patterns()
    if not patterns:
        print("FAIL  patterns.scad not found -- is the openscad-cad skill present?")
        return EXIT_FAIL

    d = tempfile.mkdtemp(prefix="scad-selftest-")
    results = []

    def record(name, ok, detail=""):
        results.append((name, ok, detail))
        print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")

    try:
        write_project(d, patterns)
        stl = os.path.join(d, "plate.stl")
        cmd = [scad_bin]
        if info.get("manifold"):
            cmd += ["--backend=Manifold"]
        cmd += ["-o", stl, "--export-format=binstl", os.path.join(d, "plate.scad")]

        print("1. Does patterns.scad render at all?")
        r = run(cmd)
        rendered = os.path.isfile(stl) and os.path.getsize(stl) > 0
        record("true_hole() parses and renders", rendered,
               "" if rendered else (r.stderr or r.stdout)[-300:])
        if not rendered:
            return EXIT_FAIL

        print("\n2. Do the checkers reach the right verdicts?")
        cd = run([sys.executable, os.path.join(HERE, "check_dimensions.py"),
                  "--stl", stl, "--scad", os.path.join(d, "plate.scad")])
        record("envelope check passes on a correct plate", cd.returncode == 0,
               cd.stdout.strip().splitlines()[-1] if cd.stdout else "")

        cf = run([sys.executable, os.path.join(HERE, "check_features.py"),
                  "--stl", stl, "--scad", os.path.join(d, "plate.scad")])
        record("compensated bore passes", cf.returncode == 0,
               cf.stdout.strip().splitlines()[0].strip() if cf.stdout else "")

        cb = run([sys.executable, os.path.join(HERE, "check_features.py"),
                  "--stl", stl, "--scad", os.path.join(d, "plate_badbore.scad")])
        n = fragments_for_r(BORE_D / 2, 0, FA, FS)
        expect = BORE_D * (1 - __import__("math").cos(__import__("math").pi / n))
        record("UNcompensated bore fails, as it must", cb.returncode == 1,
               f"(theory: short by {expect:.4f} mm at n={n})")
        if cb.stdout:
            for line in cb.stdout.strip().splitlines():
                if "across-flats" in line:
                    print(f"        {line.strip()}")

        print("\n3. Open question: can --summary replace the STL round-trip?")
        if not info.get("summary"):
            record("--summary supported", False, "this build has no --summary")
        else:
            s = run([scad_bin, "--render", "--summary", "all", "--summary-file", "-",
                     os.path.join(d, "plate.scad")])
            out = (s.stdout or "") + (s.stderr or "")
            has_bbox = "bounding" in out.lower() or '"bbox"' in out.lower()
            record("--summary reports a bounding box without -o", has_bbox,
                   "check_dimensions.py could skip the STL export"
                   if has_bbox else "STL round-trip stays necessary")
            if "volume" in out.lower():
                print("        note: 'volume' appears in the summary output too")
            print("        --- summary output ---")
            for line in out.strip().splitlines()[:25]:
                print(f"        {line}")

    finally:
        if args.keep:
            print(f"\nProject kept at {d}")
        else:
            shutil.rmtree(d, ignore_errors=True)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("Failed: " + ", ".join(failed))
        print("Note: the --summary check is informational -- a failure there means "
              "the skills keep the STL round-trip, not that anything is broken.")
    return EXIT_FAIL if any(
        not ok for n, ok, _ in results if "summary" not in n) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
