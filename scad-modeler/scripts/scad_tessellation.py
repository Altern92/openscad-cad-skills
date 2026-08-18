#!/usr/bin/env python3
"""Mirror of OpenSCAD's facet-count logic, plus the tessellation error bounds
derived from it. Shared by check_dimensions.py; importable on its own.

Why this exists
---------------
OpenSCAD approximates every circular surface with a regular polygon whose
vertices lie ON the ideal circle (an *inscribed* polygon). Two different
errors follow from that, and conflating them produces wrong tolerances:

1. ACROSS-FLATS DEFICIT (the fit-relevant one).
   The polygon's apothem -- the shortest centre-to-edge distance -- is
   a = r*cos(pi/n), not r. A shaft entering a hole binds on the apothem, so a
   modelled hole is effectively UNDERSIZED by r*(1 - cos(pi/n)) per side.
   This is what `circumscribed_d()` in openscad-cad/references/patterns.scad
   compensates for. It is a pure CAD/geometry error -- nothing to do with the
   printer.

2. BOUNDING-BOX DEVIATION (what an STL bbox check can actually see).
   NOT the same number. OpenSCAD places a polygon vertex at angle 0, so the
   bbox touches the ideal radius wherever a vertex lands on an axis:
     - n divisible by 4  -> vertices at 0/90/180/270 deg, bbox error ~= 0
     - n even, n%4 == 2  -> X exact, Y short by 2r*(1 - cos(pi/n))
     - n odd             -> both axes short by up to 2r*(1 - cos(pi/n))
   So 2r*(1 - cos(pi/n)) is a safe UPPER BOUND on the per-axis bbox error, but
   the typical value for a cylinder is zero.

   Practical consequence, and it matters: a bounding-box check is largely BLIND
   to error #1. It catches gross scale mistakes; it does not catch an
   undersized hole. Fit-critical round features need a feature-level check, not
   a bbox check.

This module computes #2 (the bound), because that is what a bbox tolerance
should be derived from. Formerly check_dimensions.py used a flat
`max(0.3mm, 1%)`, which is one to two orders of magnitude looser than the real
tessellation error and therefore not a meaningful gate.
"""
import math
import os
import re

# OpenSCAD's own defaults when a file sets none of them.
DEFAULT_FA = 12.0
DEFAULT_FS = 2.0
DEFAULT_FN = 0.0

# Floor for float32 STL storage plus mesh export rounding. At 200 mm a float32
# ulp is ~2.4e-5 mm and a bbox spans two of them, so 0.005 mm is generous
# without being meaningless.
NUMERIC_FLOOR_MM = 0.005

# Not anchored to line start: the skill's own params.scad template puts several
# on one line ("$fa = 2; $fs = 0.3;"), and anchoring would silently miss all but
# the first -- which would then fall back to OpenSCAD's much coarser defaults
# and produce a tolerance an order of magnitude too loose.
_SPECIAL_RE = {
    "fn": re.compile(r'\$fn\s*=\s*([0-9.eE+\-]+)\s*;'),
    "fa": re.compile(r'\$fa\s*=\s*([0-9.eE+\-]+)\s*;'),
    "fs": re.compile(r'\$fs\s*=\s*([0-9.eE+\-]+)\s*;'),
}
_INCLUDE_RE = re.compile(r'^\s*(?:include|use)\s*<([^>]+)>')
_LINE_COMMENT_RE = re.compile(r'//.*$')


def fragments_for_r(r, fn=DEFAULT_FN, fa=DEFAULT_FA, fs=DEFAULT_FS):
    """Facet count for a full circle of radius r -- mirrors OpenSCAD's
    Calc::get_fragments_from_r():

        fn > 0 ? max(3, fn)
               : ceil(max(min(360/fa, 2*pi*r/fs), 5))
    """
    if fn and fn > 0:
        return max(3, int(fn))
    if r <= 0:
        return 5
    return int(math.ceil(max(min(360.0 / fa, r * 2.0 * math.pi / fs), 5)))


def across_flats_deficit(d, fn=DEFAULT_FN, fa=DEFAULT_FA, fs=DEFAULT_FS):
    """Diametral undersize of a modelled circular feature, i.e. how much
    smaller the polygon is flat-to-flat than the nominal diameter d.
    This is error #1 -- the one that makes a hole too tight.
    """
    r = d / 2.0
    n = fragments_for_r(r, fn, fa, fs)
    return d * (1.0 - math.cos(math.pi / n))


def bbox_error_bound(dim, fn=DEFAULT_FN, fa=DEFAULT_FA, fs=DEFAULT_FS):
    """Upper bound on the bounding-box shortfall along one axis, assuming the
    worst case that the extent is set by a curved surface of diameter `dim`
    whose polygon phase is unfavourable. Zero for purely planar geometry --
    using the bound as a tolerance is deliberately conservative.
    """
    r = abs(dim) / 2.0
    n = fragments_for_r(r, fn, fa, fs)
    return 2.0 * r * (1.0 - math.cos(math.pi / n))


def parse_special_vars(scad_path, _depth=0, _seen=None):
    """Read $fn/$fa/$fs from a .scad file, following include/use one level so
    that the common layout -- $fa/$fs declared in params.scad, part files
    including it -- resolves correctly. Later assignments win, and the file's
    own assignments win over an included file's.
    """
    if _seen is None:
        _seen = set()
    real = os.path.realpath(scad_path)
    if real in _seen or _depth > 1:
        return {}
    _seen.add(real)

    found = {}
    included = {}
    try:
        with open(scad_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = _LINE_COMMENT_RE.sub("", raw)
                m = _INCLUDE_RE.match(line)
                if m:
                    if _depth < 1:
                        dep = os.path.join(os.path.dirname(scad_path), m.group(1))
                        if os.path.isfile(dep):
                            included.update(parse_special_vars(dep, _depth + 1, _seen))
                    continue
                for key, rx in _SPECIAL_RE.items():
                    for m2 in rx.finditer(line):
                        try:
                            found[key] = float(m2.group(1))
                        except ValueError:
                            pass
    except OSError:
        return included

    included.update(found)
    return included


def resolve_special_vars(scad_path, fn=None, fa=None, fs=None):
    """Merge CLI overrides > file/include declarations > OpenSCAD defaults.
    Returns (fn, fa, fs, source) where source describes where they came from.
    """
    parsed = parse_special_vars(scad_path)
    out_fn = fn if fn is not None else parsed.get("fn", DEFAULT_FN)
    out_fa = fa if fa is not None else parsed.get("fa", DEFAULT_FA)
    out_fs = fs if fs is not None else parsed.get("fs", DEFAULT_FS)

    if fn is not None or fa is not None or fs is not None:
        source = "CLI override"
    elif parsed:
        source = f"parsed from {os.path.basename(scad_path)} (or its includes)"
    else:
        source = "OpenSCAD defaults ($fa=12, $fs=2) -- none declared"
    return out_fn, out_fa, out_fs, source
