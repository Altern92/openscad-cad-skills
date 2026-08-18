#!/usr/bin/env python3
"""Check that a service-envelope declaration exists and every field is filled in.

Why this exists
----------------
"Service-environment load mismatch" (vibration, thermal cycling, wear,
duty cycle) is, per real failure-analysis literature, one of the two
most evidence-backed root causes of real mechanical failures (alongside
unverified design assumptions -- see check_assumptions.py) -- and nothing
else in this validation chain touches it, because it isn't a geometry
question. This script can't verify the declared conditions are CORRECT,
only that they were forced to be stated instead of silently never
considered. See templates/service_envelope.md for the field set (adapted
from NASA's "life-cycle environment profile").

Opt-in by existence, same as EXPECTED_BBOX/check_assumptions.py: a project
that hasn't created a service_envelope.md is skipped (exit 0), not failed --
this only gates projects that opted into declaring one.

Requires: nothing beyond the standard library.

Usage:
    python3 check_service_envelope.py --envelope service_envelope.md

Exit codes:
    0  pass (file doesn't exist -- not opted in -- or every field is filled)
    1  file exists but has a blank field
    4  usage error
"""
import argparse
import os
import re
import sys

EXIT_OK = 0
EXIT_MISMATCH = 1
EXIT_USAGE = 4

ROW_RE = re.compile(r'^\s*\|(.+)\|\s*$')
SEPARATOR_RE = re.compile(r'^[\s|:\-]+$')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--envelope", required=True)
    args = parser.parse_args()

    if not os.path.isfile(args.envelope):
        print(f"WARNING: no {os.path.basename(args.envelope)} found; "
              f"skipping (not opted in). See templates/service_envelope.md "
              f"if this assembly bears real load/vibration/thermal service.")
        return EXIT_OK

    with open(args.envelope, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the "| Field | Value |" header, skip the separator, read rows.
    rows = []
    in_table = False
    for line in lines:
        m = ROW_RE.match(line)
        if not m:
            in_table = False
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if SEPARATOR_RE.match(line.strip()):
            continue
        if not in_table:
            if len(cells) >= 2 and cells[0].lower() == "field" and cells[1].lower() == "value":
                in_table = True
            continue
        rows.append(cells)

    if not rows:
        print(f"ERROR: {args.envelope} exists but no '| Field | Value |' "
              f"table found in it.", file=sys.stderr)
        return EXIT_USAGE

    blank = [r[0] for r in rows if len(r) < 2 or not r[1].strip()]
    if blank:
        print(f"FAIL: {os.path.basename(args.envelope)} has {len(blank)} "
              f"blank field(s):")
        for field in blank:
            print(f"  - {field}")
        print("  -> fill in a real value, or 'TBD' if genuinely unknown -- "
              "never leave it blank.")
        return EXIT_MISMATCH

    print(f"OK: {os.path.basename(args.envelope)} -- all {len(rows)} fields declared.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
