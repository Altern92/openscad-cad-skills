#!/usr/bin/env python3
"""ab_analyze.py -- count what two runs of validate_scad.sh disagree about.

Usage: ab_analyze.py <out_dir>      (the directory ab_tooling.sh wrote)

Four questions, in this order:
  1. how many CHECK_RESULT lines each version reports, per project
  2. how many projects carry a COVERAGE line at all
  3. every check whose verdict DIFFERS between the two
  4. checks the older version never mentions -- the silence count

The last one is the point. A check that emits nothing is indistinguishable from
one that passed, from one that failed, and from one that does not exist.
Measured on 11 projects 2026-09-12: the older version was silent on 10 of 18
checks in EVERY project. See README.md in this directory.
"""
import collections
import os
import re
import sys


def parse(path):
    """-> (checks dict, has_coverage bool), or None if the log is missing."""
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    checks = dict(re.findall(r"^CHECK_RESULT ([a-z_]+)=(\w+)", text, re.M))
    return checks, re.search(r"^COVERAGE:", text, re.M) is not None


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = sys.argv[1]
    with open(os.path.join(out, "projects.txt")) as fh:
        projects = [line.strip() for line in fh if line.strip()]
    if not projects:
        print("projects.txt is empty", file=sys.stderr)
        return 1

    rows = []
    for p in projects:
        slug = p.lstrip("./").replace("/", "_")
        post = parse(os.path.join(out, "post", slug + ".log"))
        pre = parse(os.path.join(out, "pre", slug + ".log"))
        rows.append((p, pre, post))

    has_pre = any(r[1] for r in rows)
    n = len(rows)

    print("=== 1. checks reported ===")
    print("%-44s %6s %6s %8s" % ("project", "PRE", "POST", "delta"))
    tp = tq = 0
    for p, pre, post in rows:
        if post is None:
            print("%-44s  no POST log" % p[-44:])
            continue
        a = len(pre[0]) if pre else 0
        b = len(post[0])
        tp += a
        tq += b
        print("%-44s %6s %6d %+8d" % (p[-44:], a if pre else "-", b, (b - a) if pre else 0))
    print("%-44s %6d %6d %+8d" % ("TOTAL", tp, tq, tq - tp))

    print()
    print("=== 2. COVERAGE line present ===")
    cp = sum(1 for _, pre, _ in rows if pre and pre[1])
    cq = sum(1 for _, _, post in rows if post and post[1])
    if has_pre:
        print("  PRE:  %d / %d projects" % (cp, n))
    print("  POST: %d / %d projects" % (cq, n))

    if not has_pre:
        print()
        print("(no PRE logs -- pass an older scripts dir to ab_tooling.sh for the diff)")
        return 0

    print()
    print("=== 3. verdicts that differ ===")
    differ = 0
    for p, pre, post in rows:
        if pre is None or post is None:
            continue
        for k in sorted(set(pre[0]) | set(post[0])):
            va, vb = pre[0].get(k), post[0].get(k)
            if va != vb:
                differ += 1
                print("  %-38s %-20s PRE=%-12s POST=%s"
                      % (p[-38:], k, va or "(silent)", vb or "(silent)"))
    print("  total differing check verdicts: %d" % differ)

    print()
    print("=== 4. checks the PRE version never mentions ===")
    missing = collections.Counter()
    for _, pre, post in rows:
        if pre is None or post is None:
            continue
        for k in post[0]:
            if k not in pre[0]:
                missing[k] += 1
    if not missing:
        print("  none")
    for k, v in missing.most_common():
        print("  %-24s silent on PRE in %d / %d projects" % (k, v, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
