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

An UNDECLARED pair this shallow gets a fourth, more actionable verdict
instead of a bare UNINTENDED INTERFERENCE (2026-08-19 Phase-2 Pattern 2,
implemented 2026-08-22): a gap or penetration depth at or below
--touch-tolerance (default 0.05mm) is classified CANDIDATE INTENTIONAL
TOUCH, printed with a ready-to-paste joints.json stub for a human/agent
to confirm -- targeting the real gap where a benign design touch (a
clamshell split line, say) was correctly reasoned about during design but
never formalized as a declaration (INCIDENTS.md, 2026-08-18,
gearbox_case_bottom/top). Still a FAIL either way -- nothing is
auto-authorized. A slightly larger gap, in (touch-tolerance,
--near-miss-tolerance] (default up to 0.2mm), is reported as a non-fatal
NEAR MISS note instead: that band is more often a genuine design
sensitivity than a benign touch, so it is surfaced but not auto-suggested
as intentional. Both are checked unconditionally for every undeclared,
non-overlapping pair now, not only when --min-clearance is passed. NOT
implemented: a stability check that re-renders with a jittered parameter
to see whether the touch/overlap verdict flips near a boundary (the
pattern write-up's own suggestion) -- that needs an actual re-render per
candidate pair, out of scope for a static post-hoc classifier.

Declare intentional contacts in a JSON file passed with --expected-contacts:

    [
      {"pair": ["housing_bore", "bearing_608"],
       "joint_type": "press_fit",
       "expected_interference_mm": [0.05, 0.15],
       "derivation": "bearing_608 OD 22.0mm nominal, housing bore 21.9mm per
                       shaft-fit table row 3 -- see calculations.md section 2"}
    ]

Names are matched case-insensitively against each STL's basename (substring
match), so "bearing_608" matches "build/bearing_608.stl". A declared pair that
overlaps outside its stated range still fails -- the declaration licenses a
specific interference, not any interference.

"derivation" is REQUIRED whenever expected_interference_mm is declared
(added 2026-08-21) -- a non-empty, human-written trace back to the source
parameters/formula this range came from. Confirmed as a real failure mode
in this skill's own example project: a range was initially copied from an
unrelated earlier test fixture rather than derived from the actual
geometry (INCIDENTS.md, 2026-08-21). This doesn't machine-verify the
derivation is arithmetically correct (that's a larger, deferred
influence-graph mechanism) -- it makes a hand-typed guess with no stated
origin impossible to declare silently.

A declared pair passing its depth range is ALSO checked for whether it
touches in exactly one contiguous region. A max-over-all-contact-points
penetration depth cannot tell "one legitimate contact zone" from "a
legitimate zone plus a completely separate, unrelated one that happens to
be similarly shallow" -- confirmed live: a declared gear-mesh contact's
overlap split into 7 disjoint regions, one of them entirely outside the
meshing feature's own physical extent, i.e. a real structural collision
hiding behind the same declared range as the legitimate contact
(INCIDENTS.md, 2026-08-19). More than one disjoint region fails as
MULTIPLE DISJOINT CONTACT REGIONS by default. For a joint that genuinely
touches in several places on purpose (a splined shaft, say), opt out with:

    {"pair": ["shaft", "spline_hub"], "joint_type": "spline",
     "expected_interference_mm": [0.0, 0.05], "multi_region_ok": true,
     "derivation": "spline: 6 teeth, each an independent contact patch by design"}

multi_region_ok only bounds the COUNT of regions, not WHERE they are --
declaring it true would still silently accept an extra, unrelated region
anywhere on the pair. For a stronger "contact witness" that authorizes
only the specific derived location, declare expected_bounds (added
2026-08-21) -- the assembly-space bounding box (same frame as the
positioned STLs) every detected region must fall inside, regardless of
multi_region_ok or how many regions there are:

    {"pair": ["worm", "wormwheel"], "joint_type": "worm_mesh",
     "expected_interference_mm": [0.5, 2.0], "multi_region_ok": true,
     "expected_bounds": [[54.0, -10.0, -5.0], [69.0, 10.0, 5.0]],
     "derivation": "worm thread region only, X=[54,69] per calculations.md
                     section 3 -- excludes the unrelated big_gear hub at X=[23,31]"}

expected_bounds is a positive allow-list (one box the contact must stay
inside); its negative complement is forbidden_regions (added 2026-08-21) --
a list of boxes a contact must NEVER touch, for when the legitimate contact
zone is awkward to bound tightly but a specific nearby feature must stay
untouched no matter what shape the legitimate zone takes:

    {"pair": ["bracket", "housing"], "joint_type": "press_fit",
     "expected_interference_mm": [0.05, 0.15],
     "forbidden_regions": [[[55.0, 0.0, 0.0], [61.0, 10.0, 10.0]]],
     "derivation": "press-fit boss only -- forbidden_regions excludes the
                     adjacent mounting-tab zone at X=[55,61], which must
                     never bear contact load per calculations.md section 5"}

expected_bounds and forbidden_regions are independent and combinable;
forbidden_regions is checked first, so a region caught by both is reported
as CONTACT IN FORBIDDEN REGION.

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
import json
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
        # Provenance requirement (added 2026-08-21, see INCIDENTS.md): a
        # declared expected_interference_mm range must not be a hand-typed
        # guess. Confirmed as a real failure mode in this skill's own
        # example project: an initial [0.0, 0.5]mm range was copied from an
        # earlier, unrelated press-fit test fixture rather than derived from
        # the actual gear geometry, and only corrected after measuring the
        # real penetration depth post-hoc. "derivation" doesn't have to be a
        # machine-evaluated expression (that's a larger, deferred piece of
        # work -- an influence graph, not a P0 change) -- it must be a
        # non-empty, human-written trace back to the source parameters this
        # range came from, so writing a plausible-looking number without
        # justification is at least visible in the declaration itself, not
        # silently indistinguishable from a properly derived one.
        if "expected_interference_mm" in entry:
            deriv = entry.get("derivation")
            if not isinstance(deriv, str) or not deriv.strip():
                print(
                    f"ERROR: contact {entry['pair']} declares "
                    f"expected_interference_mm but has no non-empty "
                    f"'derivation' field. State which source parameters "
                    f"and formula this range came from (e.g. "
                    f"\"gear addendum overlap at module=1, see calculations.md "
                    f"section 3\") -- a hand-typed range with no traceable "
                    f"origin is exactly how a wrong declaration goes "
                    f"unnoticed (INCIDENTS.md, 2026-08-21).",
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


def intersection_regions(mesh_a, mesh_b, noise_floor=0.5):
    """Split the boolean intersection of two meshes into disjoint connected
    regions, returning a list of {"volume": mm^3, "bounds": [[x,y,z],[x,y,z]]}
    for each region at or above noise_floor mm^3 (below that, a region is
    tessellation noise -- the same floor check_subfeature_overlap.py uses by
    default). None if no boolean engine is available or the computation
    fails; [] if the parts don't actually overlap.

    Why this exists: a single MAX-penetration-depth number over ALL contact
    points for a pair (pair_penetration_depth, above) cannot tell "one
    legitimate contact zone" from "a legitimate zone plus a completely
    separate, unrelated one" -- both can produce a similar shallow max
    depth. Confirmed as a real, live gap: a declared jackshaft/output_gear
    "gear_mesh" contact's overlap split into 7 disjoint regions, one of
    them (109.5mm^3) entirely outside the worm thread's own physical
    extent -- i.e. a real structural collision (plausibly the output gear's
    hub clipping the shaft's big_gear/transition region) hiding behind the
    same declared-range check as the legitimate worm-tooth mesh
    (INCIDENTS.md, 2026-08-19). A genuine single-purpose joint (a gear
    mesh, a press fit) physically touches in ONE contiguous region;
    multiple disjoint regions between the same declared pair is itself a
    signal nothing before this checked for.
    """
    try:
        inter = mesh_a.intersection(mesh_b)
    except Exception:
        return None
    if inter is None or inter.is_empty:
        return []
    try:
        pieces = inter.split(only_watertight=False)
    except Exception:
        return None

    regions = []
    for piece in pieces:
        try:
            vol = float(piece.volume)
        except Exception:
            continue
        # Same degenerate-near-zero handling as check_subfeature_overlap.py's
        # 2026-08-19 fix: a boolean engine can return a non-`is_volume`
        # (not watertight/consistently wound) sliver whose raw .volume is
        # still a trustworthy near-zero number. Only trust a non-`is_volume`
        # piece's number when it's small; a large one that fails `is_volume`
        # is genuinely unmeasurable, not evidence either way.
        if not piece.is_volume and abs(vol) >= 1.0:
            continue
        if abs(vol) < noise_floor:
            continue
        regions.append({"volume": vol, "bounds": piece.bounds.tolist()})
    return regions


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


def suggest_touch_stub(name_a, name_b):
    """Ready-to-paste joints.json contact entry for a candidate intentional
    touch (2026-08-19 Phase-2 Pattern 2, implemented 2026-08-22, see
    INCIDENTS.md) -- printed alongside the FAIL, not auto-written to
    joints.json, since only a human/agent can confirm the touch is
    actually intentional rather than a real defect that happens to be
    shallow. The placeholder derivation is deliberately obvious so it
    can't be pasted in and mistaken for a real one."""
    stub = {
        "pair": [os.path.splitext(os.path.basename(name_a))[0],
                 os.path.splitext(os.path.basename(name_b))[0]],
        "joint_type": "touching",
        "expected_interference_mm": [0.0, 0.0],
        "derivation": "AUTO-SUGGESTED by check_collisions.py -- REPLACE with the "
                       "real reason this touch is intentional before trusting it.",
    }
    return json.dumps(stub, indent=2)


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
    parser.add_argument("--touch-tolerance", type=float, default=0.05,
                        help="mm: an undeclared pair touching/overlapping within "
                             "this separation is classified as a CANDIDATE "
                             "INTENTIONAL TOUCH (gets a suggested joints.json stub) "
                             "instead of a plain interference report (default 0.05mm, "
                             "2026-08-19 Phase-2 Pattern 2)")
    parser.add_argument("--near-miss-tolerance", type=float, default=0.2,
                        help="mm: an undeclared, non-touching pair with a gap in "
                             "(touch-tolerance, this value] is flagged as a NEAR "
                             "MISS note -- NOT auto-suggested as intentional, since "
                             "this band is more often a real design sensitivity "
                             "than a benign touch (default 0.2mm)")
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
                # Clash classification (2026-08-19 Phase-2 Pattern 2,
                # implemented 2026-08-22): an undeclared overlap this
                # shallow is exactly the shape of a benign "kissing"
                # contact (e.g. a clamshell split line) that was correctly
                # reasoned about during design but never formalized as a
                # joints.json declaration (INCIDENTS.md, 2026-08-18,
                # gearbox_case_bottom/top) -- so rather than a bare FAIL,
                # print a ready-to-paste stub for a human/agent to confirm
                # or reject. Still a FAIL either way: nothing here is
                # auto-authorized. NOT implemented: a stability check that
                # re-renders with a jittered parameter to see if the
                # touch/overlap verdict flips (the Pattern 2 write-up's
                # own suggestion) -- that needs a real re-render per pair,
                # out of scope for a static post-hoc classifier.
                if depth is not None and depth <= args.touch_tolerance:
                    failures.append(
                        f"CANDIDATE INTENTIONAL TOUCH: {label}{extra} -- shallow "
                        f"enough (<= {args.touch_tolerance} mm) to plausibly be an "
                        f"intentional design touch (e.g. a split line) that was "
                        f"never declared. NOT auto-authorized -- confirm it's "
                        f"actually intentional, then add this to joints.json's "
                        f"\"contacts\":\n{suggest_touch_stub(a, b)}")
                else:
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
                    continue

                # Depth is within the declared range, but that alone doesn't
                # prove this is ONE legitimate contact -- a max-over-all-
                # contact-points depth can't distinguish that from a
                # legitimate zone plus a separate, unrelated one that
                # happens to be similarly shallow (confirmed live,
                # INCIDENTS.md 2026-08-19: a declared gear-mesh contact's
                # overlap split into 7 disjoint regions, one entirely
                # outside the meshing feature's own extent). A genuine
                # single-purpose joint touches in ONE contiguous region;
                # more than one is a red flag by default. Declare
                # "multi_region_ok": true on the contact entry for a joint
                # that legitimately touches in several places (e.g. a
                # splined shaft).
                regions = intersection_regions(meshes[a], meshes[b])
                multi_region_ok = bool(decl.get("multi_region_ok"))

                # Contact witness (added 2026-08-21, see INCIDENTS.md): a
                # declared contact should authorize only the SPECIFIC region
                # its own derivation describes, not "however many regions,
                # wherever they are" -- multi_region_ok alone only bounds the
                # COUNT, not the LOCATION, so a single unauthorized region
                # sitting exactly where a legitimate one is expected would
                # still pass unnoticed, and multi_region_ok:true would
                # silently accept an extra region ANYWHERE. Declaring
                # "expected_bounds": [[xmin,ymin,zmin],[xmax,ymax,zmax]] (in
                # the same assembly coordinate frame as the positioned STLs)
                # requires every detected region's bounds to fall inside
                # that box (with a small tessellation-noise margin); a
                # region outside it fails regardless of multi_region_ok or
                # how many regions there are in total.
                # forbidden_regions (P2, added 2026-08-21): the negative
                # complement of expected_bounds. expected_bounds requires
                # knowing the ONE tight allowed zone, which isn't always
                # practical to bound precisely (e.g. a large, irregular
                # legitimate contact area) -- forbidden_regions instead
                # names specific OTHER nearby features that must never be
                # part of this contact (e.g. a neighboring hub, a bearing
                # tower), without needing to bound the allowed zone tightly.
                # The two are independent and can be combined; either alone
                # is enough to catch a region in the wrong place.
                forbidden_regions = decl.get("forbidden_regions") or []
                if regions is not None and forbidden_regions:
                    hits = []
                    for r in regions:
                        (rx0, ry0, rz0), (rx1, ry1, rz1) = r["bounds"]
                        for fb in forbidden_regions:
                            (fx0, fy0, fz0), (fx1, fy1, fz1) = fb
                            # AABB overlap test: forbidden if the region's
                            # box intersects the forbidden box at all.
                            if (rx0 <= fx1 and rx1 >= fx0 and
                                    ry0 <= fy1 and ry1 >= fy0 and
                                    rz0 <= fz1 and rz1 >= fz0):
                                hits.append((r, fb))
                                break
                    if hits:
                        hit_list = "; ".join(
                            f"{r['volume']:.1f}mm^3 at {[[round(c, 1) for c in pt] for pt in r['bounds']]} "
                            f"overlaps forbidden {fb}"
                            for r, fb in hits)
                        failures.append(
                            f"CONTACT IN FORBIDDEN REGION: {label} is declared "
                            f"'{joint}', but touches inside a declared "
                            f"forbidden_regions box: {hit_list}. This zone was "
                            f"explicitly named as NOT part of this joint -- "
                            f"fix the position/size at the source.")
                        continue

                expected_bounds = decl.get("expected_bounds")
                if regions is not None and expected_bounds:
                    margin = 0.5  # mm, tessellation-noise allowance
                    (ex0, ey0, ez0), (ex1, ey1, ez1) = expected_bounds
                    unauthorized = []
                    for r in regions:
                        (rx0, ry0, rz0), (rx1, ry1, rz1) = r["bounds"]
                        if (rx0 < ex0 - margin or ry0 < ey0 - margin or rz0 < ez0 - margin or
                                rx1 > ex1 + margin or ry1 > ey1 + margin or rz1 > ez1 + margin):
                            unauthorized.append(r)
                    if unauthorized:
                        region_list = "; ".join(
                            f"{r['volume']:.1f}mm^3 at {[[round(c, 1) for c in pt] for pt in r['bounds']]}"
                            for r in unauthorized)
                        failures.append(
                            f"UNAUTHORIZED CONTACT REGION: {label} is declared "
                            f"'{joint}' with expected_bounds {expected_bounds}, "
                            f"but {len(unauthorized)} region(s) fall outside "
                            f"it: {region_list}. A declaration authorizes "
                            f"contact only where its own derivation says it "
                            f"should occur -- this looks like a real, "
                            f"unrelated collision, not the declared joint.")
                        continue

                if regions is not None and len(regions) > 1 and not multi_region_ok:
                    region_list = "; ".join(
                        f"{r['volume']:.1f}mm^3 at {[[round(c, 1) for c in pt] for pt in r['bounds']]}"
                        for r in regions)
                    failures.append(
                        f"MULTIPLE DISJOINT CONTACT REGIONS: {label} is "
                        f"declared '{joint}' as a single contact, but the "
                        f"overlap splits into {len(regions)} spatially "
                        f"separate regions: {region_list}. A single-purpose "
                        f"joint touches in one contiguous region -- this "
                        f"looks like a legitimate contact PLUS an unrelated "
                        f"structural collision hiding behind the same "
                        f"declared range. If this joint genuinely touches "
                        f"in several places on purpose, declare "
                        f"\"multi_region_ok\": true on this contact entry.")
                    continue

                vol_str = f", overlap volume {vol:.2f} mm^3" if vol is not None else ""
                region_note = (f", {len(regions)} contact region(s)"
                                if regions is not None else "")
                notes.append(
                    f"OK (intentional {joint}): {label}, penetration "
                    f"depth {depth:.3f} mm, declared range {lo}-{hi} mm"
                    f"{vol_str}{region_note}")
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

        # Always query distance for an undeclared, non-overlapping pair now
        # (2026-08-19 Phase-2 Pattern 2, implemented 2026-08-22): touch/
        # near-miss classification needs it regardless of whether
        # --min-clearance was passed -- previously this whole block, and
        # any visibility into a near-zero gap, was skipped entirely unless
        # the caller opted in with --min-clearance > 0.
        dist = pair_distance(meshes[a], meshes[b], a, b)
        if dist is None:
            notes.append(f"UNVERIFIED clearance: {label} (distance query failed)")
            degraded = True
        elif dist <= args.touch_tolerance:
            failures.append(
                f"CANDIDATE INTENTIONAL TOUCH: {label} gap {dist:.3f} mm -- close "
                f"enough (<= {args.touch_tolerance} mm) to plausibly be an "
                f"intentional design touch that was never declared. NOT "
                f"auto-authorized -- confirm it's actually intentional, then add "
                f"this to joints.json's \"contacts\":\n{suggest_touch_stub(a, b)}")
        elif args.min_clearance > 0.0 and dist < args.min_clearance:
            failures.append(
                f"INSUFFICIENT CLEARANCE: {label} gap {dist:.3f} mm "
                f"< required {args.min_clearance:.3f} mm")
        elif dist <= args.near_miss_tolerance:
            notes.append(
                f"NEAR MISS: {label} gap {dist:.3f} mm (<= "
                f"{args.near_miss_tolerance} mm) -- not failed, but this band is "
                f"more often a real design sensitivity than a benign touch, so "
                f"it's flagged rather than auto-suggested as intentional. Worth "
                f"a second look.")

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
    _exit = main()
    try:
        from validation_log import log_run, label_for_exit
        log_run("collisions", _exit, "check_collisions.py " + " ".join(sys.argv[1:]), label_for_exit(_exit))
    except Exception:
        pass
    sys.exit(_exit)
