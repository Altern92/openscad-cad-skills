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
import ast
import math
import operator
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
#
# What resolves (NEXT.md 3b item 3, 2026-11-14): the sphere's radius as
#   r = <expr> | d = <expr> (r = d/2) | positional sphere(<expr>, ...)
# where <expr> is + - * / and parentheses over numeric literals and top-level
# scalars of the part or a file it include<>s (one level; a scalar may itself
# be such an expression of other scalars). Facets from the sphere's own
# $fn/$fa/$fs; any it lacks come from the file's globals, but ONLY when the
# minkowski() is top-level code with no $fn/$fa/$fs on its enclosing calls --
# inside a module a caller can pass its own.
# What stays SKIPPED (term 0, the part keeps the tight tolerance): function
# calls, conditionals, vectors, module parameters and any name rebound inside
# the enclosing module (module header, 'name =' in for/let/local assignment),
# use<>d files (use does not import variables), cylinder()/circle() and spheres
# inside a child module. Skipped, never guessed: an invented radius would
# silently widen the tolerance, the failure this module exists to prevent.
_MINKOWSKI_RE = re.compile(r"\bminkowski\s*\(")
_SPHERE_RE = re.compile(r"\bsphere\s*\(")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
_INCLUDE_LINE_RE = re.compile(r"^\s*(include|use)\s*<([^>]+)>.*$", re.M)
_STMT_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)\s*(.+?)\s*$", re.S)
_ARG_RE = re.compile(r"^\s*(\$?[A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)\s*(.*?)\s*$", re.S)
_SPECIAL_ANY_RE = re.compile(r"\$f[nas]\b")
_MODULE_HDR_RE = re.compile(r"\bmodule\s+[A-Za-z_][A-Za-z0-9_]*\s*\(([^)]*)\)")
_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv}


def _strip_comments(text):
    return re.sub(r"//[^\n]*", "", _BLOCK_COMMENT_RE.sub("", text))


def _eval_expr(expr, lookup):
    """+ - * / and parentheses over numbers and names (lookup(name) -> float
    or None). None for anything else, an unknown name, or division by zero.
    OpenSCAD and Python agree on this subset; '^', '%', calls, '?:' and
    vectors fall outside it and return None.
    """
    try:
        tree = ast.parse(expr.strip(), mode="eval").body
    except (SyntaxError, ValueError):
        return None

    def ev(n):
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            return float(n.value)
        if isinstance(n, ast.Name):
            return lookup(n.id)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand)
            return None if v is None else (-v if isinstance(n.op, ast.USub) else v)
        if isinstance(n, ast.BinOp) and type(n.op) in _BINOPS:
            a, b = ev(n.left), ev(n.right)
            if a is None or b is None or (isinstance(n.op, ast.Div) and b == 0):
                return None
            return _BINOPS[type(n.op)](a, b)
        return None

    v = ev(tree)
    return v if v is not None and math.isfinite(v) else None


def _scalar_exprs(scad_path, _depth=0, _seen=None):
    """Top-level 'name = expr;' statements (name -> expr text) of a file and,
    one level deep, the files it include<>s. use<> is not followed: OpenSCAD
    does not import a used file's variables. Assignments inside module bodies
    or other braces are local and ignored. The file's own win over includes.
    """
    if _seen is None:
        _seen = set()
    real = os.path.realpath(scad_path)
    if real in _seen or _depth > 1:
        return {}
    _seen.add(real)
    try:
        text = _strip_comments(open(scad_path, "r", encoding="utf-8").read())
    except OSError:
        return {}
    exprs = {}
    for m in _INCLUDE_LINE_RE.finditer(text):
        if m.group(1) == "include" and _depth < 1:
            dep = os.path.join(os.path.dirname(scad_path), m.group(2))
            if os.path.isfile(dep):
                exprs.update(_scalar_exprs(dep, _depth + 1, _seen))
    text = _INCLUDE_LINE_RE.sub("", text)
    depth, buf = 0, []
    for c in text:
        if c == "{":
            depth += 1
            buf = []
        elif c == "}":
            depth -= 1
            buf = []
        elif depth == 0:
            if c == ";":
                m = _STMT_ASSIGN_RE.match("".join(buf))
                if m:
                    exprs[m.group(1)] = m.group(2)
                buf = []
            else:
                buf.append(c)
    return exprs


def parse_scalar_vars(scad_path):
    """Top-level scalars (name -> float) of a part and its include<>s, with
    computed ones ('fillet = wall * 0.75;') evaluated from the others. Names
    whose value is not plain arithmetic over resolvable names are left out.
    Values are the FINAL assignment, as in OpenSCAD.
    """
    exprs = _scalar_exprs(scad_path)
    out, busy = {}, set()

    def get(name):
        if name in out:
            return out[name]
        if name not in exprs or name in busy:   # unknown or circular
            return None
        busy.add(name)
        v = _eval_expr(exprs[name], get)
        busy.discard(name)
        if v is not None:
            out[name] = v
        return v

    for name in exprs:
        get(name)
    return out


def _close(text, i, open_ch, close_ch):
    """Index of the bracket closing the one at text[i], or -1."""
    depth = 0
    for j in range(i, len(text)):
        if text[j] == open_ch:
            depth += 1
        elif text[j] == close_ch:
            depth -= 1
            if depth == 0:
                return j
    return -1


def _split_args(s):
    out, depth, cur = [], 0, []
    for c in s:
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        if c == "," and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    out.append("".join(cur))
    return [a for a in out if a.strip()]


def _top_stmt_start(text, pos):
    """(start of the top-level statement containing pos, brace depth at pos)."""
    depth, start = 0, 0
    for i in range(pos):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                start = i + 1
        elif c == ";" and depth == 0:
            start = i + 1
    return start, depth


def minkowski_sphere_deficit(scad_path, _scalars=None):
    """Largest bounding-box shortfall contributed by a faceted sphere inside a
    minkowski() sum, in mm for ONE axis. 0.0 when the file has no minkowski()
    with a resolvable sphere -- the caller then keeps its existing tolerance.
    Resolved and skipped radius forms: see the comment block above.
    """
    if _scalars is None:
        _scalars = parse_scalar_vars(scad_path)
    try:
        text = _strip_comments(open(scad_path, "r", encoding="utf-8").read())
    except OSError:
        return 0.0

    worst = 0.0
    for mk in _MINKOWSKI_RE.finditer(text):
        # Block form 'minkowski() { ... }': walk to the matching close BRACE so
        # a sphere after the block cannot be attributed to it.
        close_p = _close(text, mk.end() - 1, "(", ")")
        if close_p < 0:
            continue
        rest = text[close_p + 1:]
        if not rest.lstrip().startswith("{"):
            continue
        b0 = close_p + 1 + (len(rest) - len(rest.lstrip()))
        b1 = _close(text, b0, "{", "}")
        if b1 < 0:
            continue
        stmt_start, depth = _top_stmt_start(text, mk.start())
        before = text[stmt_start:mk.start()]   # enclosing module header/calls
        params = set()
        for h in _MODULE_HDR_RE.finditer(before):
            params.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", h.group(1)))

        for sm in _SPHERE_RE.finditer(text, b0, b1):
            a1 = _close(text, sm.end() - 1, "(", ")")
            if a1 < 0:
                continue
            # Names rebound between the statement start and this call
            # (module params, for/let, local assignment) shadow file scalars.
            scope = before + text[mk.start():sm.start()]

            def lookup(name, scope=scope):
                if name in params or re.search(r"\b%s\s*=(?!=)" % re.escape(name), scope):
                    return None
                return _scalars.get(name)

            named, positional = {}, []
            for a in _split_args(text[sm.end():a1]):
                m = _ARG_RE.match(a)
                if m:
                    named[m.group(1)] = m.group(2)
                else:
                    positional.append(a)
            r_srcs = [e for e in (named.get("r"), positional[0] if positional else None) if e]
            if len(r_srcs) + ("d" in named) != 1:
                continue   # no radius, or r and d both given
            if r_srcs:
                r = _eval_expr(r_srcs[0], lookup)
            else:
                d = _eval_expr(named["d"], lookup)
                r = None if d is None else d / 2.0
            if r is None or r <= 0:
                continue

            special = {}
            for k in ("fn", "fa", "fs"):
                if "$" + k in named:
                    special[k] = _eval_expr(named["$" + k], lookup)
                    if special[k] is None:
                        break      # unresolvable facet setting: skip this sphere
            else:
                if not special.get("fn", 0) > 0:
                    if depth > 0 or _SPECIAL_ANY_RE.search(scope):
                        continue   # caller/enclosing $fn could override globals
                    g = resolve_special_vars(scad_path)
                    for k, v in zip(("fn", "fa", "fs"), g[:3]):
                        special.setdefault(k, v)
                if special.get("fa", DEFAULT_FA) <= 0 or special.get("fs", DEFAULT_FS) <= 0:
                    continue
                n = fragments_for_r(r, special.get("fn", 0.0),
                                    special.get("fa", DEFAULT_FA),
                                    special.get("fs", DEFAULT_FS))
                worst = max(worst, 2.0 * r * (1.0 - math.cos(math.pi / n)))
    return worst
