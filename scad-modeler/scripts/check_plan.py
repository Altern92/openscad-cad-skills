#!/usr/bin/env python3
"""Gate detail work behind a completed design plan.

The failure this catches: an agent computes gear ratios and centre distances
before deciding what kind of mechanism it is building. The numbers come out
correct and worthless, because the architecture they rest on was never chosen --
it was assumed from whichever reading of the brief came first.

Prose in SKILL.md is advisory; a model may skip it. This makes the planning
gate checkable, which is the only kind of instruction that holds. It reads
`design/plan.md` (see templates/plan.md) and refuses to pass while:

  * fewer than two architecture options were compared -- one option is not a
    choice, it is an assumption wearing a table;
  * no decision line records which was chosen;
  * a blocking assumption is still unresolved;
  * a part in layout.scad never appeared in the dependency order, meaning it was
    invented during detail work and never planned.

That last check is the one worth having: it links the plan to the geometry
rather than letting the plan become a document nobody revisits.

Usage:
    python3 check_plan.py --plan design/plan.md
    python3 check_plan.py --plan design/plan.md --layout layout.scad

Exit codes:
    0  gate passed -- detail work may start
    1  plan incomplete or inconsistent (reasons printed)
    4  usage error (file missing/unreadable)
"""
import argparse
import os
import re
import sys

EXIT_OK, EXIT_INCOMPLETE, EXIT_USAGE = 0, 1, 4

SECTIONS = {
    1: "Task", 2: "Architecture options", 3: "Selection",
    4: "Dependency order", 5: "Assumptions and decisions",
}
PLACEHOLDER = re.compile(r"<[^>\n]{2,}>")


def split_sections(text):
    """Map section number -> its body, from '## <n>. <title>' headings."""
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\d)\.\s", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = int(m.group(1)), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def table_rows(body):
    """Data rows of the first markdown table in `body`, as cell lists."""
    rows, seen_header = [], False
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            if rows:
                break            # table ended
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(set(c) <= set("-: ") and c for c in cells):
            seen_header = True   # the |---|---| separator
            continue
        if not seen_header:
            continue             # header row
        if any(c for c in cells):
            rows.append(cells)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--layout", default=None,
                    help="layout.scad, to check every part was planned")
    args = ap.parse_args()

    if not os.path.isfile(args.plan):
        print(f"ERROR: plan not found: {args.plan}\n"
              f"Copy templates/plan.md to design/plan.md and fill it in before "
              f"starting geometry.", file=sys.stderr)
        return EXIT_USAGE
    try:
        text = open(args.plan, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: cannot read {args.plan}: {e}", file=sys.stderr)
        return EXIT_USAGE

    sec = split_sections(text)
    problems, notes = [], []

    for n, title in SECTIONS.items():
        if n not in sec or not sec[n].strip():
            problems.append(f"section {n} ({title}) is missing or empty")

    # 2 -- at least two genuinely stated architecture options.
    if 2 in sec:
        opts = [r for r in table_rows(sec[2])
                if len(r) >= 2 and r[1] and not PLACEHOLDER.search(r[1])]
        if len(opts) < 2:
            problems.append(
                f"section 2: {len(opts)} architecture option(s) filled in, need "
                f"at least 2 -- a single option is an assumption, not a choice")
        else:
            notes.append(f"{len(opts)} architecture options compared")

    # 3 -- a decision was actually recorded.
    if 3 in sec:
        m = re.search(r"\*\*Decision:\*\*\s*(.+)", sec[3])
        if not m or PLACEHOLDER.search(m.group(1)) or len(m.group(1).strip()) < 4:
            problems.append("section 3: no '**Decision:** ...' line recording "
                            "which architecture was chosen and why")
        else:
            notes.append(f"decision: {m.group(1).strip()[:70]}")
        if not re.search(r"\bunknown", sec[3], re.I):
            notes.append("section 3 has no unknowns criterion -- the matrix will "
                         "favour whichever option is least specified")

    # 4 -- a design order, and the parts it names.
    planned = set()
    if 4 in sec:
        m = re.search(r"\*\*Design order:\*\*\s*(.+)", sec[4])
        if not m or PLACEHOLDER.search(m.group(1)):
            problems.append("section 4: no '**Design order:** ...' line")
        else:
            planned = {p.strip().lower() for p in re.split(r"[,;]", m.group(1))
                       if p.strip()}
            notes.append(f"design order covers {len(planned)} part(s)")
        unchecked = [r[0] for r in table_rows(sec[4])
                     if len(r) >= 3 and "?" in r[2]]
        if unchecked:
            notes.append(f"unchecked dependencies ('?') on: {', '.join(unchecked)}"
                         f" -- resolve or accept explicitly")

    # 5 -- no blocking assumption left standing.
    if 5 in sec:
        blocking, open_items = [], 0
        for r in table_rows(sec[5]):
            if len(r) < 4:
                continue
            ident, kind, statement, status = r[0], r[1].lower(), r[2], r[3].lower()
            if PLACEHOLDER.search(statement):
                continue
            if "blocking" in status:
                blocking.append(f"{ident}: {statement}")
            elif "open" in status or "unverified" in status:
                open_items += 1
        if blocking:
            problems.append("section 5: unresolved blocking assumption(s) -- "
                            "these change a decision if wrong:")
            problems.extend(f"    {b}" for b in blocking)
        if open_items:
            notes.append(f"{open_items} non-blocking open item(s) carried forward")

    # Cross-check: geometry must not contain parts that never went through §4.
    if args.layout:
        if not os.path.isfile(args.layout):
            print(f"ERROR: layout not found: {args.layout}", file=sys.stderr)
            return EXIT_USAGE
        try:
            lay = open(args.layout, encoding="utf-8").read()
        except OSError as e:
            print(f"ERROR: cannot read {args.layout}: {e}", file=sys.stderr)
            return EXIT_USAGE
        lay = re.sub(r"//.*", "", lay)
        names = re.findall(r'\[\s*"([^"]+)"\s*,', lay)
        missing = [n for n in names
                   if n.lower() not in planned and not n.startswith("<")]
        if missing:
            problems.append(
                f"parts in {os.path.basename(args.layout)} that never appear in "
                f"the design order: {', '.join(missing)} -- these were invented "
                f"during detail work and skipped planning")
        elif names:
            notes.append(f"all {len(names)} layout parts appear in the plan")

    for n in notes:
        print(f"  note: {n}")
    if problems:
        print(f"\nFAIL: {os.path.basename(args.plan)} is not ready to gate detail "
              f"work:")
        for p in problems:
            print(f"  - {p}")
        print("\nFinish the plan before computing ratios, centre distances or "
              "geometry. A wrong architecture cannot be corrected by better "
              "numbers downstream.")
        return EXIT_INCOMPLETE

    print(f"\nOK: {os.path.basename(args.plan)} passes the planning gate.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
