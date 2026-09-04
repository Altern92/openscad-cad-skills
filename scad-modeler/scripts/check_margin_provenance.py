#!/usr/bin/env python3
"""Margin-provenance guard (2026-08-19 Phase-2 pattern analysis, Pattern 1;
implemented 2026-08-22, see INCIDENTS.md). Catches a safety-margin assert()
in params.scad that omits a clearance term the real geometry applies
separately -- the assert reports a "safe" margin computed from nominal
dimensions while the actual, clearance-inflated geometry is tighter.

Real incident this targets (INCIDENTS.md, 2026-08-18,
jackshaft_bearing_wall_at_diff): an assert computed a wall thickness from
nominal pitch/OD dimensions only (`CD2 - diff_ring_outer_r -
jackshaft_bearing_od/2` > 1.0, reporting a "safe" ~1.6mm margin). The real
geometry-cutting code (`diff_cavity()`, `jackshaft_bearing_pockets()`)
separately added `gear_spin_clearance` (0.4mm) and `bearing_press_fit`
(0.05mm) to the cavity radii the assert's own dependencies feed into --
terms the assert's formula never included. Recomputing with both terms
gave ~1.2mm, matching a code comment that had already noticed the drift by
hand. The assert's "safe" verdict did not match the geometry it was meant
to guard.

Mechanism (deliberately lightweight, no full parser -- same tokenizer
approach check_dependencies.py already uses for its own DAG): a params.scad
variable whose name ends in a clearance-like suffix (_clearance, _fit,
_bias, _offset, _backlash) is a CLEARANCE_VAR. For each assert() in
params.scad, compute the transitive set of params.scad variables its
checked condition depends on (walking `name = expr;` references backward).
Separately scan parts/*.scad for any CLEARANCE_VAR added/subtracted
directly next to an identifier that IS one of the assert's own
dependencies -- i.e., geometry applying a clearance term to a value the
assert's formula is built from. If that CLEARANCE_VAR's name never appears
anywhere in the assert's own transitive dependency set, flag it: the
geometry inflates a value the assert depends on, using a term the assert
itself never accounts for.

Heuristic, not exact -- a textual adjacency match, not real data-flow
analysis. A false positive (an unrelated same-named coincidence) is
possible; escalate to a human/agent reading the assert against the
geometry when this fires, don't just silence it. Opt out a specific,
confirmed-fine case with a `// MARGIN_EXCLUDES_OK: <clearance_var>`
comment on the assert's own line or the line directly above it (mirrors
the `// EXPECTED_BODIES: N` opt-out convention elsewhere in this skill).

SECOND DETECTION MODE (added 2026-09-04): wrong-variable-family. Real
incident this targets (INCIDENTS.md, 2026-09-02, nas_deck_v3): a local
variable `_deck_socket_depth` was introduced to hold a reduced, deck-
specific socket depth, but the assert meant to guard it kept referencing
the older, global `_socket_depth` (`post_socket_depth`) instead -- a
same-family name (both about "socket depth"), but not the same value.
The geometry-cutting code used `_deck_socket_depth`; the assert checked
`_socket_depth`; the "passing" assert proved nothing about the value
actually cut. Unlike the omitted-clearance-term check above (cross-file,
params.scad vs parts/*.scad), this is intra-file: for every locally-
assigned, dimensional-sounding variable (`_depth`/`_thickness`/
`_clearance`/`_fit`/`_bias`/`_offset`/`_backlash`/`_gap`/`_pitch`/
`_margin`/`_wall`-suffixed) that's actually consumed inside a geometry-
producing call (`cylinder`/`cube`/`sphere`/`translate`/`linear_extrude`/
etc.) in a file, checks whether that EXACT variable has an assert() of
its own in that file. If not, but a "family sibling" -- another variable
whose name shares the same core after stripping one leading qualifier
segment (`post_socket_depth` and `_deck_socket_depth` both normalize to
`socket_depth`) -- DOES have an assert, that's flagged: the assert may be
checking the wrong one. Runs across `--scad` and every file under
`--parts-dir`, independently per file (the bug is local to one file's own
variable shadowing, not a cross-file relationship). Same
`// MARGIN_EXCLUDES_OK: <var>` opt-out applies, checked per-file.

Usage:
    python3 check_margin_provenance.py --scad params.scad --parts-dir parts/

Exit codes:
    0  pass (or nothing to check -- no params.scad asserts, or no parts-dir)
    3  fail -- at least one assert appears to omit a clearance term
    4  usage error
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_dependencies import parse_assignments, IDENT_RE  # noqa: E402

CLEARANCE_SUFFIXES = ("_clearance", "_fit", "_bias", "_offset", "_backlash")


def find_asserts(text):
    """Return [(condition_text, line_no)] for every assert(...) in text,
    handling nested parens (e.g. assert(f(x) > 0, ...)) by counting depth
    rather than matching to the first ')'."""
    out = []
    for m in re.finditer(r"assert\s*\(", text):
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
            i += 1
        content = text[start:i - 1]
        condition, _ = split_top_level(content)
        line = text.count("\n", 0, m.start()) + 1
        out.append((condition, line))
    return out


def split_top_level(s, sep=","):
    """Split s at the first sep that is not nested inside (), [], or a
    string literal -- used to separate assert()'s condition from its
    message argument without a real parser."""
    depth = 0
    in_str = None
    for i, ch in enumerate(s):
        if in_str:
            if ch == in_str and s[i - 1] != "\\":
                in_str = None
            continue
        if ch in "\"'":
            in_str = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == sep and depth == 0:
            return s[:i], s[i + 1:]
    return s, None


def transitive_deps(names, assignments):
    """Every params.scad variable (transitively) referenced by expanding
    each starting name's own defining expression -- "what does this
    formula ultimately depend on", not "what depends on this"."""
    seen = set()
    stack = list(names)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        if n in assignments:
            expr, _ = assignments[n]
            for tok in IDENT_RE.findall(expr):
                if tok in assignments and tok not in seen:
                    stack.append(tok)
    return seen


def clearance_vars(assignments):
    return {n for n in assignments if n.endswith(CLEARANCE_SUFFIXES)}


def find_opt_outs(scad_path):
    """// MARGIN_EXCLUDES_OK: var1, var2 anywhere in params.scad -- global
    to the file rather than per-assert, since params.scad asserts here are
    typically few and this stays simple; tighten to per-line proximity if
    that ever proves too coarse in practice."""
    try:
        text = open(scad_path, encoding="utf-8").read()
    except OSError:
        return set()
    out = set()
    for m in re.finditer(r"//\s*MARGIN_EXCLUDES_OK:\s*(.+)", text):
        out.update(v.strip() for v in m.group(1).split(",") if v.strip())
    return out


def find_clearance_applications(parts_dir, dep_var, clearance_var):
    """True if dep_var and clearance_var appear directly combined via +/-
    (either order) anywhere under parts_dir -- the textual signature of
    geometry applying a clearance term to a value an assert depends on."""
    if not parts_dir or not os.path.isdir(parts_dir):
        return []
    pat = re.compile(
        r"\b" + re.escape(dep_var) + r"\b\s*[+\-]\s*\b" + re.escape(clearance_var) + r"\b"
        r"|\b" + re.escape(clearance_var) + r"\b\s*[+\-]\s*\b" + re.escape(dep_var) + r"\b"
    )
    hits = []
    for fn in sorted(os.listdir(parts_dir)):
        if not fn.endswith(".scad"):
            continue
        p = os.path.join(parts_dir, fn)
        try:
            text = open(p, encoding="utf-8").read()
        except OSError:
            continue
        if pat.search(text):
            hits.append(fn)
    return hits


GEOMETRY_PRIMITIVES = (
    "cylinder", "cube", "sphere", "polyhedron", "polygon", "linear_extrude",
    "rotate_extrude", "translate", "rotate", "scale", "offset", "hull",
)

DIMENSIONAL_SUFFIXES = (
    "_depth", "_thickness", "_clearance", "_fit", "_bias", "_offset",
    "_backlash", "_gap", "_pitch", "_margin", "_wall",
)


def find_call_args(text, keyword):
    """Return [(args_text, line_no)] for every call to keyword(...) in
    text, handling nested parens the same way find_asserts() does."""
    out = []
    for m in re.finditer(r"\b" + re.escape(keyword) + r"\s*\(", text):
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
            i += 1
        out.append((text[start:i - 1], text.count("\n", 0, m.start()) + 1))
    return out


def geometry_variable_uses(text, assignments):
    """Names from assignments that appear as an argument inside any
    geometry-producing primitive call in text."""
    used = set()
    for kw in GEOMETRY_PRIMITIVES:
        for args_text, _line in find_call_args(text, kw):
            for tok in IDENT_RE.findall(args_text):
                if tok in assignments:
                    used.add(tok)
    return used


def variable_family(name):
    """Normalize a variable name to its 'family core' -- strip a leading
    underscore and the first underscore-separated qualifier segment, so
    'post_socket_depth' and '_deck_socket_depth' both normalize to
    'socket_depth'. Heuristic: a two-segment name has no qualifier to
    strip past its own core and normalizes to itself (lstrip'd)."""
    n = name.lstrip("_")
    parts = n.split("_")
    if len(parts) >= 3:
        return "_".join(parts[1:])
    return n


def find_direct_assert_vars(text):
    """Every variable name referenced by any assert()'s condition in text."""
    names = set()
    for condition, _line in find_asserts(text):
        names.update(IDENT_RE.findall(condition))
    return names


def check_wrong_variable_family(path, assignments, opted_out):
    """See module docstring, "SECOND DETECTION MODE". Returns a list of
    human-readable failure strings for `path`."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return []
    geom_vars = geometry_variable_uses(text, assignments)
    dimensional = {v for v in geom_vars if v.endswith(DIMENSIONAL_SUFFIXES)}
    if not dimensional:
        return []
    asserted = find_direct_assert_vars(text)
    families = {}
    for v in assignments:
        families.setdefault(variable_family(v), []).append(v)

    failures = []
    for v in sorted(dimensional):
        if v in asserted or v in opted_out:
            continue
        siblings = sorted(s for s in families.get(variable_family(v), []) if s != v)
        asserted_siblings = [s for s in siblings if s in asserted]
        if asserted_siblings:
            failures.append(
                f"'{v}' (in {path}) is used in geometry but has no assert() of "
                f"its own; same-family sibling(s) {asserted_siblings} IS/ARE "
                f"asserted instead. Verify '{v}' doesn't also need its own "
                f"guard, or that the existing assert is actually meant to "
                f"constrain '{v}' too, not just {asserted_siblings} -- this is "
                f"exactly the shape of a refactor that introduced a new, more-"
                f"specific local variable without updating the assert meant to "
                f"guard it (INCIDENTS.md, 2026-09-02, nas_deck_v3)."
            )
    return failures


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scad", required=True, help="params.scad (or equivalent) to check")
    ap.add_argument("--parts-dir", default="parts", help="directory of part .scad files (default: parts)")
    args = ap.parse_args()

    if not os.path.isfile(args.scad):
        print(f"error: {args.scad} not found", file=sys.stderr)
        return 4

    text = open(args.scad, encoding="utf-8").read()
    assignments = parse_assignments(args.scad)
    asserts = find_asserts(text)
    cvars = clearance_vars(assignments)
    opted_out = find_opt_outs(args.scad)

    failures = []

    # --- Detection mode 1: omitted clearance term (cross-file) ---
    if asserts and cvars:
        for condition, line in asserts:
            direct = {tok for tok in IDENT_RE.findall(condition) if tok in assignments}
            if not direct:
                continue
            deps = transitive_deps(direct, assignments)
            for dep_var in sorted(deps):
                for cvar in sorted(cvars):
                    if cvar in deps or cvar in opted_out:
                        continue
                    hits = find_clearance_applications(args.parts_dir, dep_var, cvar)
                    if hits:
                        failures.append(
                            f"assert() at {args.scad}:{line} depends on '{dep_var}', but "
                            f"{', '.join(hits)} applies '{cvar}' directly to '{dep_var}' in "
                            f"geometry -- the assert's own formula never references '{cvar}'. "
                            f"Verify the assert's margin still holds once '{cvar}' is included, "
                            f"or add '// MARGIN_EXCLUDES_OK: {cvar}' if it genuinely doesn't apply here."
                        )

    # --- Detection mode 2: wrong-variable-family (intra-file, every file) ---
    scan_files = [args.scad]
    if args.parts_dir and os.path.isdir(args.parts_dir):
        scan_files += [os.path.join(args.parts_dir, fn)
                        for fn in sorted(os.listdir(args.parts_dir)) if fn.endswith(".scad")]
    for f in scan_files:
        f_assignments = assignments if f == args.scad else parse_assignments(f)
        f_opted_out = opted_out if f == args.scad else find_opt_outs(f)
        failures.extend(check_wrong_variable_family(f, f_assignments, f_opted_out))

    if failures:
        print("FAIL: possible margin-provenance gap(s):")
        for f in failures:
            print(f"  - {f}")
        return 3

    print(f"OK: {len(asserts)} assert(s) in {args.scad} checked against {len(cvars)} "
          f"clearance variable(s); {len(scan_files)} file(s) checked for wrong-variable-"
          f"family gaps -- nothing found.")
    return 0


if __name__ == "__main__":
    _exit = main()
    try:
        from validation_log import log_run
        _label = {0: "OK", 3: "FAIL", 4: "USAGE_ERROR"}.get(_exit, f"exit={_exit}")
        log_run("margin_provenance", _exit, "check_margin_provenance.py " + " ".join(sys.argv[1:]), _label)
    except Exception:
        pass
    sys.exit(_exit)
