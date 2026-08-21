#!/usr/bin/env python3
"""Overlap check BETWEEN named sub-features inside a single printed part.

`check_collisions.py` only ever compares separately-exported STLs against
each other -- once two named sub-modules (a tower, a wall, a boss) are
union()-ed together and exported as one part, they no longer exist as
distinguishable objects, so an overlap between them, however large, cannot
be flagged: union() of two overlapping solids is still one valid,
watertight, single-body shell. Confirmed: a bearing tower overlapped an
unrelated motor-mounting cradle in the same part by 419mm^3, invisible
through several rounds of "all green" validation because both were part of
one part's union() (INCIDENTS.md, 2026-08-19).

This checks overlap volume between sub-features BEFORE union: export each
named sub-module of a part as its own solo STL (same local coordinate
system, not yet combined), and this script checks every pair for
unintended interference.

Declare intentional fusions (a boss meant to blend into the tower it
mounts on) in a JSON file passed with --exempt, the same way
check_collisions.py's --expected-contacts declares intentional contact
between separate parts -- silently excluding a pair is not an option, it
must be a written decision:

    [
      {"pair": ["boss_a", "tower_main"], "reason": "boss blends into tower"}
    ]

Names are matched case-insensitively against each STL's basename (substring
match), same convention as check_collisions.py.

Requires: trimesh, and a mesh boolean engine (e.g. manifold3d) for volume
measurement -- without one, overlap cannot be quantified and this reports
degraded, not passed. Install with:
    pip install trimesh manifold3d

Usage:
    python3 check_subfeature_overlap.py sub_features/*.stl
    python3 check_subfeature_overlap.py --max-overlap-mm3 0.5 sub_features/*.stl
    python3 check_subfeature_overlap.py --exempt fusions.json sub_features/*.stl

Exit codes:
    0  pass -- no un-exempted pair overlaps beyond the threshold.
    2  degraded -- no mesh boolean engine available, so overlap volume could
       not be measured for at least one pair. Treat as not checked.
    3  fail -- an un-exempted pair overlaps beyond --max-overlap-mm3.
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
    print("ERROR: trimesh not installed. Run: pip install trimesh manifold3d",
          file=sys.stderr)
    sys.exit(EXIT_USAGE)


def load_exempt(path):
    if not path:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read exempt file {path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if isinstance(data, dict):
        data = data.get("exempt", [])
    if not isinstance(data, list):
        print(f"ERROR: {path} must contain a JSON list of exemptions, or an "
              f"object with an \"exempt\" list.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    for entry in data:
        if "pair" not in entry or len(entry.get("pair", [])) != 2:
            print(f"ERROR: exempt entry missing a 2-element 'pair': {entry}",
                  file=sys.stderr)
            sys.exit(EXIT_USAGE)
    return data


def is_exempt(exempt, path_a, path_b):
    a = os.path.basename(path_a).lower()
    b = os.path.basename(path_b).lower()
    for entry in exempt:
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
        vol = float(inter.volume)
    except Exception:
        return None
    # A near-zero (but non-empty) intersection -- two parts that barely
    # touch or don't quite overlap -- often comes back from the boolean
    # engine as a degenerate sliver that fails is_volume (not watertight/
    # consistently wound), even though its own .volume is a trustworthy
    # near-zero number. Confirmed manually (2026-08-19): a pair the engine
    # flagged as unmeasurable this way had a real .intersection().volume
    # of exactly 0.0 when computed directly, outside this script. Only
    # fall back to "unmeasurable" for a substantial volume, where a
    # degenerate mesh's number can't be trusted; small volumes are safe
    # either way since a genuine failure there wouldn't matter at
    # --max-overlap-mm3 scale.
    if inter.is_volume or abs(vol) < 1.0:
        return vol
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stls", nargs="*", help="solo-exported sub-feature STLs "
                                                  "(pre-union, shared local coords)")
    parser.add_argument("--max-overlap-mm3", type=float, default=0.5,
                         help="overlap volume above this fails (default 0.5 mm^3, "
                              "-- tessellation noise floor, not zero)")
    parser.add_argument("--exempt", default=None,
                         help="JSON file declaring intentionally-fused pairs")
    args = parser.parse_args()

    paths = args.stls
    if len(paths) < 2:
        print("Need at least 2 sub-feature STLs to check for overlap.",
              file=sys.stderr)
        return EXIT_USAGE

    exempt = load_exempt(args.exempt)

    meshes = {}
    for p in paths:
        try:
            m = trimesh.load(p, force="mesh")
        except Exception as e:
            print(f"ERROR: cannot load {p}: {e}", file=sys.stderr)
            return EXIT_USAGE
        if m.is_empty:
            print(f"ERROR: {p} contains no geometry.", file=sys.stderr)
            return EXIT_USAGE
        meshes[p] = m

    failures = []
    notes = []
    degraded = False

    for a, b in itertools.combinations(paths, 2):
        label = f"{os.path.basename(a)} <-> {os.path.basename(b)}"
        vol = overlap_volume(meshes[a], meshes[b])
        decl = is_exempt(exempt, a, b)

        if vol is None:
            notes.append(f"UNVERIFIED: {label} -- no mesh boolean engine available "
                         f"to measure overlap (pip install manifold3d)")
            degraded = True
            continue

        if vol <= args.max_overlap_mm3:
            continue

        if decl is not None:
            notes.append(f"OK (exempt, {decl.get('reason', 'declared fusion')}): "
                         f"{label}, overlap {vol:.2f} mm^3")
            continue

        failures.append(
            f"UNINTENDED SUB-FEATURE OVERLAP: {label}, {vol:.2f} mm^3 "
            f"(threshold {args.max_overlap_mm3:.2f} mm^3)")

    for n in notes:
        print(f"  {n}")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        print("Fix at the source -- reposition or resize the offending "
              "sub-feature. If the overlap is an intentional fusion (e.g. a "
              "boss meant to blend into a tower), declare it with --exempt "
              "instead of raising --max-overlap-mm3 to silence a real one.")
        return EXIT_FAIL

    if degraded:
        print("DEGRADED: no un-exempted overlap found, but some pairs could not "
              "be measured. Treat as not checked.")
        return EXIT_DEGRADED

    print(f"OK: no unintended overlap among {len(paths)} sub-features "
          f"(threshold {args.max_overlap_mm3:.2f} mm^3).")
    return EXIT_OK


if __name__ == "__main__":
    _exit = main()
    try:
        from validation_log import log_run, label_for_exit
        log_run("subfeature_overlap", _exit, "check_subfeature_overlap.py " + " ".join(sys.argv[1:]), label_for_exit(_exit))
    except Exception:
        pass
    sys.exit(_exit)
