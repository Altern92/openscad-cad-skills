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
Names match the part name exactly (case-insensitive; P26 / AC-3 -- substrings let a
label like "s" match every part). Parts are parts/*.scad minus PREVIEW_FILE; when build/ holds rendered
STLs, only parts that rendered count (a shared module library renders nothing).

Retention (INC-2026-11-07-01): a joints.json contact only says two parts TOUCH,
not that anything HOLDS them -- a divider shelf with flush seams to four panels
passed every check while nothing supported it. So every part must also say what
retains it:
  - attachments.json {"part": "<this part>", ...} (a material point that
    check_attachment.py verifies), or
  - `// NO_RETENTION: <reason>` (e.g. "held by gravity in a pocket"), or
  - `// NO_JOINT: <reason>` (its reason already names what holds it, e.g. a
    carrier clipped onto a purchased DIN rail).
Being only the "to" side of an attachment does not count.

The joint graph's components are printed too: two joined clusters that never
meet are legal here but worth a look.

Geometry (P26 / AC-1, Fable audit 2026-11-19): a declaration alone proved nothing -- a
shelf 110 mm above its base passed. With --geometry build/positioned every declared joint
(contact pair, attachment part -> to) is measured on the positioned meshes: farther apart
than MAX_GAP_MM, or a name with no positioned STL, is a FAIL.

Usage:
    python3 check_joint_graph.py --project-dir .
    python3 check_joint_graph.py --project-dir . --geometry build/positioned

Exit codes:
    0  pass, or SKIP (fewer than 2 parts)
    3  fail -- a part has no joint and no NO_JOINT reason, or nothing declares what retains it
    4  usage error (unreadable joints.json / attachments.json)
"""
import argparse
import glob
import json
import os
import re
import sys

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 3, 4
from markers import LIBRARY_RE, NO_JOINT_RE, NO_RETENTION_RE, PREVIEW_RE
MAX_GAP_MM = 1.0  # same cap as behavior.json max_gap: a bigger gap is a missing part


def mesh_gap(a, b):
    """Smallest distance between two meshes (0 when they touch or overlap)."""
    import numpy as np
    import trimesh
    lo, hi = np.maximum(a.bounds[0], b.bounds[0]), np.minimum(a.bounds[1], b.bounds[1])
    box = float(np.linalg.norm(np.maximum(lo - hi, 0.0)))
    if box > MAX_GAP_MM:  # the boxes alone are already too far apart (a lower bound)
        return box
    best = float("inf")
    for m, n in ((a, b), (b, a)):
        pts = np.vstack([m.vertices, trimesh.sample.sample_surface(m, 4000, seed=0)[0]])
        if n.is_watertight and n.contains(pts).any():
            return 0.0
        best = min(best, float(trimesh.proximity.closest_point(n, pts)[1].min()))
    return best


def bridge(x, y, printed, behavior):
    """Chain x -> ... -> y in behavior.json joints whose inner bodies are all non-printed (purchased parts:
    ball cups, bearings, pins). check_behavior.py renders those bodies and measures each of their joints,
    so a gap between two printed parts that a modelled vitamin fills is proven there, not here."""
    adj = {}
    for j in (behavior or {}).get("joints", []) if isinstance(behavior, dict) else []:
        a, b = str(j.get("a", "")).lower(), str(j.get("b", "")).lower()
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    bodies = behavior.get("bodies", {}) if isinstance(behavior, dict) else {}
    # printed = rendered as a part (mirror copies like upper_arm_l included), not only the positioned STL names
    printed = set(printed) | {str(k).lower() for k, b in bodies.items()
                              if any(str(r.get("MODE", "")).strip('"') in ("part", "assembly")
                                     for r in (b or {}).get("render", []) if isinstance(r, dict))}
    from collections import deque
    seen, stack = {x: None}, deque([x])   # breadth first: the shortest bridge is the one to report
    while stack:
        n = stack.popleft()
        for m in adj.get(n, ()):
            if m == y and n != x:
                path = [n]
                while seen[path[-1]] not in (None, x):
                    path.append(seen[path[-1]])
                return path[::-1]
            if m not in seen and m not in printed:
                seen[m] = n; stack.append(m)
    return None


def geometry(edges, pos_dir, behavior=None):
    """FAIL lines for declared joints whose positioned meshes are apart or missing."""
    import trimesh
    stls = {os.path.splitext(os.path.basename(p))[0].lower(): p for p in glob.glob(os.path.join(pos_dir, "*.stl"))}
    meshes, bad, n = {}, [], 0
    for x, y in dict.fromkeys(tuple(sorted((str(a).lower(), str(b).lower()))) for a, b in edges):
        gone = [v for v in (x, y) if v not in stls]
        if gone:
            bad.append(f"FAIL: contact_geometry, {x} <-> {y}: no part named {', '.join(gone)} in {pos_dir} "
                       f"-- a declaration must name a real part exactly")
            continue
        for v in (x, y):
            meshes.setdefault(v, trimesh.load(stls[v], force="mesh"))
        gap = mesh_gap(meshes[x], meshes[y]); n += 1
        via = bridge(x, y, set(stls), behavior) if gap > MAX_GAP_MM else None
        if via:
            print(f"INFO: contact_geometry, {x} and {y} are {gap:.1f} mm apart, bridged by purchased "
                  f"{' -> '.join(via)} (behavior.json; the behavior gate measures those joints)")
        elif gap > MAX_GAP_MM:
            bad.append(f"FAIL: contact_geometry, {x} and {y} are declared joined but are {gap:.1f} mm apart "
                       f"(cap {MAX_GAP_MM} mm) -- move the part onto its support or add the part that bridges the gap")
    return bad, n


def load(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--geometry", metavar="DIR", help="positioned STL dir: measure every declared joint")
    args = ap.parse_args()
    d = args.project_dir

    built = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(d, "build", "*.stl"))}
    parts, excused, ret_excused = [], set(), set()
    for scad in sorted(glob.glob(os.path.join(d, "parts", "*.scad"))):
        name = os.path.splitext(os.path.basename(scad))[0]
        src = open(scad, encoding="utf-8", errors="replace").read()
        if PREVIEW_RE.search(src) or LIBRARY_RE.search(src) or (built and name not in built):
            continue
        parts.append(name)
        if NO_JOINT_RE.search(src):
            excused.add(name)
        if NO_JOINT_RE.search(src) or NO_RETENTION_RE.search(src):
            ret_excused.add(name)
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
    edges, singles, holders = [], [], []
    for c in contacts:
        pair = c.get("pair") if isinstance(c, dict) else None
        if isinstance(pair, list) and len(pair) == 2:
            edges.append(tuple(pair))
    for a in attach or []:
        if isinstance(a, dict) and a.get("part") and not str(a.get("name", "")).startswith("_"):
            (edges.append((a["part"], a["to"])) if a.get("to") else singles.append(a["part"]))
            holders.append(a["part"])

    if args.geometry:
        try:
            behavior = load(os.path.join(d, "behavior.json"))
        except (ValueError, OSError):
            behavior = None
        bad, n = geometry(edges, args.geometry, behavior)
        print("\n".join(bad) if bad else f"PASS: contact_geometry, {n} declared joint(s) touch within {MAX_GAP_MM} mm "
              f"or are bridged by modelled purchased parts (INFO lines)")
        return EXIT_FAIL if bad else EXIT_OK

    def hits(label):
        return [p for p in parts if str(label).lower() == p.lower()]  # exact (P26 / AC-3)

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
    retained = {p for h in holders for p in hits(h)}
    unretained = [p for p in parts if p not in retained and p not in ret_excused]
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
    for p in missing:
        print(f"FAIL: joints, parts/{p}.scad is joined to nothing -- add a joints.json contact or an "
              f"attachments.json entry (\"part\"/\"to\"), or `// NO_JOINT: <reason>`")
    for p in unretained:
        print(f"FAIL: retention, parts/{p}.scad: nothing declares what holds it -- a joints.json contact only says it "
              f"touches. Add an attachments.json entry with \"part\": \"{p}\" (a material point check_attachment.py "
              f"verifies) or `// NO_RETENTION: <reason>`")
    if missing or unretained:
        return EXIT_FAIL
    print(f"PASS: joints, {len(parts)} part(s) each have a joint ({len(excused)} excused by NO_JOINT) "
          f"and a declared retention ({len(ret_excused)} by NO_JOINT/NO_RETENTION)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
