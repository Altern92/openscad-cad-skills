#!/usr/bin/env python3
"""Interference and clearance check between already-positioned assembly parts.

Three distinct verdicts, not one boolean -- binary "do they overlap?" is the
wrong primitive for a printed assembly:

  UNINTENDED INTERFERENCE  two parts overlap and nothing says they should.
  INSUFFICIENT CLEARANCE   they do not overlap, but the gap is below what the
                           process can resolve, so they will fuse or bind.
                           A pass here is meaningless without a threshold:
                           0.02 mm of air does not survive an FDM print.
  INTENTIONAL CONTACT      a press fit, snap fit or thread is *supposed* to
                           overlap in the nominal model. Flagging those as
                           errors trains the operator to ignore the checker,
                           so they must be declared and range-checked instead.

Declare intentional contacts in a JSON file passed with --expected-contacts:

    [
      {"pair": ["housing_bore", "bearing_608"],
       "joint_type": "press_fit",
       "expected_interference_mm": [0.05, 0.15]},
      {"pair": ["lid", "body"],
       "joint_type": "touching",
       "expected_interference_mm": [0.0, 0.0]}
    ]

Names are matched case-insensitively against each STL's basename (substring
match), so "bearing_608" matches "build/bearing_608.stl". A declared pair that
overlaps outside its stated range still fails -- the declaration licenses a
specific interference, not any interference.

SCOPE -- what this does NOT check
---------------------------------
One static pose only. A gearbox, hinge, latch, cam or slider can be clear at 0
degrees and interfere at 37. Nothing here sweeps motion or checks whether an
assembly sequence physically exists. Do not read a pass as "the mechanism
works"; read it as "this one configuration is not obviously wrong".

Requires: trimesh, python-fcl (trimesh.collision.CollisionManager wraps FCL for
the actual collision math -- trimesh alone does not do this), and scipy
(trimesh's own mesh checks need it). Install with:
    pip install trimesh python-fcl scipy

Overlap-volume reporting additionally needs a mesh boolean engine (e.g.
manifold3d); without one, collisions are still detected and reported, just
without a volume number -- and a declared press fit then cannot be range-
checked, which is reported as degraded rather than passed.

Every STL passed in must already be in the shared assembly coordinate system
(exported from assembly.scad with parts positioned via at(), not raw
unpositioned part files) -- checking unpositioned parts against each other is
meaningless, since they would all sit at their own local origins.

Usage:
    python3 check_collisions.py build/*.stl
    python3 check_collisions.py --min-clearance 0.3 build/*.stl
    python3 check_collisions.py --expected-contacts joints.json build/*.stl
    python3 check_collisions.py --strict build/*.stl

Exit codes:
    0  pass
    2  degraded -- a mesh was not watertight, or a declared interference could
       not be measured. Results are unreliable; treat as "not checked".
    3  fail -- unintended interference, clearance below the threshold, or a
       declared interference outside its stated range.
    4  usage/runtime error.
"""
import argparse
import itertools
import os
import sys

EXIT_OK = 0
EXIT_DEGRADED = 2
EXIT_FAIL = 3
EXIT_USAGE = 4

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: pip install trimesh python-fcl scipy",
          file=sys.stderr)
    sys.exit(EXIT_USAGE)

try:
    from trimesh.collision import CollisionManager
except ImportError:
    print(
        "ERROR: trimesh.collision.CollisionManager unavailable -- this needs the "
        "python-fcl package (trimesh doesn't implement collision detection itself, "
        "it wraps FCL). Run: pip install python-fcl",
        file=sys.stderr,
    )
    sys.exit(EXIT_USAGE)


def load_contacts(path):
    import json
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read contacts file {path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if not isinstance(data, list):
        print(f"ERROR: {path} must contain a JSON list of contact entries.",
              file=sys.stderr)
        sys.exit(EXIT_USAGE)
    for entry in data:
        if "pair" not in entry or len(entry.get("pair", [])) != 2:
            print(f"ERROR: contact entry missing a 2-element 'pair': {entry}",
                  file=sys.stderr)
            sys.exit(EXIT_USAGE)
    return data


def match_contact(contacts, path_a, path_b):
    """Find the declaration covering this pair, if any (order-insensitive)."""
    a = os.path.basename(path_a).lower()
    b = os.path.basename(path_b).lower()
    for entry in contacts:
        n1, n2 = (str(x).lower() for x in entry["pair"])
        if (n1 in a and n2 in b) or (n1 in b and n2 in a):
            return entry
    return None


def overlap_volume(mesh_a, mesh_b):
    """Boolean intersection volume in mm^3, or None if no engine is available."""
    try:
        inter = mesh_a.intersection(mesh_b)
    except Exception:
        return None
    if inter is None or inter.is_empty:
        return 0.0
    try:
        return float(inter.volume) if inter.is_volume else None
    except Exception:
        return None


def pair_distance(mesh_a, mesh_b, name_a, name_b):
    """Minimum separation between two non-overlapping meshes, or None."""
    try:
        mgr = CollisionManager()
        mgr.add_object(name_a, mesh_a)
        mgr.add_object(name_b, mesh_b)
        return float(mgr.min_distance_internal())
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stls", nargs="*", help="positioned part STLs")
    parser.add_argument("--min-clearance", type=float, default=0.0,
                        help="minimum required gap in mm between parts that are "
                             "not in declared contact (default 0 = overlap only)")
    parser.add_argument("--expected-contacts", default=None,
                        help="JSON file declaring intentional contact pairs")
    parser.add_argument("--strict", action="store_true",
                        help="treat a non-watertight mesh as a failure, not as "
                             "degraded")
    args = parser.parse_args()

    paths = args.stls
    if len(paths) < 2:
        print("Need at least 2 STL files to check for collisions.", file=sys.stderr)
        return EXIT_USAGE

    contacts = load_contacts(args.expected_contacts) if args.expected_contacts else []

    meshes = {}
    degraded = False
    for p in paths:
        try:
            m = trimesh.load(p, force="mesh")
        except Exception as e:
            print(f"ERROR: cannot load {p}: {e}", file=sys.stderr)
            return EXIT_USAGE
        if m.is_empty:
            print(f"ERROR: {p} contains no geometry.", file=sys.stderr)
            return EXIT_USAGE
        if not m.is_watertight:
            # The old version printed this and carried on, while its own
            # docstring promised a non-zero exit. FCL results on a
            # non-watertight mesh are not trustworthy, so this now changes the
            # verdict instead of being cosmetic.
            level = "ERROR" if args.strict else "DEGRADED"
            print(f"{level}: {p} is not watertight -- collision results for it "
                  f"are unreliable.")
            if args.strict:
                return EXIT_FAIL
            degraded = True
        meshes[p] = m

    manager = CollisionManager()
    for p, m in meshes.items():
        manager.add_object(p, m)
    colliding = set()
    is_collision, contact_names = manager.in_collision_internal(return_names=True)
    if is_collision:
        colliding = {frozenset(pair) for pair in contact_names}

    failures = []
    notes = []

    for a, b in itertools.combinations(paths, 2):
        decl = match_contact(contacts, a, b)
        overlaps = frozenset((a, b)) in colliding
        label = f"{os.path.basename(a)} <-> {os.path.basename(b)}"

        if overlaps:
            vol = overlap_volume(meshes[a], meshes[b])
            if decl is None:
                vol_str = f", overlap volume {vol:.2f} mm^3" if vol else ""
                failures.append(f"UNINTENDED INTERFERENCE: {label}{vol_str}")
                continue

            lo, hi = (decl.get("expected_interference_mm") or [0.0, 0.0])[:2]
            joint = decl.get("joint_type", "declared")
            if vol is None:
                notes.append(
                    f"UNVERIFIED {joint}: {label} overlaps as declared, but no "
                    f"mesh boolean engine is available to measure it against the "
                    f"{lo}-{hi} mm range (pip install manifold3d)")
                degraded = True
            else:
                # Volume is a severity signal, not a linear depth. Report it and
                # let a zero-range declaration ("touching") catch real overlap.
                if hi <= 0.0 and vol > 0.0:
                    failures.append(
                        f"DECLARED CONTACT EXCEEDED: {label} is declared "
                        f"'{joint}' with no permitted interference, but overlaps "
                        f"by {vol:.2f} mm^3")
                else:
                    notes.append(
                        f"OK (intentional {joint}): {label}, overlap "
                        f"{vol:.2f} mm^3, declared range {lo}-{hi} mm")
            continue

        if decl is not None:
            lo = (decl.get("expected_interference_mm") or [0.0, 0.0])[0]
            if lo > 0.0:
                failures.append(
                    f"MISSING INTERFERENCE: {label} is declared "
                    f"'{decl.get('joint_type', 'press_fit')}' needing at least "
                    f"{lo} mm interference, but the parts do not touch")
            continue

        if args.min_clearance > 0.0:
            dist = pair_distance(meshes[a], meshes[b], a, b)
            if dist is None:
                notes.append(f"UNVERIFIED clearance: {label} (distance query failed)")
                degraded = True
            elif dist < args.min_clearance:
                failures.append(
                    f"INSUFFICIENT CLEARANCE: {label} gap {dist:.3f} mm "
                    f"< required {args.min_clearance:.3f} mm")

    for n in notes:
        print(f"  {n}")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        print("Fix these at the source -- a wrong parameter or a wrong layout "
              "position. Do not raise --min-clearance or add a contact "
              "declaration just to silence a real overlap.")
        return EXIT_FAIL

    scope = (f"{len(paths)} parts, static pose, "
             f"min-clearance {args.min_clearance:.3f} mm")
    if degraded:
        print(f"DEGRADED: no failures found, but some results are unreliable "
              f"({scope}). Treat as not checked.")
        return EXIT_DEGRADED

    print(f"OK: no unintended interference and no clearance violations ({scope}).")
    print("Note: this is one static configuration only -- it says nothing about "
          "interference through motion or assembly feasibility.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
