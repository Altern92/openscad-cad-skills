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
                           "Range-checked" means against penetration depth in
                           mm (FCL's per-contact-point narrow-phase depth,
                           the max over each pair -- the same standard
                           quantity GJK/EPA-style contact libraries expose in
                           robotics/contact mechanics), compared directly to
                           the declared expected_interference_mm range. This
                           replaced an earlier boolean-intersection VOLUME
                           check (2026-08-19) that could not be compared
                           precisely to a linear mm spec without knowing
                           contact area -- confirmed as a real gap: a
                           declared 0.0-0.5mm press fit accepted a 1114mm^3
                           overlap between two ~R20mm cylinders with
                           effectively no check at all before this fix, and
                           even the volume-plausibility-bound interim fix
                           was still only a proxy, not an exact comparison
                           (INCIDENTS.md 2026-08-19). Volume is still
                           reported alongside depth for context, and remains
                           the fallback if FCL contact data is unavailable
                           for a pair that trimesh otherwise reports as
                           colliding. Not a whole-shape EPA minimum-
                           translation-distance -- that needs convex
                           decomposition of each part first, which this does
                           not do -- so for non-convex geometry with multiple
                           simultaneous contact regions this is the worst
                           LOCAL penetration found, a defensible but not
                           exact-global measure.

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
    # Two accepted shapes: a bare list of contacts (the original form), or an
    # object with "contacts" alongside the "motion" block motion_sweep.py reads
    # from the same file. Both scripts share one joints.json.
    if isinstance(data, dict):
        data = data.get("contacts", [])
    if not isinstance(data, list):
        print(f"ERROR: {path} must contain a JSON list of contact entries, or an "
              f"object with a \"contacts\" list.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    data = [e for e in data if isinstance(e, dict) and "pair" in e]
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


def pair_penetration_depth(contact_data, name_a, name_b):
    """Worst (max) penetration depth in mm among FCL contact points for this
    pair, or None if no contact data covers it.

    This is FCL's per-contact-point penetration_depth (narrow-phase, from the
    BVH triangle-pair collision), not a whole-shape EPA-style minimum-
    translation-distance -- getting that would need convex decomposition of
    each part first. For a declared interference spec written as a linear mm
    value, per-contact depth is still a direct, correctly-united comparison
    -- unlike a boolean-intersection VOLUME, which can only be compared to a
    linear mm spec via an arbitrary proxy (see the plausibility-bound
    fallback below, kept only for when contact data is unavailable).
    """
    depths = [c.depth for c in contact_data if c.names == {name_a, name_b}]
    return max(depths) if depths else None


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
    is_collision, contact_names, contact_data = manager.in_collision_internal(
        return_names=True, return_data=True)
    if is_collision:
        colliding = {frozenset(pair) for pair in contact_names}

    failures = []
    notes = []

    for a, b in itertools.combinations(paths, 2):
        decl = match_contact(contacts, a, b)
        overlaps = frozenset((a, b)) in colliding
        label = f"{os.path.basename(a)} <-> {os.path.basename(b)}"

        if overlaps:
            depth = pair_penetration_depth(contact_data, a, b)
            vol = overlap_volume(meshes[a], meshes[b])
            if decl is None:
                extra = f", penetration depth {depth:.3f} mm" if depth is not None else (
                    f", overlap volume {vol:.2f} mm^3" if vol else "")
                failures.append(f"UNINTENDED INTERFERENCE: {label}{extra}")
                continue

            lo, hi = (decl.get("expected_interference_mm") or [0.0, 0.0])[:2]
            joint = decl.get("joint_type", "declared")

            if depth is not None:
                # Penetration depth (FCL narrow-phase, max over this pair's
                # contact points) is a linear mm quantity -- the same unit
                # expected_interference_mm is written in, so this compares
                # directly and exactly, unlike a boolean-intersection volume
                # (2026-08-19: upgraded from a volume-vs-part-fraction
                # heuristic after Perplexity deep-research confirmed
                # penetration depth, not volume, is the standard quantity
                # for this in contact mechanics/robotics -- GJK/EPA-style
                # libraries expose it directly, and trimesh already wraps
                # FCL for exactly this). Not a whole-shape EPA minimum-
                # translation-distance (that needs convex decomposition
                # first) -- this is the worst LOCAL penetration among
                # detected contact points, a defensible proxy but not an
                # exact global minimum for non-convex geometry.
                if depth < lo or depth > hi:
                    failures.append(
                        f"DECLARED INTERFERENCE OUT OF RANGE: {label} is "
                        f"declared '{joint}' ({lo}-{hi} mm), but measured "
                        f"penetration depth is {depth:.3f} mm")
                else:
                    vol_str = f", overlap volume {vol:.2f} mm^3" if vol is not None else ""
                    notes.append(
                        f"OK (intentional {joint}): {label}, penetration "
                        f"depth {depth:.3f} mm, declared range {lo}-{hi} mm"
                        f"{vol_str}")
                continue

            # No contact data for this pair (shouldn't normally happen when
            # `overlaps` is True, but defensive): fall back to the coarser
            # volume-based plausibility bound instead of silently passing.
            if vol is None:
                notes.append(
                    f"UNVERIFIED {joint}: {label} overlaps as declared, but "
                    f"neither penetration depth nor a mesh boolean engine "
                    f"is available to measure it against the {lo}-{hi} mm "
                    f"range (pip install manifold3d)")
                degraded = True
            else:
                plausibility_frac = 0.25
                min_own_vol = None
                if hi > 0.0:
                    try:
                        if meshes[a].is_watertight and meshes[b].is_watertight:
                            min_own_vol = min(abs(meshes[a].volume), abs(meshes[b].volume))
                    except Exception:
                        min_own_vol = None
                if hi <= 0.0 and vol > 0.0:
                    failures.append(
                        f"DECLARED CONTACT EXCEEDED: {label} is declared "
                        f"'{joint}' with no permitted interference, but overlaps "
                        f"by {vol:.2f} mm^3")
                elif min_own_vol and vol > plausibility_frac * min_own_vol:
                    failures.append(
                        f"IMPLAUSIBLE DECLARED OVERLAP: {label} is declared "
                        f"'{joint}' ({lo}-{hi} mm), but the {vol:.2f} mm^3 "
                        f"overlap is {100*vol/min_own_vol:.0f}% of the smaller "
                        f"part's own volume -- far beyond what a surface-level "
                        f"interference fit produces. This is gross overlap, not "
                        f"a press fit; fix the position/size at the source.")
                else:
                    notes.append(
                        f"OK (intentional {joint}, volume-only fallback): "
                        f"{label}, overlap {vol:.2f} mm^3, declared range "
                        f"{lo}-{hi} mm")
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
