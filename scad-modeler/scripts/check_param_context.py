#!/usr/bin/env python3
"""Parameter context manifest guard (2026-08-19 Phase-2 pattern analysis,
Pattern 3; implemented 2026-08-22, see INCIDENTS.md). Catches a shared
params.scad value that's consumed for a hardware-fit purpose in more than
one context, where only ONE context's constraint was ever actually
verified by an assert().

Real incident this targets (INCIDENTS.md, 2026-08-18, axle_d): a single
`axle_d = 6` fed both the diff-side output stub (photo-measured, ~6mm OK)
and the wheel_hub end (which seats an MR105 bearing, fixed 5mm ID -- a
uniform 6mm shaft cannot pass through a 5mm-ID bearing). Nothing checked
the wheel-hub context; only the diff-side context had ever actually been
verified, and the incompatibility went unnoticed until someone traced
both ends of the same half-shaft by hand.

Mechanism: a project opts in by declaring, in any .scad file (typically
right where a shared parameter is consumed for a hardware-fit purpose):

    use_param("axle_d", "diff_stub_end", "photo_measured_~6mm");
    use_param("axle_d", "wheel_hub_bearing_end", "press_fit_MR105_bore5mm");

`use_param(name, context, constraint)` is a no-op module at render time
(defined once in params.scad -- see SKILL.md) -- purely a static-analysis
marker for this script. For every parameter name declared via use_param()
in TWO OR MORE DISTINCT (file, context) pairs -- i.e. genuinely shared
across contexts, the only case with any cross-context risk -- this script
checks that the SAME FILE also contains at least one assert() that
textually references that parameter name. A context declared in a file
with no matching assert() in that file is flagged: the constraint was
named but never actually exercised where it was declared.

Heuristic, not exact -- "an assert() referencing the name exists in this
file" does not prove the assert enforces THIS SPECIFIC constraint (it
could theoretically be an unrelated assert that happens to mention the
same variable). Escalate to a human/agent read when this fires; a clean
run is not a proof of correctness, only "no undeclared-verification gap
was found by this heuristic."

Usage:
    python3 check_param_context.py --project-dir .

Exit codes:
    0  pass (no use_param() calls found, or every ≥2-context parameter has
       a matching assert() in each declaring file)
    3  fail -- at least one context's constraint has no matching assert()
    4  usage error
"""
import argparse
import os
import re
import sys

USE_PARAM_RE = re.compile(
    r'use_param\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)')
IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")


def find_scad_files(project_dir):
    out = []
    for root, _dirs, files in os.walk(project_dir):
        for fn in files:
            if fn.endswith(".scad"):
                out.append(os.path.join(root, fn))
    return sorted(out)


def find_use_param_calls(path):
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return []
    return [(name, context, constraint) for name, context, constraint
            in USE_PARAM_RE.findall(text)]


def file_asserts_on(path, name):
    """True if path contains an assert(...) whose condition references
    name as a whole identifier -- balanced-paren extraction so a nested
    call like assert(f(name) > 0, ...) is still matched correctly."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return False
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
        if name in IDENT_RE.findall(content):
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", default=".", help="project root to scan (default: .)")
    args = ap.parse_args()

    if not os.path.isdir(args.project_dir):
        print(f"error: {args.project_dir} is not a directory", file=sys.stderr)
        return 4

    files = find_scad_files(args.project_dir)
    # (name, context, constraint, file) for every use_param() call found.
    entries = []
    for f in files:
        for name, context, constraint in find_use_param_calls(f):
            entries.append((name, context, constraint, f))

    if not entries:
        print("OK: no use_param() declarations found -- nothing to check "
              "(opt-in, see SKILL.md §2).")
        return 0

    by_name = {}
    for name, context, constraint, f in entries:
        by_name.setdefault(name, []).append((context, constraint, f))

    failures = []
    checked_names = 0
    for name, uses in sorted(by_name.items()):
        distinct_contexts = {(context, f) for context, _c, f in uses}
        if len(distinct_contexts) < 2:
            continue  # no cross-context risk with a single use
        checked_names += 1
        for context, constraint, f in uses:
            if not file_asserts_on(f, name):
                failures.append(
                    f"'{name}' context '{context}' ({constraint}) declared in "
                    f"{f}, but no assert() in {f} references '{name}' -- this "
                    f"context's constraint was named but never actually "
                    f"verified where it was declared.")

    if failures:
        print(f"FAIL: {len(failures)} parameter-context gap(s) found "
              f"(checked {checked_names} multi-context parameter(s)):")
        for msg in failures:
            print(f"  - {msg}")
        print("A shared parameter with multiple hardware-fit contexts needs "
              "each context's own assert() -- one verified context proves "
              "nothing about the others.")
        return 3

    print(f"OK: {len(entries)} use_param() declaration(s) across "
          f"{len(by_name)} parameter name(s), {checked_names} of them shared "
          f"across ≥2 contexts -- every context has a matching assert().")
    return 0


if __name__ == "__main__":
    _exit = main()
    try:
        from validation_log import log_run
        _label = {0: "OK", 3: "FAIL", 4: "USAGE_ERROR"}.get(_exit, f"exit={_exit}")
        log_run("param_context", _exit, "check_param_context.py " + " ".join(sys.argv[1:]), _label)
    except Exception:
        pass
    sys.exit(_exit)
