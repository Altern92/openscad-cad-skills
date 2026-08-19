#!/usr/bin/env python3
"""Verify a bore/pocket is actually open to the outside of the part, not sealed.

`check_features.py` measures a bore's diameter wherever it's told to probe.
`check_connectivity.py` and `is_watertight` both report clean for a fully
enclosed internal cavity. None of them can tell a real through-bore from a
sealed tunnel, because a sealed cavity is still one connected, perfectly
valid watertight shell -- geometrically indistinguishable from a good bore
by any check that doesn't know where "outside the part" is.

Confirmed failure mode, not a hypothetical: a gearbox frame with three
bearing towers built as cylinders with a bore drilled perpendicular through
each tower's own center axis passed every check above while all three bores
were sealed behind ~8mm of solid, un-bored material -- a wall centered
exactly on the tower's own axis, so reaching the tower's true (curved)
exterior needed the tower's full radius, not the small fixed buffer the
bore actually had. The part was completely unassemblable and nothing said
so (INCIDENTS.md, 2026-08-19, "bearing bores never reached the tower's
true exterior surface").

This does a point-containment scan along each declared bore's own axis,
from a point outside the part to the bore's seat position, and fails if any
sampled point along that path is inside the solid mesh.

Declare each bore to check in a JSON file passed with --bores:

    [
      {"name": "bearing_tower_1_bore", "part": "gearbox_frame",
       "start": [-50, 10, 10], "end": [4, 10, 10], "step_mm": 0.5}
    ]

"start" is a point that must be OUTSIDE the part, on the bore's centerline,
beyond where the bore enters. "end" is the seat position (how far in the
bearing/shaft/fastener actually needs to travel) -- not necessarily the
part's far surface. "part" is matched case-insensitively as a substring
against each input STL's basename, the same convention check_collisions.py
uses for its contacts file. "step_mm" defaults to 0.25mm if omitted.

Getting start/end backwards or wrong doesn't fail closed -- a bore checked
against the wrong axis or a start point that's already inside the part
will pass regardless of whether the real bore is open. This checks exactly
the segment it's told to check; it is not a substitute for looking at the
part.

Requires: trimesh, numpy, rtree (trimesh's point-in-mesh containment test needs
rtree for its triangle bounds tree; without it `.contains()` raises
ModuleNotFoundError, not a silent wrong answer -- confirmed by hitting this
directly while building this script). Install with:
    pip install trimesh numpy rtree

Usage:
    python3 check_bore_reachability.py --bores bores.json build/*.stl

Exit codes:
    0  pass -- every declared bore's path is clear along its whole segment.
    3  fail -- at least one declared bore is blocked by solid material.
    4  usage/runtime error (missing file, no matching part, bad declaration).
"""
import argparse
import json
import os
import sys

EXIT_OK = 0
EXIT_FAIL = 3
EXIT_USAGE = 4

try:
    import numpy as np
    import trimesh
except ImportError:
    print("ERROR: trimesh/numpy not installed. Run: pip install trimesh numpy rtree",
          file=sys.stderr)
    sys.exit(EXIT_USAGE)

try:
    import rtree  # noqa: F401  -- trimesh.contains() needs this, checked eagerly
except ImportError:
    print("ERROR: rtree not installed -- trimesh's point-in-mesh containment test "
          "needs it for its triangle bounds tree. Run: pip install rtree",
          file=sys.stderr)
    sys.exit(EXIT_USAGE)


def load_bores(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read bores file {path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if isinstance(data, dict):
        data = data.get("bores", [])
    if not isinstance(data, list):
        print(f"ERROR: {path} must contain a JSON list of bore entries, or an "
              f"object with a \"bores\" list.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    for entry in data:
        missing = [k for k in ("name", "part", "start", "end") if k not in entry]
        if missing:
            print(f"ERROR: bore entry missing {missing}: {entry}", file=sys.stderr)
            sys.exit(EXIT_USAGE)
        if len(entry["start"]) != 3 or len(entry["end"]) != 3:
            print(f"ERROR: bore '{entry.get('name')}' start/end must be [x,y,z]: "
                  f"{entry}", file=sys.stderr)
            sys.exit(EXIT_USAGE)
    return data


def match_part(bores, stl_path):
    base = os.path.basename(stl_path).lower()
    return [b for b in bores if str(b["part"]).lower() in base]


def sample_axis(start, end, step_mm):
    start = np.array(start, dtype=float)
    end = np.array(end, dtype=float)
    length = float(np.linalg.norm(end - start))
    if length == 0.0:
        return np.array([start])
    n = max(2, int(length / step_mm) + 1)
    return np.linspace(start, end, n)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stls", nargs="*", help="positioned part STLs")
    parser.add_argument("--bores", required=True,
                         help="JSON file declaring bore axis segments to check")
    args = parser.parse_args()

    if not args.stls:
        print("Need at least 1 STL file to check.", file=sys.stderr)
        return EXIT_USAGE

    bores = load_bores(args.bores)
    if not bores:
        print(f"ERROR: {args.bores} declares no bores.", file=sys.stderr)
        return EXIT_USAGE

    failures = []
    checked = 0
    matched_names = set()

    for stl_path in args.stls:
        entries = match_part(bores, stl_path)
        if not entries:
            continue
        try:
            m = trimesh.load(stl_path, force="mesh")
        except Exception as e:
            print(f"ERROR: cannot load {stl_path}: {e}", file=sys.stderr)
            return EXIT_USAGE
        if m.is_empty:
            print(f"ERROR: {stl_path} contains no geometry.", file=sys.stderr)
            return EXIT_USAGE
        if not m.is_watertight:
            print(f"ERROR: {stl_path} is not watertight -- containment results "
                  f"for it are unreliable.", file=sys.stderr)
            return EXIT_USAGE

        for entry in entries:
            matched_names.add(entry["name"])
            step = float(entry.get("step_mm", 0.25))
            axis_pts = sample_axis(entry["start"], entry["end"], step)
            inside = m.contains(axis_pts)
            blocked = axis_pts[inside]
            checked += 1
            if len(blocked) > 0:
                first = blocked[0]
                failures.append(
                    f"BLOCKED: '{entry['name']}' in {os.path.basename(stl_path)} -- "
                    f"{len(blocked)}/{len(axis_pts)} sampled points along the bore "
                    f"axis are inside solid material, first at "
                    f"({first[0]:.2f}, {first[1]:.2f}, {first[2]:.2f})")

    unmatched = {b["name"] for b in bores} - matched_names
    if unmatched:
        print(f"ERROR: no input STL matched these declared bores' \"part\": "
              f"{sorted(unmatched)}", file=sys.stderr)
        return EXIT_USAGE

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        print("Fix at the source -- extend the bore/pocket geometry so material "
              "is actually removed along the whole declared path. Do not shorten "
              "the declared 'end' just to make this pass; 'end' is the real seat "
              "position the bearing/shaft/fastener needs to reach.")
        return EXIT_FAIL

    print(f"OK: {checked} declared bore(s) clear along their full path.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
