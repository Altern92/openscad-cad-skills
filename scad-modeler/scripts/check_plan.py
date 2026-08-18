#!/usr/bin/env python3
"""Enforce §0.5 Planning actually happened, not just that prose asked for it.

Why this exists
----------------
Every other check in this skill is a script, not a paragraph, for one
consistent reason: prose in SKILL.md is advice a model can skip under
pressure; a script that fails validate_scad.sh is a gate it can't. §0.5
("Planning") existed only as methodology (references/planning.md) with
nothing enforcing it was actually followed -- exactly the gap that let the
rear_axle incident happen in the first place (INCIDENTS.md, 2026-08-18):
architecture decided mid-calculation because nothing stopped work from
proceeding without it being settled first.

This script closes that gap by checking a project's plan.md
(templates/plan.md) for three concrete failure modes:

  1. Fewer than 2 architecture options listed, and no declared exemption --
     comparing one option against itself isn't a comparison, it's an
     assumption wearing a table.
  2. No `Decision` row with `Status: Confirmed` in the decisions log --
     the comparison happened but nothing was actually decided.
  3. A part named in layout.scad's LAYOUT that never appears in the plan's
     parts table -- a part invented later, during detailing, that skipped
     planning entirely. This is the most valuable check here: the other
     two catch a plan that's incomplete, this one catches a plan that was
     silently bypassed altogether for a specific part.

Requires: nothing beyond the standard library.

Usage:
    python3 check_plan.py --plan plan.md --layout layout.scad

Exit codes:
    0  pass (no plan.md -- not opted in -- or all three checks pass)
    1  at least one check failed
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
EXEMPT_RE = re.compile(r'<!--\s*PLAN_EXEMPT\s*:\s*(.*?)\s*-->')
SECTION_RE = re.compile(r'^\s*##\s+(.+?)\s*$')
LAYOUT_ENTRY_RE = re.compile(r'\[\s*"([^"]+)"\s*,')


def parse_sections(lines):
    """Split into {lowercased heading: [lines]} on '## Heading' boundaries."""
    sections = {}
    current = None
    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            current = m.group(1).lower()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def table_rows(section_lines):
    """Parse the first Markdown table in a section into a list of cell-lists,
    skipping the header and separator rows."""
    rows = []
    header_seen = False
    for line in section_lines:
        m = ROW_RE.match(line)
        if not m:
            if header_seen:
                break  # table ended
            continue
        if SEPARATOR_RE.match(line.strip()):
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if not header_seen:
            header_seen = True
            continue  # this is the header row itself
        if any(cells):
            rows.append(cells)
    return rows


def check_architecture_options(plan_text, sections):
    m = EXEMPT_RE.search(plan_text)
    if m:
        return None, f"exempt: {m.group(1)}"
    opts = table_rows(sections.get("architecture options", []))
    if len(opts) < 2:
        return ("fewer than 2 architecture options listed (found "
                f"{len(opts)}), and no <!-- PLAN_EXEMPT: ... --> declared -- "
                "comparing one option against itself isn't a comparison."), None
    return None, f"{len(opts)} options listed"


def check_decision(sections):
    rows = table_rows(sections.get("decision", []))
    for r in rows:
        # Columns: ID, Type, Criticality, Statement, Status, Evidence
        if len(r) >= 5 and r[1].lower() == "decision" and r[4].lower() in (
                "confirmed", "verified", "resolved"):
            return None
    return ("no 'Decision' row with Status: Confirmed found in the ## Decision "
            "table -- options were compared but nothing was actually chosen.")


def check_parts_coverage(sections, layout_path):
    if not layout_path or not os.path.isfile(layout_path):
        return None, "no layout.scad given/found -- skipped"
    with open(layout_path, "r", encoding="utf-8") as f:
        layout_text = f.read()
    layout_parts = set(LAYOUT_ENTRY_RE.findall(layout_text))
    if not layout_parts:
        return None, "layout.scad has no LAYOUT entries yet -- skipped"

    plan_rows = table_rows(sections.get("parts and dependency order", []))
    plan_parts = {r[0] for r in plan_rows if r}
    missing = sorted(layout_parts - plan_parts)
    if missing:
        return (f"layout.scad names part(s) not in the plan's parts table: "
                f"{', '.join(missing)} -- invented during detailing, skipped "
                "planning entirely."), None
    return None, f"{len(layout_parts)} layout part(s), all planned"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--layout", default=None)
    args = parser.parse_args()

    if not os.path.isfile(args.plan):
        print(f"WARNING: no {os.path.basename(args.plan)} found; skipping "
              f"(not opted in). See templates/plan.md if this assembly has "
              f"a genuinely uncertain architecture (SKILL.md §0.5).")
        return EXIT_OK

    with open(args.plan, "r", encoding="utf-8") as f:
        plan_text = f.read()
    lines = plan_text.splitlines()
    sections = parse_sections(lines)

    failures = []
    notes = []

    fail, note = check_architecture_options(plan_text, sections)
    (failures if fail else notes).append(fail or note)

    fail = check_decision(sections)
    if fail:
        failures.append(fail)
    else:
        notes.append("decision confirmed")

    fail, note = check_parts_coverage(sections, args.layout)
    (failures if fail else notes).append(fail or note)

    if failures:
        print(f"FAIL: {os.path.basename(args.plan)} is incomplete:")
        for f in failures:
            print(f"  - {f}")
        return EXIT_MISMATCH

    print(f"OK: {os.path.basename(args.plan)} -- " + "; ".join(notes) + ".")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
