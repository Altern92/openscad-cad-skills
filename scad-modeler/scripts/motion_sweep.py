#!/usr/bin/env python3
"""Interference checking through a motion cycle, not just one frozen pose.

check_collisions.py answers "is this assembled pose clear?". For anything that
moves -- a gearbox, hinge, latch, cam, slider -- that is close to meaningless:
parts can be clear at 0 degrees and interfere at 37. This sweeps the declared
motion and reports the worst configuration found.

WHAT IT DOES NOT PROVE
----------------------
Sampling, not a proof. Between two sampled positions the parts are not checked,
so a clash narrower than the step can be missed entirely. The adaptive pass
below refines around the tightest region, which finds narrow clashes near a
minimum, but a clash that is narrow AND far from the global minimum can still
slip through. Reduce --step-deg if the geometry has fine features; a tooth
flank is not resolved by a 5 degree step.

DECLARING MOTION
----------------
Extend the joints file (the same one check_collisions.py uses) from a bare list
of contacts to an object with both sections:

    {
      "contacts": [
        {"pair": ["shaft", "gear_1"], "joint_type": "press_fit",
         "expected_interference_mm": [0.02, 0.08]}
      ],
      "motion": [
        {
          "id": "gear_train",
          "drivers": [
            {"part": "gear_1", "type": "revolute",
             "axis": [0,0,1], "origin": [0,0,0], "ratio": 1.0, "teeth": 20},
            {"part": "gear_2", "type": "revolute",
             "axis": [0,0,1], "origin": [45,0,0], "ratio": -0.5, "teeth": 40}
          ],
          "range_deg": [0, 360],
          "step_deg": 2.0,
          "min_clearance_mm": 0.3
        }
      ]
    }

`ratio` is that part's motion per unit of the sweep parameter: a gear pair
meshing 20:40 turns at 1.0 and -0.5. Getting the sign wrong is the easy
mistake -- meshing external gears turn *opposite* ways, and a same-sign
pair produces a sweep that "passes" without proving anything about the
real mechanism. Checked automatically now (added 2026-09-04, see
check_gear_mesh_signs() below): for every declared `gear_mesh` contact
whose both parts are also drivers in the same motion block, this refuses
to even start sweeping unless their ratios have opposite, nonzero signs.
Declare a genuinely same-direction mesh (internal/planetary) with
`"joint_type": "internal_gear_mesh"` instead of `"gear_mesh"` to opt out.
For a `prismatic` driver, `ratio` is millimetres per degree of sweep parameter.

Parts named in `contacts` are swept too, but may overlap by up to the top of their
`expected_interference_mm` range (0.05 mm when none is given) at every position,
measured as the P16 bounded depth. A declared hinge therefore no longer hides a lid
that swings into its box (before 2026-11-01 such a pair was skipped and the sweep
passed with 0 positions checked). Parts not listed as drivers are static.

GEAR PERIODICITY
----------------
With `teeth` given for every driver, the configuration repeats after one tooth
pitch, so a 20-tooth gear needs 18 degrees of sweep rather than 360 -- a 20x
saving. This is applied only when every driver agrees on the period, which is
the case exactly when the gears actually mesh; otherwise the full range is
swept. Omit `teeth` to force the full range.

Requires: trimesh, python-fcl, scipy, numpy.

Usage:
    python3 motion_sweep.py --joints joints.json build/*.stl
    python3 motion_sweep.py --joints joints.json --step-deg 0.5 build/*.stl
    python3 motion_sweep.py --joints joints.json --json result.json build/*.stl

Exit codes:
    0  pass -- no interference and no clearance violation anywhere sampled
    2  degraded -- a mesh was not watertight, so results are unreliable
    3  fail -- interference or insufficient clearance at some position
    4  usage/runtime error
"""
import argparse
import itertools
import json
import math
import os
import sys

EXIT_OK, EXIT_DEGRADED, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4

try:
    import numpy as np
    import trimesh
    from trimesh.collision import CollisionManager
except ImportError as e:
    print(f"ERROR: missing dependency ({e}). "
          f"Run: pip install trimesh python-fcl scipy numpy", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def load_joints(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        print(f"ERROR: cannot read joints file {path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    if isinstance(data, list):          # the contacts-only format
        return [e for e in data if "pair" in e], []
    return data.get("contacts", []), data.get("motion", [])


def match_part(paths, name):
    """Resolve a declared part name to one of the STL paths."""
    name = str(name).lower()
    hits = [p for p in paths if name in os.path.basename(p).lower()]
    if len(hits) == 1:
        return hits[0]
    return None


def declared_entry(contacts, a, b):
    a, b = os.path.basename(a).lower(), os.path.basename(b).lower()
    for e in contacts:
        n1, n2 = (str(x).lower() for x in e["pair"])
        if (n1 in a and n2 in b) or (n1 in b and n2 in a):
            return e
    return None


def is_declared(contacts, a, b):
    return declared_entry(contacts, a, b) is not None


def allowed_depth(entry):
    """Overlap a declared contact may show at any sweep position: the top of its
    expected_interference_mm range (P8 agent eval, 2026-11-01). Before, a declared pair
    was never swept, so a hinged lid swinging INTO its box passed with 0 positions checked."""
    rng = entry.get("expected_interference_mm") if entry else None
    return float(rng[1]) + 0.01 if rng else 0.05


def transform_for(driver, t):
    """4x4 placement of a driven part at sweep parameter t (degrees)."""
    axis = np.array(driver.get("axis", [0, 0, 1]), dtype=float)
    n = np.linalg.norm(axis)
    if n == 0:
        raise ValueError(f"driver '{driver.get('part')}' has a zero-length axis")
    axis /= n
    ratio = float(driver.get("ratio", 1.0))
    T = np.eye(4)

    if driver.get("type", "revolute") == "prismatic":
        T[:3, 3] = axis * (ratio * t)
        return T

    ang = math.radians(ratio * t)
    c, s, C = math.cos(ang), math.sin(ang), 1 - math.cos(ang)
    x, y, z = axis
    R = np.array([
        [x * x * C + c,     x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, y * y * C + c,     y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, z * z * C + c],
    ])
    origin = np.array(driver.get("origin", [0, 0, 0]), dtype=float)
    T[:3, :3] = R
    T[:3, 3] = origin - R @ origin      # rotate about `origin`, not the world origin
    return T


def _name_matches(declared, driver_part):
    """Same case-insensitive substring convention as is_declared()/match_part(),
    applied to two plain declared-name strings instead of an STL path."""
    a, b = str(declared).lower(), str(driver_part).lower()
    return a in b or b in a


def check_gear_mesh_signs(contacts, motions):
    """Gear-ratio sign sanity check (added 2026-09-04, see INCIDENTS.md).
    This script's own docstring has always warned "getting the sign wrong
    is the easy mistake -- meshing external gears turn opposite ways," but
    nothing ever actually verified it: a same-sign ratio on a declared
    gear_mesh pair produces a sweep that never actually separates the two
    gears' relative motion the way real meshing teeth would, so "no
    interference found" from that sweep proves nothing about the real
    mechanism.

    For every declared 'gear_mesh' contact whose both members are ALSO
    drivers within the SAME motion block, requires opposite-sign, nonzero
    ratios (the correct relationship for external spur/helical gears).
    Scoped ONLY to joint_type == "gear_mesh" deliberately -- a worm_mesh's
    ratio relationship isn't a simple sign rule (it's a large reduction
    across non-parallel axes), and an internal/planetary mesh legitimately
    turns same-direction; neither should be flagged by this heuristic.

    Returns a list of human-readable failure strings (empty if nothing
    wrong).
    """
    failures = []
    for c in contacts:
        if str(c.get("joint_type", "")).lower() != "gear_mesh":
            continue
        pair = c.get("pair", [])
        if len(pair) != 2:
            continue
        name_a, name_b = pair
        for motion in motions:
            drivers = motion.get("drivers", [])
            driver_a = next((d for d in drivers if _name_matches(name_a, d.get("part", ""))), None)
            driver_b = next((d for d in drivers if _name_matches(name_b, d.get("part", ""))), None)
            if driver_a is None or driver_b is None:
                continue  # this gear_mesh pair isn't (both) driven in this motion block
            ratio_a = float(driver_a.get("ratio", 1.0))
            ratio_b = float(driver_b.get("ratio", 1.0))
            if ratio_a == 0.0 or ratio_b == 0.0:
                failures.append(
                    f"gear_mesh '{name_a}'<->'{name_b}' in motion '{motion.get('id', '?')}': "
                    f"one driver has ratio 0 (not actually driven) -- a gear_mesh pair "
                    f"where one side never moves relative to the other cannot mesh; check "
                    f"the ratio was set intentionally.")
            elif (ratio_a > 0) == (ratio_b > 0):
                failures.append(
                    f"gear_mesh '{name_a}'<->'{name_b}' in motion '{motion.get('id', '?')}': "
                    f"both drivers have SAME-sign ratio ({ratio_a}, {ratio_b}). External "
                    f"gears mesh in OPPOSITE rotational directions -- a same-sign ratio is "
                    f"almost always the sign gotten backwards, and the sweep below would "
                    f"prove nothing about a real collision between real meshing teeth. If "
                    f"this is a genuine internal/planetary mesh (same-direction by design), "
                    f"declare it with \"joint_type\": \"internal_gear_mesh\" instead of "
                    f"\"gear_mesh\" to opt out of this check.")
    return failures


def sweep_period(motion):
    """One tooth pitch of sweep parameter, or None if it doesn't apply.

    Driver i advances ratio_i*t degrees; its geometry repeats every 360/z_i of
    its own rotation, so the assembly repeats at t = 360/(|ratio_i|*z_i). For
    gears that genuinely mesh these agree; when they disagree the shortcut is
    unsound and the full range is swept instead.
    """
    periods = []
    for d in motion["drivers"]:
        z = d.get("teeth")
        if not z or d.get("type", "revolute") != "revolute":
            return None
        denom = abs(float(d.get("ratio", 1.0))) * float(z)
        if denom == 0:
            return None
        periods.append(360.0 / denom)
    if not periods:
        return None
    return periods[0] if max(periods) - min(periods) < 1e-6 * max(periods) else None


class Pairwise:
    """One FCL manager per pair, so a pair can be measured or skipped
    individually -- trimesh's internal check has no per-pair exemption."""

    def __init__(self, meshes, pairs, allow=None):
        self.mgr, self.pairs, self.meshes, self.allow = {}, pairs, meshes, allow or {}
        for a, b in pairs:
            m = CollisionManager()
            m.add_object(a, meshes[a])
            m.add_object(b, meshes[b])
            self.mgr[(a, b)] = m

    def evaluate(self, transforms):
        """Returns (worst_clearance, worst_pair, colliding_pairs)."""
        worst, worst_pair, colliding = float("inf"), None, []
        for (a, b), m in self.mgr.items():
            for name in (a, b):
                if name in transforms:
                    m.set_transform(name, transforms[name])
            if m.in_collision_internal():
                if (a, b) in self.allow and self.depth(a, b, transforms) <= self.allow[(a, b)]:
                    if 0.0 < worst:
                        worst, worst_pair = 0.0, (a, b)
                    continue
                colliding.append((a, b))
                worst, worst_pair = -1.0, (a, b)
                continue
            d = float(m.min_distance_internal())
            if d < worst:
                worst, worst_pair = d, (a, b)
        return worst, worst_pair, colliding

    def depth(self, a, b, transforms):
        """Penetration of a declared pair, bounded by the boolean intersection (P16)."""
        from check_collisions import bounded_depth
        ma, mb = self.meshes[a].copy(), self.meshes[b].copy()
        for name, mesh in ((a, ma), (b, mb)):
            if name in transforms:
                mesh.apply_transform(transforms[name])
        _, data = self.mgr[(a, b)].in_collision_internal(return_data=True)
        fcl = max((c.depth for c in data), default=0.0)
        return bounded_depth(fcl, ma, mb)


def run_motion(motion, meshes, paths, contacts, step_override, verbose=True):
    drivers = []
    for d in motion["drivers"]:
        p = match_part(paths, d["part"])
        if p is None:
            print(f"ERROR: driver part '{d['part']}' matches no STL "
                  f"(or matches several)", file=sys.stderr)
            return None
        drivers.append(dict(d, _path=p))

    moving = {d["_path"] for d in drivers}
    pairs = [(a, b) for a, b in itertools.combinations(sorted(meshes), 2)
             if a in moving or b in moving]
    allow = {(a, b): allowed_depth(declared_entry(contacts, a, b))
             for a, b in pairs if is_declared(contacts, a, b)}
    if not pairs:
        print(f"  '{motion.get('id', 'motion')}': nothing to check -- every pair "
              f"involving a moving part is a declared contact.")
        return {"id": motion.get("id"), "pass": True, "samples": 0}

    lo, hi = motion.get("range_deg", [0.0, 360.0])
    step = step_override or float(motion.get("step_deg", 2.0))
    min_clear = float(motion.get("min_clearance_mm", 0.0))

    period = sweep_period(motion)
    if period and period < (hi - lo):
        if verbose:
            z = [d.get("teeth") for d in drivers]
            print(f"  gear periodicity: sweeping {period:.3f}deg instead of "
                  f"{hi - lo:.0f}deg (teeth {z}) -- one tooth pitch repeats")
        hi = lo + period

    engine = Pairwise(meshes, pairs, allow)

    def sample(t):
        tf = {d["_path"]: transform_for(d, t) for d in drivers}
        return engine.evaluate(tf)

    steps = max(2, int(math.ceil((hi - lo) / step)) + 1)
    ts = [lo + i * (hi - lo) / (steps - 1) for i in range(steps)]
    results = [(t,) + sample(t) for t in ts]

    # Adaptive refinement: re-sample finely around the tightest sample, where a
    # clash narrower than the coarse step is most likely to be hiding.
    worst_i = min(range(len(results)), key=lambda i: results[i][1])
    span = (hi - lo) / (steps - 1)
    fine_lo = max(lo, results[worst_i][0] - span)
    fine_hi = min(hi, results[worst_i][0] + span)
    if fine_hi > fine_lo:
        for i in range(21):
            t = fine_lo + i * (fine_hi - fine_lo) / 20
            results.append((t,) + sample(t))

    results.sort(key=lambda r: r[0])
    worst = min(results, key=lambda r: r[1])
    clashes = [r for r in results if r[3]]
    violations = [r for r in results if not r[3] and r[1] < min_clear]

    ok = not clashes and not violations
    out = {
        "id": motion.get("id"), "pass": ok, "samples": len(results),
        "swept_deg": [lo, hi], "step_deg": step,
        "min_clearance_required_mm": min_clear,
        "worst": {"t_deg": round(worst[0], 4),
                  "clearance_mm": (None if worst[1] < 0 else round(worst[1], 4)),
                  "pair": [os.path.basename(x) for x in worst[2]] if worst[2] else None,
                  "interfering": worst[1] < 0},
        "clash_t_deg": [round(r[0], 3) for r in clashes],
        "violation_t_deg": [round(r[0], 3) for r in violations],
    }

    if verbose:
        label = motion.get("id", "motion")
        if ok:
            print(f"  PASS  '{label}': {len(results)} positions, worst clearance "
                  f"{worst[1]:.3f} mm at t={worst[0]:.2f}deg "
                  f"({' <-> '.join(out['worst']['pair'] or [])})")
        else:
            print(f"  FAIL  '{label}': {len(results)} positions")
            if clashes:
                a = out["clash_t_deg"]
                print(f"    interference at t = {a[0]}..{a[-1]}deg "
                      f"({len(a)} positions), e.g. "
                      f"{' <-> '.join(os.path.basename(x) for x in clashes[0][2])}")
            if violations:
                v = out["violation_t_deg"]
                print(f"    clearance below {min_clear} mm at t = {v[0]}..{v[-1]}deg "
                      f"({len(v)} positions); tightest {worst[1]:.3f} mm "
                      f"at t={worst[0]:.2f}deg")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stls", nargs="*")
    ap.add_argument("--joints", required=True)
    ap.add_argument("--step-deg", type=float, default=None,
                    help="override the declared step for every motion")
    ap.add_argument("--json", default=None, help="write the full result here")
    args = ap.parse_args()

    if len(args.stls) < 2:
        print("Need at least 2 STL files.", file=sys.stderr)
        return EXIT_USAGE

    contacts, motions = load_joints(args.joints)
    if not motions:
        print(f"No 'motion' section in {args.joints} -- nothing to sweep. "
              f"(check_collisions.py covers the static pose.)")
        return EXIT_OK

    bad = [m.get("id", f"#{i}") for i, m in enumerate(motions)
           if not isinstance(m.get("drivers"), list) or not m["drivers"]]
    if bad:
        print(f"FAIL: motion entry {', '.join(map(str, bad))} has no \"drivers\" list, so nothing "
              f"can be swept. Expected shape (see DECLARING MOTION in this script's --help):")
        print('  {"id": "lid_open", "range_deg": [0, 110], "step_deg": 2.0, "drivers": '
              '[{"part": "lid", "type": "revolute", "axis": [1, 0, 0], "origin": [0, 60, 20], "ratio": 1.0}]}')
        return EXIT_FAIL

    sign_failures = check_gear_mesh_signs(contacts, motions)
    if sign_failures:
        print("FAIL: gear-ratio sign check (before any sweep runs):")
        for f in sign_failures:
            print(f"  - {f}")
        print("Fix the ratio sign at the source -- do not sweep with a sign "
              "known to be wrong; the result would not mean anything.")
        return EXIT_FAIL

    meshes, degraded = {}, False
    for p in args.stls:
        try:
            m = trimesh.load(p, force="mesh")
        except Exception as e:
            print(f"ERROR: cannot load {p}: {e}", file=sys.stderr)
            return EXIT_USAGE
        if m.is_empty:
            print(f"ERROR: {p} contains no geometry.", file=sys.stderr)
            return EXIT_USAGE
        if not m.is_watertight:
            print(f"DEGRADED: {p} is not watertight -- results unreliable.")
            degraded = True
        meshes[p] = m

    print(f"Sweeping {len(motions)} motion(s) over {len(meshes)} parts:")
    out = []
    for motion in motions:
        r = run_motion(motion, meshes, args.stls, contacts, args.step_deg)
        if r is None:
            return EXIT_USAGE
        out.append(r)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"motions": out,
                       "pass": all(r["pass"] for r in out)}, f, indent=2)

    if not all(r["pass"] for r in out):
        print("\nFix at the source -- centre distance, backlash, or a layout "
              "position. Do not widen min_clearance_mm to make this pass.")
        print("Sampling caveat: a clash narrower than the step can be missed; "
              "lower --step-deg before concluding a design is clear.")
        return EXIT_FAIL
    if degraded:
        print("\nDEGRADED: no failures, but a mesh was not watertight. "
              "Treat as not checked.")
        return EXIT_DEGRADED
    print("\nOK: no interference or clearance violation at any sampled position.")
    return EXIT_OK


if __name__ == "__main__":
    _exit = main()
    try:
        from validation_log import log_run, label_for_exit
        log_run("motion_sweep", _exit, "motion_sweep.py " + " ".join(sys.argv[1:]), label_for_exit(_exit))
    except Exception:
        pass
    sys.exit(_exit)
