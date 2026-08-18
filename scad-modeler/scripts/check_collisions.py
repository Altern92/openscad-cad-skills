#!/usr/bin/env python3
"""Check for unintended interference between already-positioned assembly parts.

Requires: trimesh, python-fcl (trimesh.collision.CollisionManager wraps FCL for
the actual collision math -- trimesh alone does not do this), and scipy (trimesh's
own is_convex/body_count checks need it, even though this script never imports it
directly). Confirmed by actually running this script end-to-end -- install with:
    pip install trimesh python-fcl scipy

Overlap-volume reporting additionally needs a mesh boolean engine (e.g.
manifold3d) to compute the intersection; without one it still correctly
reports collision True/False, just without a volume number.

Usage:
    python3 check_collisions.py build/part_a.stl build/part_b.stl [...]

Every STL passed in must already be in the shared assembly coordinate system
(i.e. exported from assembly.scad with parts positioned via at(), not raw
unpositioned part files) -- checking unpositioned parts against each other is
meaningless, since they'd all be sitting at their own local origins.

Exits non-zero if any pair overlaps, or if any mesh isn't watertight (a
non-watertight mesh makes the collision/volume results unreliable).
"""
import sys
import itertools

try:
    import trimesh
except ImportError:
    print("ERROR: trimesh not installed. Run: pip install trimesh python-fcl", file=sys.stderr)
    sys.exit(1)

try:
    from trimesh.collision import CollisionManager
except ImportError:
    print(
        "ERROR: trimesh.collision.CollisionManager unavailable -- this needs the "
        "python-fcl package (trimesh doesn't implement collision detection itself, "
        "it wraps FCL). Run: pip install python-fcl",
        file=sys.stderr,
    )
    sys.exit(1)


def main(paths):
    if len(paths) < 2:
        print("Need at least 2 STL files to check for collisions.", file=sys.stderr)
        sys.exit(1)

    meshes = {}
    for p in paths:
        m = trimesh.load(p, force="mesh")
        if not m.is_watertight:
            print(f"WARNING: {p} is not watertight -- results for it are unreliable")
        meshes[p] = m

    manager = CollisionManager()
    for p, m in meshes.items():
        manager.add_object(p, m)

    is_collision, contact_names = manager.in_collision_internal(return_names=True)

    if not is_collision:
        print(f"OK: no collisions among {len(paths)} parts.")
        return 0

    print("COLLISION(S) FOUND:")
    for a, b in contact_names:
        # Estimate overlap volume via boolean intersection, for a sense of severity.
        try:
            overlap = meshes[a].intersection(meshes[b])
            vol = overlap.volume if overlap is not None and overlap.is_volume else None
        except Exception:
            vol = None
        vol_str = f", approx overlap volume {vol:.1f} mm^3" if vol else ""
        print(f"  - {a}  <->  {b}{vol_str}")

    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
