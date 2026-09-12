#!/usr/bin/env python3
"""Print one STL's bounding-box size as "dx dy dz", for a given file.

Why this is a script and not an inline snippet
----------------------------------------------
validate_scad.sh needs to tell a positioned part from a whole assembly, and it
first tried to do that by comparing FILE SIZES. That produced a false positive on
the very first complete test project: a base plate with four screw holes carries
more triangles than the small assembly it belongs to. So it switched to
comparing bounding boxes -- with the comparison written as an inline python -c
that assumed a BINARY STL.

OpenSCAD writes ASCII STL by default ("solid OpenSCAD_Model"). The inline parser
read garbage, raised, and the shell call was wrapped in "|| echo 0" so the
failure became a silent "0 parts are suspicious" -- the tripwire stopped
detecting anything at all, and nothing said so. Caught by re-measuring the one
case it was built for: all 136 collision pairs in server_rack_modular_v4 again
reported the same 170.000mm, which is the signature of 17 copies of the whole
assembly (INCIDENTS.md, 2026-09-12).

Two lessons are encoded here rather than in a comment elsewhere:
  * handle BOTH STL encodings, because the writer chooses;
  * never swallow the error -- this exits non-zero and says so, so the caller
    can fail loudly instead of passing by default.
"""
import struct
import sys


def _binary_extent(fh):
    fh.read(80)
    raw = fh.read(4)
    if len(raw) != 4:
        raise ValueError("truncated binary STL header")
    n = struct.unpack("<I", raw)[0]
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for _ in range(n):
        rec = fh.read(50)
        if len(rec) != 50:
            raise ValueError("truncated binary STL: expected %d triangles" % n)
        for k in range(3):
            vx, vy, vz = struct.unpack_from("<3f", rec, 12 + 12 * k)
            for a, v in enumerate((vx, vy, vz)):
                if v < lo[a]:
                    lo[a] = v
                if v > hi[a]:
                    hi[a] = v
    return [hi[a] - lo[a] for a in range(3)]


def _ascii_extent(fh):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    seen = 0
    for line in fh:
        s = line.strip()
        if not s.startswith(b"vertex"):
            continue
        parts = s.split()
        if len(parts) < 4:
            continue
        vals = [float(x) for x in parts[1:4]]
        seen += 1
        for a, v in enumerate(vals):
            if v < lo[a]:
                lo[a] = v
            if v > hi[a]:
                hi[a] = v
    if seen == 0:
        raise ValueError("no 'vertex' lines found -- not a recognisable STL")
    return [hi[a] - lo[a] for a in range(3)]


def extent(path):
    with open(path, "rb") as fh:
        head = fh.read(512)
        if head.lstrip()[:5].lower() == b"solid":
            # ASCII files start with "solid", but so do some binary writers --
            # the reliable test is whether the body contains 'facet'.
            if b"facet" in head or b"vertex" in head:
                fh.seek(0)
                return _ascii_extent(fh)
        fh.seek(0)
        return _binary_extent(fh)


def main():
    if len(sys.argv) < 2:
        print("usage: stl_extent.py <file.stl> [...]", file=sys.stderr)
        return 4
    for p in sys.argv[1:]:
        try:
            e = extent(p)
        except Exception as ex:
            print("ERROR: cannot read %s: %s" % (p, ex), file=sys.stderr)
            return 3
        print("%.6f %.6f %.6f" % (e[0], e[1], e[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
