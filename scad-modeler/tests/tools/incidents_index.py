#!/usr/bin/env python3
"""incidents_index.py -- regenerate the `## Index` at the top of INCIDENTS.md.

Usage:
    incidents_index.py check   <INCIDENTS.md>   # verify every line number
    incidents_index.py rebuild <INCIDENTS.md>   # rewrite the index

Why this exists. INCIDENTS.md is append-only and grew to ~1 500 lines; SKILL.md
tells the model to read it before writing geometry, which made every design pay
~20k tokens to find three relevant entries. The index costs ~130 lines instead.

An index whose line numbers drift is worse than no index -- it sends the reader
to the wrong entry and looks authoritative while doing it. So the numbers are
MEASURED against the written file, never computed from an offset, and `check`
exists to catch drift after an append.
"""
import re
import sys

HEAD = [
    "## Index",
    "",
    "Every incident here is real and was fixed. **Read the entry you need, not the",
    "file.** This list is ~130 lines; the file is 1 500. `grep -n <term> INCIDENTS.md`",
    "works too. Numbers point at each entry's `###` heading.",
    "",
]

ENTRY = re.compile(r"^### (20[0-9]{2}-[0-9]{2}-[0-9]{2}) -- (.*)")


def split(lines):
    """-> (preamble, rest) with the index stripped out."""
    first = next((i for i, l in enumerate(lines) if ENTRY.match(l)), None)
    if first is None:
        raise SystemExit("no entries found")
    # Strip the WHOLE block, not the lines that look like index rows. An earlier
    # version filtered on "- " and "[L" and removed only the entry lines, leaving
    # the date headings and prose behind -- so each rebuild grew the file by ~28
    # lines. `check` cannot see it: the numbers it verifies were still correct.
    start = next((i for i, l in enumerate(lines) if l.rstrip() == "## Index"), None)
    if start is not None and start < first:
        return lines[:start], lines[first:]
    return lines[:first], lines[first:]


def entries(rest):
    by_date = {}
    for line in rest:
        m = ENTRY.match(line)
        if m:
            by_date.setdefault(m.group(1), []).append(m.group(2).strip())
    return by_date


def check(path):
    lines = open(path, encoding="utf-8").read().split(chr(10))
    headings = {}
    for i, line in enumerate(lines, 1):
        m = ENTRY.match(line)
        if m:
            headings.setdefault(m.group(2).strip()[:60], i)
    total = wrong = 0
    for line in lines:
        m = re.search(r"\[L(\d+)\]", line)
        if not m:
            continue
        total += 1
        n = int(m.group(1))
        if not (0 < n <= len(lines)) or not ENTRY.match(lines[n - 1]):
            wrong += 1
            print("  L%d does not point at an entry heading" % n, file=sys.stderr)
    missing = len(headings) - total
    print("index links: %d, pointing at a heading: %d, wrong: %d" % (total, total - wrong, wrong))
    if missing:
        print("entries with no index line: %d" % missing, file=sys.stderr)
    return 1 if (wrong or missing) else 0


def rebuild(path):
    lines = open(path, encoding="utf-8").read().split(chr(10))
    preamble, rest = split(lines)
    by_date = entries(rest)

    idx = []
    for d in sorted(by_date, reverse=True):
        idx.append("**%s** (%d)" % (d, len(by_date[d])))
        for title in by_date[d]:
            s = title.replace("|", "/")
            if len(s) > 96:
                s = s[:93] + "..."
            idx.append("- %s  @@%s@@" % (s, title[:60]))
        idx.append("")

    open(path, "w", encoding="utf-8").write(chr(10).join(preamble + HEAD + idx + rest))

    # measure against the file as written -- never trust an offset
    done = open(path, encoding="utf-8").read().split(chr(10))
    pos = {}
    for i, line in enumerate(done, 1):
        m = ENTRY.match(line)
        if m:
            pos.setdefault(m.group(2).strip()[:60], i)

    out, hit, miss = [], 0, 0
    for line in done:
        m = re.search(r"@@(.*)@@$", line)
        if not m:
            out.append(line)
            continue
        key = m.group(1)
        if key in pos:
            out.append(re.sub(r"@@.*@@$", "[L%d]" % pos[key], line))
            hit += 1
        else:
            out.append(re.sub(r"@@.*@@$", "[L?]", line))
            miss += 1

    open(path, "w", encoding="utf-8").write(chr(10).join(out))
    print("entries: %d, linked: %d, unlinked: %d" % (sum(len(v) for v in by_date.values()), hit, miss))
    return 1 if miss else 0


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("check", "rebuild"):
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)
    sys.exit(check(sys.argv[2]) if sys.argv[1] == "check" else rebuild(sys.argv[2]))