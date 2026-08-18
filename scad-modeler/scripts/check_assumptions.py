#!/usr/bin/env python3
"""Fail validation if a CRITICAL design assumption is still unverified.

Why this exists
----------------
Perplexity research (2026-08-19), triangulating multiple independent
failure-analysis studies, found "wrong or unverified initial design
assumptions" to be the single most evidence-backed root cause of real
mechanical failures -- not geometric interference, which is what every
other check in this skill catches. A 284-case chemical-process accident
study found ~79% involved a design error; a nuclear-industry dataset found
design error outranked component failure as a root cause (35% vs 18%).
Every OTHER check in this toolchain (dimensions, features, collisions,
connectivity, motion) validates that the geometry is CONSISTENT WITH the
calculation table -- none of them can tell you the calculation table's own
starting assumptions were correct in the first place. This is the one gate
aimed at that different, higher-priority failure class.

WHAT IT CHECKS
---------------
Parses the decisions/assumptions log (references/planning.md §1's format --
a Markdown table with ID/Type/Criticality/Statement/Status/Evidence columns)
out of a calculations.md (or any Markdown file). Any row marked
`Criticality: Critical` whose `Status` is not one of Confirmed/Verified/
Resolved/Closed fails the check. Rows without a Criticality column, or a
file with no such table at all, are silently skipped (exit 0) -- this is
opt-in by existence, same as EXPECTED_BBOX/EXPECTED_HOLE: it only gates
projects that have adopted the planning.md log format, so it doesn't break
every pre-existing project that hasn't.

Requires: nothing beyond the standard library -- this only parses Markdown
tables, no mesh/geometry involved.

Usage:
    python3 check_assumptions.py --calc calculations.md

Exit codes:
    0  pass (no table found, or every Critical row is resolved)
    1  at least one Critical row is still unresolved
    4  usage error (file not found)
"""
import argparse
import os
import re
import sys

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 4

RESOLVED_STATUSES = {"confirmed", "verified", "resolved", "closed"}

# A Markdown table row: | a | b | c | ... | -- split on unescaped pipes.
ROW_RE = re.compile(r'^\s*\|(.+)\|\s*$')
SEPARATOR_RE = re.compile(r'^[\s|:\-]+$')


def find_table(lines):
    """Locate the header row for the ID/Type/Criticality/.../Status/...
    table and return (header_cells_lowercased, data_row_indices)."""
    for i, line in enumerate(lines):
        m = ROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        lower = [c.lower() for c in cells]
        if "criticality" in lower and "status" in lower:
            # Next line should be the Markdown table separator (---|---|...).
            if i + 1 < len(lines) and SEPARATOR_RE.match(lines[i + 1].strip()):
                return lower, i + 2
    return None, None


def parse_rows(lines, header, start):
    idx = {name: header.index(name) for name in
           ("id", "type", "criticality", "statement", "status") if name in header}
    rows = []
    for line in lines[start:]:
        m = ROW_RE.match(line)
        if not m:
            break  # table ended
        cells = [c.strip() for c in m.group(1).split("|")]
        if len(cells) < len(header):
            continue
        row = {name: cells[i] for name, i in idx.items()}
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calc", required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.calc):
        print(f"ERROR: file not found: {args.calc}", file=sys.stderr)
        return EXIT_USAGE

    with open(args.calc, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header, start = find_table(lines)
    if header is None:
        print(f"WARNING: no decisions/assumptions log table (with a "
              f"Criticality column) found in {args.calc}; skipping.")
        return EXIT_OK

    rows = parse_rows(lines, header, start)
    unresolved = [
        r for r in rows
        if r.get("criticality", "").lower() == "critical"
        and r.get("status", "").lower() not in RESOLVED_STATUSES
    ]

    if unresolved:
        print(f"FAIL: {len(unresolved)} CRITICAL assumption(s)/risk(s) still "
              f"unresolved in {os.path.basename(args.calc)}:")
        for r in unresolved:
            rid = r.get("id", "?")
            statement = r.get("statement", "")
            status = r.get("status", "")
            print(f"  - {rid}: \"{statement}\" -- status: {status}")
        print("  -> these feed load-bearing/fit-critical calculations and "
              "must be confirmed (datasheet/measurement/test/literature), "
              "not just left as a guess, before this design is finalized.")
        return EXIT_MISMATCH

    n_critical = sum(1 for r in rows if r.get("criticality", "").lower() == "critical")
    print(f"OK: {n_critical} critical item(s) in the log, all resolved "
          f"({len(rows)} rows total).")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
