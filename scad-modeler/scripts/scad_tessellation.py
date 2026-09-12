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
   Same expression, different meaning. OpenSCAD emits vertex i at
   `phi = 360*i/n` (verified in upstream primitives.cc, 2026-08-18), so vertex 0
   sits at angle 0 and the bbox touches the ideal radius wherever a vertex lands
   on an axis:
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

# src/geometry/Grid.h: const double GRID_FINE = 0.00000095367431640625 (2^-20).
# Below this radius OpenSCAD short-circuits to 3 fragments. Dimensionally
# irrelevant at any real size; mirrored only so this stays a faithful copy.
GRID_FINE = 0.00000095367431640625

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
    """Facet count for a full circle of radius r -- mirrors OpenSCAD's own
    fragment calculation (verified against upstream source, 2026-08-18):

        r < GRID_FINE ? 3
      : fn > 0        ? max(3, fn)
      :                 ceil(max(min(360/fa, 2*pi*r/fs), 5))
    """
    if r < GRID_FINE:
        return 3
    if fn and fn > 0:
        return max(3, int(fn))
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

# --- Minkowski fillet shortfall -------------------------------------------
# bbox_error_bound() above assumes the axis extent is set by a curved surface
# of the part's OWN size, so it evaluates the inscribed-polygon shortfall at
# r = dim/2 with the file's global $fn/$fa/$fs. A minkowski() sum with a
# faceted sphere breaks that assumption: the extent is set by the SPHERE's
# radius and the SPHERE's $fn, which are usually far smaller than the part.
#
# Measured (INCIDENTS.md, 2026-09-12) on server_rack_modular_v4/v8
# parts/node.scad:
#     minkowski() { cube([node_s - fillet_post, ...]); sphere(r = fillet_post/2, $fn = 24); }
# with node_s = 26 and fillet_post = 2.5. Declared bbox 26.0, rendered 25.9786
# -- short by exactly 0.0214 mm. bbox_error_bound() gives 2*13*(1-cos(pi/180))
# = 0.0040 mm, which the 0.005 floor swallows, so the check reported a FAIL on
# a part that is 0.08% off nominal. The real bound is 2*r*(1-cos(pi/$fn)) at
# the SPHERE's r and $fn: 2*1.25*(1-cos(pi/24)) = 0.0214 mm. Same formula,
# different inputs -- which is why this is a separate term and not a floor bump.
_MINKOWSKI_RE = re.compile(r"\bminkowski\s*\(")
_SPHERE_RE = re.compile(r"\bsphere\s*\(([^)]*)\)")
_NUM_ARG_RE = re.compile(r"\br\s*=\s*([^,)]+)")
_FN_ARG_RE = re.compile(r"\$fn\s*=\s*([0-9.]+)")
_ASSIGN_RE = re.compile(r"^[ \t]*([A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*([0-9.]+)[ \t]*;")


def parse_scalar_vars(scad_path, _depth=0, _seen=None):
    """Numeric top-level assignments (name -> float), following include one
    level. Enough to resolve 'sphere(r = fillet_post/2, ...)' when the
    parameter is a plain literal in the part or its params.scad.
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
                            included.update(parse_scalar_vars(dep, _depth + 1, _seen))
                    continue
                m = _ASSIGN_RE.match(line)
                if m:
                    try:
                        found[m.group(1)] = float(m.group(2))
                    except ValueError:
                        pass
    except OSError:
        return included
    included.update(found)
    return included


def _resolve_radius(expr, scalars):
    """'1.25' | 'fillet_post/2' | 'w/2' -> float, or None if not resolvable.
    Returns None rather than guessing: an invented radius would silently widen
    the tolerance, which is the failure mode this whole module exists to avoid.
    """
    expr = expr.strip()
    try:
        return float(expr)
    except ValueError:
        pass
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*/\s*([0-9.]+)$", expr)
    if m and m.group(1) in scalars:
        try:
            return scalars[m.group(1)] / float(m.group(2))
        except (ValueError, ZeroDivisionError):
            return None
    if expr in scalars:
        return scalars[expr]
    return None


def minkowski_sphere_deficit(scad_path, _depth=0, _seen=None, _scalars=None):
    """Largest bounding-box shortfall contributed by a faceted sphere inside a
    minkowski() sum, in mm for ONE axis. 0.0 when the file has no minkowski()
    with a resolvable sphere -- the caller then keeps its existing tolerance.
    """
    if _seen is None:
        _seen = set()
    real = os.path.realpath(scad_path)
    if real in _seen or _depth > 1:
        return 0.0
    _seen.add(real)
    if _scalars is None:
        _scalars = parse_scalar_vars(scad_path)

    try:
        text = open(scad_path, "r", encoding="utf-8").read()
    except OSError:
        return 0.0

    lines = [_LINE_COMMENT_RE.sub("", l) for l in text.splitlines()]
    worst = 0.0
    for i, line in enumerate(lines):
        if not _MINKOWSKI_RE.search(line):
            continue
        # Walk to the matching close BRACE of the minkowski() block, so a
        # sphere after the block cannot be attributed to it. Braces, not
        # parens: the block form is 'minkowski() { ... }' and its own
        # parentheses are already balanced on the first line -- walking parens
        # stops immediately and finds no sphere at all (hit exactly this while
        # building it: deficit came back 0.0 for node.scad).
        depth = 0
        started = False
        body = []
        for j in range(i, min(i + 60, len(lines))):
            seg = lines[j]
            body.append(seg)
            for ch in seg:
                if ch == "{":
                    depth += 1
                    started = True
                elif ch == "}":
                    depth -= 1
            if started and depth <= 0:
                break
        for seg in body:
            for m in _SPHERE_RE.finditer(seg):
                args = m.group(1)
                fn_m = _FN_ARG_RE.search(args)
                r_m = _NUM_ARG_RE.search(args)
                if not fn_m or not r_m:
                    continue
                try:
                    n = float(fn_m.group(1))
                except ValueError:
                    continue
                if n < 3:
                    continue
                r = _resolve_radius(r_m.group(1), _scalars)
                if r is None or r <= 0:
                    continue
                worst = max(worst, 2.0 * r * (1.0 - math.cos(math.pi / n)))
    return worst
