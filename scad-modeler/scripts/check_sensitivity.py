#!/usr/bin/env python3
"""Does the part actually follow the parameter it claims to? (P13, 2026-11-01)

A part that writes `4` where it meant `wall` renders, matches its bbox at the
nominal value and passes everything -- until someone changes `wall` in
params.scad and only half the model follows (the hard-coded constant class in
INCIDENTS.md: beam 211 vs 216.5, plates resized without their holes).

    // SENSITIVE_TO: wall

re-renders the part with `-D wall=<value x 1.5>` and fails when the mesh's
bounding box and volume do not change at all. The value is read from the part
file or a file it include<>s/use<>s (one level), so the number is real.

Usage:
    python3 check_sensitivity.py --scad parts/x.scad --stl build/x.stl

Exit codes:
    0  pass, or SKIP when the part declares nothing
    3  fail -- geometry did not change, or the parameter has no numeric value
    4  usage error (missing file, OpenSCAD failed, trimesh missing)
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4
DECL_RE = re.compile(r"^[ \t]*//[ \t]*SENSITIVE_TO[ \t]*:[ \t]*([A-Za-z_]\w*)", re.M)
INC_RE = re.compile(r"^\s*(?:include|use)\s*<([^>]+)>", re.M)
FACTOR = 1.5

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: bash scripts/setup_env.sh", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def value_of(name, scad):
    srcs = [scad]
    text = open(scad, encoding="utf-8", errors="replace").read()
    srcs += [os.path.join(os.path.dirname(scad), m) for m in INC_RE.findall(text)]
    val_re = re.compile(r"(?<![\w.$])" + re.escape(name) + r"\s*=\s*(-?(?:\d+\.?\d*|\.\d+))\s*;")
    found = None
    for p in srcs:  # the part file overrides its includes only if assigned after them; last wins
        if os.path.isfile(p):
            for m in val_re.finditer(open(p, encoding="utf-8", errors="replace").read()):
                found = float(m.group(1))
    return found


def signature(stl):
    m = trimesh.load(stl, force="mesh")
    return [float(x) for x in (m.bounds[1] - m.bounds[0])] + [float(abs(m.volume))]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scad", required=True)
    ap.add_argument("--stl", required=True, help="the nominal render")
    a = ap.parse_args()
    for p in (a.scad, a.stl):
        if not os.path.isfile(p):
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            return EXIT_USAGE
    names = list(dict.fromkeys(DECL_RE.findall(open(a.scad, encoding="utf-8", errors="replace").read())))
    if not names:
        print(f"SKIP: sensitivity, {a.scad} declares no // SENSITIVE_TO: <param>")
        return EXIT_OK
    exe = shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
    base = signature(a.stl)
    fails = []
    with tempfile.TemporaryDirectory() as td:
        for n in names:
            v = value_of(n, a.scad)
            if v is None:
                fails.append(f"{n}: no numeric `{n} = <number>;` in {a.scad} or its includes")
                continue
            new = v * FACTOR if v != 0 else 1.0
            out = os.path.join(td, f"{n}.stl")
            r = subprocess.run([exe, "-q", "-D", f"{n}={new!r}", "-o", out, a.scad],
                               capture_output=True, text=True, timeout=600)
            if r.returncode != 0 or not os.path.isfile(out):
                print(f"ERROR: render with {n}={new:g} failed: {r.stderr.strip()[-300:]}", file=sys.stderr)
                return EXIT_USAGE
            got = signature(out)
            if all(abs(x - y) <= 1e-6 * max(1.0, abs(y)) for x, y in zip(got, base)):
                fails.append(f"{n}: {v:g} -> {new:g} left bbox and volume unchanged -- the part does not use "
                             f"{n} (a hard-coded number where {n} was meant?)")
    if fails:
        for f in fails:
            print(f"FAIL: sensitivity, {a.scad}: {f}")
        return EXIT_FAIL
    print(f"PASS: sensitivity, {a.scad} follows {', '.join(names)}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
