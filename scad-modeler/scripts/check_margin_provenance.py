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

    if not asserts:
        print("OK: no assert() in params.scad -- nothing to check.")
        return 0
    if not cvars:
        print("OK: no clearance-suffixed variable (_clearance/_fit/_bias/_offset/_backlash) "
              "declared in params.scad -- nothing to cross-check.")
        return 0

    failures = []
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

    if failures:
        print("FAIL: possible margin-provenance gap(s) -- an assert() may not account for a "
              "clearance term the real geometry applies:")
        for f in failures:
            print(f"  - {f}")
        return 3

    print(f"OK: {len(asserts)} assert(s) checked against {len(cvars)} clearance variable(s) "
          f"in {args.parts_dir}/ -- no unaccounted-for clearance term found.")
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
