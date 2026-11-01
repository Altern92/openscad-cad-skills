#!/usr/bin/env python3
"""Every part of an assembly is joined to something (P4, 2026-11-01).

D class, 13 of 95 incidents: a part with nothing holding it to the rest. The
side panels of a server rack had no fastening at all and passed connectivity,
dimensions and collisions, because each of those asks whether a part is
CORRECT, never whether it is ATTACHED. MUSE-style assembly graphs make the
joint a first-class fact; here it is one line in a file the project already has.

A part is joined when it appears in
  - joints.json "contacts": {"pair": ["a", "b"], ...}, or
  - attachments.json: {"part": "c", "to": "a", ...} (as part or as "to"),
or it says why not: `// NO_JOINT: <reason>` (a loose tray, a spare).
Names match case-insensitively as substrings, the same rule check_collisions.py
uses. Parts are parts/*.scad minus PREVIEW_FILE; when build/ holds rendered
STLs, only parts that rendered count (a shared module library renders nothing).

The joint graph's components are printed too: two joined clusters that never
meet are legal here but worth a look.

Usage:
    python3 check_joint_graph.py --project-dir .

Exit codes:
    0  pass, or SKIP (fewer than 2 parts)
    3  fail -- a part has no joint and no NO_JOINT reason
    4  usage error (unreadable joints.json / attachments.json)
"""
import argparse
import glob
import json
import os
import re
import sys

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4
NO_JOINT_RE = re.compile(r"^[ \t]*//[ \t]*NO_JOINT[ \t]*:[ \t]*\S", re.M)
PREVIEW_RE = re.compile(r"^\s*//\s*PREVIEW_FILE", re.M)


def load(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", default=".")
    d = ap.parse_args().project_dir

    built = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(d, "build", "*.stl"))}
    parts, excused = [], set()
    for scad in sorted(glob.glob(os.path.join(d, "parts", "*.scad"))):
        name = os.path.splitext(os.path.basename(scad))[0]
        src = open(scad, encoding="utf-8", errors="replace").read()
        if PREVIEW_RE.search(src) or (built and name not in built):
            continue
        parts.append(name)
        if NO_JOINT_RE.search(src):
            excused.add(name)
    if len(parts) < 2:
        print(f"SKIP: joints, {len(parts)} printable part(s) -- a joint graph needs 2+")
        return EXIT_OK

    try:
        joints = load(os.path.join(d, "joints.json"))
        attach = load(os.path.join(d, "attachments.json"))
    except (ValueError, OSError) as e:
        print(f"ERROR: cannot read joint declarations: {e}", file=sys.stderr)
        return EXIT_USAGE
    contacts = joints.get("contacts", []) if isinstance(joints, dict) else (joints or [])
    edges, singles = [], []
    for c in contacts:
        pair = c.get("pair") if isinstance(c, dict) else None
        if isinstance(pair, list) and len(pair) == 2:
            edges.append(tuple(pair))
    for a in attach or []:
        if isinstance(a, dict) and a.get("part") and not str(a.get("name", "")).startswith("_"):
            (edges.append((a["part"], a["to"])) if a.get("to") else singles.append(a["part"]))

    def hits(label):
        return [p for p in parts if str(label).lower() in p.lower()]

    joined, adj = set(), {p: set() for p in parts}
    for x, y in edges:
        hx, hy = hits(x), hits(y)
        joined.update(hx + hy)
        for a in hx:
            for b in hy:
                if a != b:
                    adj[a].add(b); adj[b].add(a)
    for s in singles:
        joined.update(hits(s))

    missing = [p for p in parts if p not in joined and p not in excused]
    seen, comps = set(), []
    for p in parts:
        if p in seen or p in excused:
            continue
        stack, comp = [p], []
        while stack:
            q = stack.pop()
            if q in seen:
                continue
            seen.add(q); comp.append(q); stack += adj[q]
        comps.append(sorted(comp))
    if len(comps) > 1:
        print(f"INFO: joint graph has {len(comps)} separate groups: " + " | ".join(", ".join(c) for c in comps))
    if missing:
        for p in missing:
            print(f"FAIL: joints, parts/{p}.scad is joined to nothing -- add a joints.json contact or an "
                  f"attachments.json entry (\"part\"/\"to\"), or `// NO_JOINT: <reason>`")
        return EXIT_FAIL
    print(f"PASS: joints, {len(parts)} part(s) each have a joint ({len(excused)} excused by NO_JOINT)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
