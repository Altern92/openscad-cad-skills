#!/usr/bin/env python3
"""List every subtracted cylinder of a part as a bores.json candidate (P3, 2026-11-01).

bores.json is the input check_bore_reachability.py needs, and nobody wrote it:
bore_reachability was SKIP on 10 of 11 real projects while 22 incidents were
bores sealed or blocked by later geometry. This reads OpenSCAD's own CSG tree
(`openscad -o part.csg`, every transform already flattened to multmatrix), so
the axes are exact, not guessed from the mesh.

The segment is inset 0.05 mm from each end face. A cylinder counts when it is subtracted: a non-first child of difference(), at
any depth (a cutter of a cutter is material again). Its axis from base to top,
transformed into the part's local frame, becomes start/end. Run the reachability
check on the result and it fails when a later union() refilled a cut.

It is a candidate list, not a declaration: delete entries that are not bores
(a pocket, a chamfer cone is already skipped because r1 != r2), and extend
`end` to the far face for a hole that must go all the way through.

Usage:
    python3 bore_candidates.py --scad parts/plate.scad [--part plate] > bores.json
    python3 bore_candidates.py --scad parts/a.scad --scad parts/b.scad   # one list

shortcut: intersection() children keep their parent's polarity, and cones
(r1 != r2) are skipped; upgrade if a real part needs either.

Exit codes:
    0  printed the JSON list (possibly empty)
    4  usage error, or OpenSCAD failed to export the CSG
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

EXIT_OK, EXIT_USAGE = 0, 4
INSET = 0.05  # mm
IDENT_RE = re.compile(r"\s*([A-Za-z_$][\w$]*)\s*\(")


def split_top(s):
    parts, depth, cur = [], 0, []
    for ch in s:
        depth += ch in "([{"
        depth -= ch in ")]}"
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def parse_args(s):
    out = {}
    for p in split_top(s):
        k, _, v = p.partition("=")
        v = v.strip().replace("true", "1").replace("false", "0")
        try:
            out[k.strip()] = json.loads(v)
        except ValueError:
            out[k.strip()] = v
    return out


def match(src, i, open_ch, close_ch):
    depth = 0
    for j in range(i, len(src)):
        depth += src[j] == open_ch
        depth -= src[j] == close_ch
        if depth == 0:
            return j
    raise ValueError(f"unbalanced {open_ch} at {i}")


def parse(src, i=0):
    """[(name, args, children)] until a closing brace or end of input."""
    nodes = []
    while True:
        while i < len(src) and src[i] in " \t\r\n;":
            i += 1
        if i >= len(src) or src[i] == "}":
            return nodes, i
        m = IDENT_RE.match(src, i)
        if not m:
            raise ValueError(f"unexpected CSG text at {i}: {src[i:i + 40]!r}")
        a0 = m.end() - 1
        a1 = match(src, a0, "(", ")")
        name, args, i = m.group(1), parse_args(src[a0 + 1:a1]), a1 + 1
        while i < len(src) and src[i] in " \t\r\n":
            i += 1
        children = []
        if i < len(src) and src[i] == "{":
            children, i = parse(src, i + 1)
            i += 1
        nodes.append((name, args, children))


def matmul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def apply(m, p):
    return [m[r][0] * p[0] + m[r][1] * p[1] + m[r][2] * p[2] + m[r][3] for r in range(3)]


IDENTITY = [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]


def walk(nodes, m, cut, out):
    for name, args, children in nodes:
        if name == "multmatrix":
            walk(children, matmul(m, args.get("m") or args.get("") or IDENTITY), cut, out)
        elif name == "difference":
            for k, ch in enumerate(children):
                walk([ch], m, cut if k == 0 else not cut, out)
        elif name == "cylinder":
            if not cut:
                continue
            h, r1, r2 = float(args.get("h", 1)), float(args.get("r1", 1)), float(args.get("r2", 1))
            if abs(r1 - r2) > 1e-9:
                continue
            z0 = -h / 2 if args.get("center") in (1, True) else 0.0
            # the cutter's own end faces touch whatever it was pushed into; sampling exactly
            # there read solid (real gearbox_frame, z=18), so the segment starts INSET mm inside
            inset = min(INSET, h / 4)
            out.append((apply(m, [0, 0, z0 + inset]), apply(m, [0, 0, z0 + h - inset]), 2 * r1))
        else:
            walk(children, m, cut, out)


def first_matrix_arg(src):
    # multmatrix's matrix is a positional argument; give it a key so parse_args keeps it
    return re.sub(r"multmatrix\(\s*\[", "multmatrix(m = [", src)


def candidates(scad, part):
    exe = shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
    with tempfile.TemporaryDirectory() as td:
        csg = os.path.join(td, "part.csg")
        r = subprocess.run([exe, "-q", "-o", csg, scad], capture_output=True, text=True, timeout=300)
        if r.returncode != 0 or not os.path.isfile(csg):
            raise RuntimeError(f"openscad could not export CSG for {scad}: {r.stderr.strip()[-300:]}")
        src = first_matrix_arg(open(csg, encoding="utf-8").read())
    tree, _ = parse(src)
    found = []
    walk(tree, IDENTITY, False, found)
    out = []
    for i, (s, e, d) in enumerate(found, 1):
        out.append({"name": f"{part}_bore{i}_d{d:g}", "part": part,
                    "start": [round(x, 6) for x in s], "end": [round(x, 6) for x in e],
                    "diameter": round(d, 6), "step_mm": 0.25})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scad", action="append", required=True)
    ap.add_argument("--part", default=None, help="part name (default: the .scad basename); one --scad only")
    a = ap.parse_args()
    if a.part and len(a.scad) > 1:
        print("ERROR: --part works with a single --scad", file=sys.stderr)
        return EXIT_USAGE
    allc = []
    for scad in a.scad:
        if not os.path.isfile(scad):
            print(f"ERROR: file not found: {scad}", file=sys.stderr)
            return EXIT_USAGE
        try:
            allc += candidates(scad, a.part or os.path.splitext(os.path.basename(scad))[0])
        except (RuntimeError, ValueError, subprocess.SubprocessError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return EXIT_USAGE
    print(json.dumps(allc, indent=1))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
