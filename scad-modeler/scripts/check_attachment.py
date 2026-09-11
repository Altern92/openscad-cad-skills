#!/usr/bin/env python3
"""Verify a part actually has material where it is supposed to attach to another.

Every other check in this chain asks whether a part is *correct*: is it one
solid (check_connectivity.py), is it the right size (check_dimensions.py), does
it collide (check_collisions.py), can a bore reach its seat
(check_bore_reachability.py). None of them asks the previous question: **does
this part have anything on it to attach with at all?**

That is a real, confirmed failure, not a hypothetical. A side panel shipped as
a bare 3 x 229.7 x 200 mm rectangle with zero attachment features -- no
flanges, no bosses, no holes. It passed connectivity (one solid), dimensions
(it was exactly the declared size) and collision (it collided, which was a
separate finding) while being physically impossible to fasten to anything. The
author had removed the bosses earlier "to make the assembly fit" and never put
them back, and nothing noticed, because connectivity checks whether a part is
one body, never whether that body carries attachment features
(INCIDENTS.md, 2026-09-11, "side panels: (a) no fastening at all, (b) collided
with the posts"; server_rack_modular_v4 v8).

This does a point-containment test: for each declared attachment point, the
mesh must contain solid material at that point. A point that falls in empty
space means the feature was never modelled, was removed, or has drifted
somewhere else -- all three are the same defect from the fastener's point of
view.

Declare each attachment in a JSON file passed with --attachments:

    [
      {"name": "side_panel_to_post_front",
       "part": "side_panel",
       "at": [0, 237.7, 100],
       "feature": "m3_boss",
       "min_material_mm": 6.0}
    ]

"at" is a point in the part's OWN local coordinates (the same coordinate system
the part file is modelled in and its STL is exported from -- not assembly
coordinates; this checks the part, not the assembly). "feature" is free text
for the report. "min_material_mm" is optional: when given, the checker also
samples a small ring of points at that radius around "at" and requires most of
them to be solid too, which distinguishes a real boss from a sliver that
happens to cross one point. Omit it and only the centre point is tested.

"part" is matched case-insensitively as a substring against each input STL's
basename, the same convention check_collisions.py and check_bore_reachability.py
use for their declaration files.

A declared point with no material fails closed: the declaration says a fastener
goes here, and a fastener cannot go through air. Getting the point wrong
(declaring it in assembly coordinates, say) will produce a failure, not a false
pass -- which is the safe direction.

Requires: trimesh, numpy, rtree (trimesh's point-in-mesh containment test needs
rtree for its triangle bounds tree; without it .contains() raises
ModuleNotFoundError rather than answering wrongly). Install with:
    pip install trimesh numpy rtree

Not wired into validate_scad.sh -- the declaration file is a deliberate extra
step the part file's author writes, the same way bores.json is a prerequisite
for check_bore_reachability.py rather than something the normal per-part render
produces on its own.

Usage:
    python3 check_attachment.py --attachments attachments.json build/*.stl

Exit codes:
    0  pass -- every declared attachment point has material.
    3  fail -- at least one declared attachment point is in empty space.
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


def load_attachments(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read attachments file {path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if not isinstance(data, list) or not data:
        print(f"ERROR: {path} must be a non-empty JSON list of attachment entries",
              file=sys.stderr)
        sys.exit(EXIT_USAGE)
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            print(f"ERROR: entry {i} in {path} is not an object", file=sys.stderr)
            sys.exit(EXIT_USAGE)
        for key in ("name", "part", "at"):
            if key not in entry:
                print(f"ERROR: entry {i} in {path} is missing required key {key!r}",
                      file=sys.stderr)
                sys.exit(EXIT_USAGE)
        at = entry["at"]
        if not isinstance(at, (list, tuple)) or len(at) != 3:
            print(f"ERROR: entry {i} ({entry.get('name')}): 'at' must be [x, y, z]",
                  file=sys.stderr)
            sys.exit(EXIT_USAGE)
    return data


def ring_points(centre, radius, samples=6):
    """A small ring of test points around the centre, one per axis pair.

    Sampling in the three coordinate planes rather than a sphere keeps this
    cheap and deterministic while still catching a sliver that crosses the
    centre point by accident.
    """
    cx, cy, cz = centre
    pts = []
    for i in range(samples):
        angle = 2.0 * np.pi * i / samples
        dx, dy = radius * np.cos(angle), radius * np.sin(angle)
        pts.append([cx + dx, cy + dy, cz])
        pts.append([cx + dx, cy, cz + dy])
        pts.append([cx, cy + dx, cz + dy])
    return pts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attachments", required=True,
                        help="JSON list of declared attachment points")
    parser.add_argument("stls", nargs="+", help="part STL file(s)")
    args = parser.parse_args()

    attachments = load_attachments(args.attachments)

    meshes = {}
    for stl in args.stls:
        if not os.path.isfile(stl):
            print(f"ERROR: STL not found: {stl}", file=sys.stderr)
            return EXIT_USAGE
        try:
            mesh = trimesh.load(stl, force="mesh")
        except Exception as e:
            print(f"ERROR: cannot load mesh {stl}: {e}", file=sys.stderr)
            return EXIT_USAGE
        if mesh.is_empty:
            print(f"ERROR: STL is empty or invalid: {stl}", file=sys.stderr)
            return EXIT_USAGE
        meshes[os.path.basename(stl)] = mesh

    failures = []
    checked = 0

    for entry in attachments:
        name = entry["name"]
        want = entry["part"].lower()
        matches = [(bn, m) for bn, m in meshes.items() if want in bn.lower()]
        if not matches:
            print(f"ERROR: no input STL matches part {entry['part']!r} "
                  f"(declared by attachment {name!r})", file=sys.stderr)
            return EXIT_USAGE
        if len(matches) > 1:
            print(f"ERROR: part {entry['part']!r} (attachment {name!r}) matches "
                  f"multiple STLs: {[bn for bn, _ in matches]}", file=sys.stderr)
            return EXIT_USAGE

        bn, mesh = matches[0]
        checked += 1
        point = np.asarray(entry["at"], dtype=float)

        has_material = bool(mesh.contains([point])[0])
        detail = "material present" if has_material else "EMPTY SPACE"

        ring_ok = None
        ring_total = None
        min_material = entry.get("min_material_mm")
        if has_material and min_material:
            pts = ring_points(point.tolist(), float(min_material) / 2.0)
            ring_total = len(pts)
            inside = mesh.contains(np.asarray(pts, dtype=float))
            ring_ok = int(inside.sum())
            detail += (f", ring {ring_ok}/{ring_total} solid at "
                       f"r={float(min_material)/2:.2f}mm")

        # A declared point with no material always fails. The ring is advisory
        # only: fewer than half its samples solid suggests a sliver rather than
        # a real boss, which is worth failing on but is not certain -- the
        # message says "likely", not "definitely".
        too_thin = ring_ok is not None and ring_ok < ring_total / 2
        failed = (not has_material) or too_thin

        feature = entry.get("feature", "attachment")
        status = "FAIL" if failed else "PASS"
        print(f"{status}: {name} [{feature}] on {bn} at {point.tolist()} -- {detail}")
        if failed:
            failures.append((name, bn, point.tolist(), has_material, ring_ok))

    print()
    if failures:
        print(f"{len(failures)} of {checked} declared attachment point(s) have a "
              f"problem:")
        for name, bn, pt, has_material, ring_ok in failures:
            if not has_material:
                print(f"  - {name} ({bn}): no material at {pt} -- the attachment "
                      f"feature is missing, was removed, or has drifted. A "
                      f"fastener cannot go through air.")
            else:
                print(f"  - {name} ({bn}): material at {pt} is too thin "
                      f"(ring only {ring_ok} solid samples) -- likely a sliver, "
                      f"not a usable boss.")
        print("Fix by modelling the feature, or correct the declared point if it "
              "was written in the wrong coordinate system -- do not delete the "
              "declaration to make this pass.")
        return EXIT_FAIL

    print(f"OK: all {checked} declared attachment point(s) have material.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
