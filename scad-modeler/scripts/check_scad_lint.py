#!/usr/bin/env python3
"""Static SCAD lint for two "not yet promoted" incident shapes (P2, 2026-11-01).

1. Numeric default for a computed dimension (INCIDENTS.md 2026-09-04,
   server_rack part4): `module beam(len = 211)` while assembly.scad called
   `beam(len = span - 2*node_r)` = 216.5. Any call that forgot the argument
   silently got 211 and the beam rammed 10 mm into the node. Rule: FAIL when
   one call computes an argument (non-literal) while another call omits it
   and so gets the numeric default -- the callers disagree about where the
   value comes from. (Defaults alone are fine: on BOSL2/NopSCADlib/MCAD the
   looser "any computed caller" rule fired on ordinary library API defaults.)

2. Rounded standard constant (INCIDENTS.md 2026-08-23, D17): `unit_1U = 44.5`
   instead of EIA-310's exact 44.45 -- 0.05 mm of error per U in every
   module. Rule: a variable whose NAME says which standard it is must hold
   the exact value; a value within 2 % of it but not equal is a rounding.

Comments and string literals are blanked before matching.

Usage:
    python3 check_scad_lint.py --project-dir . [--scad lone.scad ...]

Scans params.scad, layout.scad, assembly.scad, parts/*.scad and every --scad.

Exit codes:
    0  pass
    3  fail -- at least one finding
    4  usage error
"""
import argparse
import glob
import os
import re
import sys

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4

NUM_RE = re.compile(r"^-?(\d+\.?\d*|\.\d+)$")
MODULE_RE = re.compile(r"\bmodule\s+([A-Za-z_]\w*)\s*\(")
ASSIGN_RE = re.compile(r"(?<![\w.$])([A-Za-z_]\w*)\s*=\s*(-?(?:\d+\.?\d*|\.\d+))\s*;")

# (exact value, standard, name regex). Name-gated: `wall = 44.5` is fine.
STANDARDS = [
    (44.45, "EIA-310 1U", re.compile(r"(^|_)(1u|u1|unit_?1u|1u_?unit|rack_?u(nit)?|u_?height|ru)($|_)", re.I)),
    (25.4, "inch", re.compile(r"(^|_)(inch(es)?|in_?mm|mm_?per_?in)($|_)", re.I)),
    (482.6, "19-inch panel width", re.compile(r"(^|_)(19_?in(ch)?|panel_?w(idth)?|rack_?w(idth)?)($|_)", re.I)),
    (15.875, "EIA-310 hole pitch", re.compile(r"(eia|rail|hole).*(pitch|spacing)|(pitch|spacing).*(eia|rail|hole)", re.I)),
]
TOLERANCE = 0.02


def blank_comments_and_strings(src):
    """Same length, newlines kept, so offsets still map to line numbers."""
    out, i, n = [], 0, len(src)
    while i < n:
        c, nxt = src[i], src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j])); i = j
        elif c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append('"' + " " * (j - i - 2) + '"' if j - i >= 2 else src[i:j]); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def balanced(src, open_idx):
    """Text inside the parens starting at src[open_idx] == '('."""
    depth = 0
    for j in range(open_idx, len(src)):
        if src[j] in "([{":
            depth += 1
        elif src[j] in ")]}":
            depth -= 1
            if depth == 0:
                return src[open_idx + 1:j]
    return src[open_idx + 1:]


def split_top(args):
    parts, depth, cur = [], 0, []
    for ch in args:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def kwargs(args):
    out = {}
    for p in split_top(args):
        m = re.match(r"^([A-Za-z_]\w*)\s*=(?!=)\s*(.+)$", p, re.S)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def line_of(src, idx):
    return src.count("\n", 0, idx) + 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--scad", action="append", default=[])
    a = ap.parse_args()
    if not os.path.isdir(a.project_dir):
        print(f"ERROR: not a directory: {a.project_dir}", file=sys.stderr)
        return EXIT_USAGE

    d = a.project_dir
    paths = [os.path.join(d, f) for f in ("params.scad", "layout.scad", "assembly.scad")]
    paths += sorted(glob.glob(os.path.join(d, "parts", "*.scad"))) + a.scad
    files = {}
    for p in dict.fromkeys(paths):
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="replace") as f:
                files[os.path.relpath(p, d) if not os.path.relpath(p, d).startswith("..") else p] = blank_comments_and_strings(f.read())

    findings = []

    # 1. numeric defaults vs computed callers
    defaults = {}  # module -> {arg: (literal, file, line)}
    for rel, src in files.items():
        for m in MODULE_RE.finditer(src):
            for arg, val in kwargs(balanced(src, m.end() - 1)).items():
                # 0 is the usual "feature off" sentinel (chamfer = 0, bore = 0) and +/-1 a sign
                # (nas_post side = 1, server_rack v4), not a dimension.
                if NUM_RE.match(val) and abs(float(val)) not in (0, 1):
                    defaults.setdefault(m.group(1), {})[arg] = (val, rel, line_of(src, m.start()))
    for mod, args in defaults.items():
        call_re = re.compile(r"(?<![\w.])" + re.escape(mod) + r"\s*\(")
        computed, omitted = {}, {}  # arg -> first (file, line, expr)
        for rel, src in files.items():
            for m in call_re.finditer(src):
                if re.search(r"\bmodule\s+$", src[max(0, m.start() - 20):m.start()]):
                    continue
                inner = balanced(src, m.end() - 1)
                kw, npos = kwargs(inner), len([p for p in split_top(inner) if not re.match(r"^[A-Za-z_]\w*\s*=(?!=)", p)])
                where = (rel, line_of(src, m.start()))
                for arg in args:
                    if arg in kw:
                        if not NUM_RE.match(kw[arg]):
                            computed.setdefault(arg, where + (" ".join(kw[arg].split()),))
                    elif npos == 0:
                        omitted.setdefault(arg, where)
        for arg in args:
            if arg in computed and arg in omitted:
                lit, drel, dline = args[arg]
                (crel, cline, expr), (orel, oline) = computed[arg], omitted[arg]
                findings.append(
                    f"{drel}:{dline}: module {mod}({arg} = {lit}): {crel}:{cline} computes {arg} "
                    f"({arg} = {expr}) but {orel}:{oline} omits it and silently gets {lit}. "
                    f"Make it `{arg} = undef` with assert(!is_undef({arg})) and pass it everywhere.")
    # shortcut: a call with any positional argument is not counted as omitting (positions are
    # not mapped to names); upgrade if an incident shows one.

    # 2. rounded standard constants
    for rel, src in files.items():
        for m in ASSIGN_RE.finditer(src):
            name, val = m.group(1), float(m.group(2))
            for exact, std, name_re in STANDARDS:
                if name_re.search(name) and val != exact and abs(val - exact) <= TOLERANCE * exact:
                    findings.append(
                        f"{rel}:{line_of(src, m.start(1))}: {name} = {m.group(2)} looks like a rounded "
                        f"{std}; the exact value is {exact:g}. Rounding a standard spreads its error "
                        f"into every part that uses it.")

    if findings:
        for f in findings:
            print("FAIL: " + f)
        print(f"scad_lint: {len(findings)} finding(s) in {len(files)} file(s)")
        return EXIT_FAIL
    print(f"PASS: scad_lint, {len(files)} file(s), no computed-default or rounded-standard findings")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
