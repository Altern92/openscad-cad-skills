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

END STOPS (P28, 2026-11-28)
---------------------------
"stops": {"ends": ["high"], "within_deg": 5} in a motion block: past that end of range_deg the parts
must touch (<= 0.05 mm) or interfere within within_deg, else FAIL -- the declared range is otherwise a
promise nothing physical enforces. The first touching angle is printed.

GROUPS AND ASSIGNMENT (P21, 2026-11-14)
---------------------------------------
A machine axis moves many parts as one body (gantry: side plates, beam, drive, carriage).
Name them, do not select them by bounding box -- a bbox silently dropped a Z drive from its
group and the sweep reported a false 1.2 mm (INC-2026-11-13-05):

    {"static": ["frame", "home_sensor"],
     "motion": [{"id": "x_axis", "range_deg": [0, 650], "step_deg": 10,
                 "drivers": [{"parts": ["x_carriage", "z_plate", "z_motor"],
                              "type": "prismatic", "axis": [1, 0, 0], "ratio": 1.0}]}]}

`"parts"` moves every listed part with one transform; pairs inside one group are not checked
against each other (they are bolted together). Once a top-level `"static"` list exists, every
STL must be named by some driver or by `static`, otherwise FAIL before any sweep: a part added
later and never assigned is exactly the one that hides a collision. Without `"static"` the old
behaviour stays (unnamed parts are static) and a NOTE says so.

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
    __import__("mesh_python").reexec()
    print(f"ERROR: missing dependency ({e}). "
          f"Run: bash scripts/setup_env.sh", file=sys.stderr)
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


def expand_groups(motions):
    """{"parts": [a, b]} -> one driver per part, all sharing a group id (P21)."""
    for mi, m in enumerate(motions):
        out = []
        for di, d in enumerate(m.get("drivers") or []):
            if isinstance(d.get("parts"), list) and "part" not in d:
                g = f"{mi}.{di}"
                out += [dict({k: v for k, v in d.items() if k != "parts"}, part=n, _group=g) for n in d["parts"]]
            else:
                out.append(d)
        if out:
            m["drivers"] = out
    return motions


def unassigned(paths, motions, static):
    """STLs no driver and no static entry names, plus declared names matching no STL."""
    names = [d.get("part", "") for m in motions for d in m.get("drivers", [])] + list(static)
    # P26 / AC-3b: exact names -- "wheel" must not cover the mirror copy wheel_l
    want = {str(n).lower() for n in names if n}
    loose = [p for p in paths if os.path.splitext(os.path.basename(p))[0].lower() not in want]
    dead = [n for n in static if match_part(paths, n) is None]
    return loose, dead


def match_part(paths, name):
    """Resolve a declared part name to one of the STL paths."""
    name = str(name).lower()
    hits = [p for p in paths if os.path.splitext(os.path.basename(p))[0].lower() == name]
    if len(hits) == 1:
        return hits[0]
    return None


def declared_entry(contacts, a, b):
    stem = lambda p: os.path.splitext(os.path.basename(p))[0].lower()
    a, b = stem(a), stem(b)
    for e in contacts:  # exact part names (P26 / AC-3)
        n1, n2 = (str(x).lower() for x in e["pair"])
        if (n1 == a and n2 == b) or (n1 == b and n2 == a):
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


def symmetric_under(mesh, driver, period, tol=0.1, n=3000):
    """True when the part's surface maps onto itself after turning by one period (within tol mm)."""
    # P27b: every vertex too -- 3000 random samples missed a 1x1x2 mm nub on a 120 mm disc; any feature has vertices
    smp = trimesh.sample.sample_surface(mesh, n, seed=0)[0] if "seed" in trimesh.sample.sample_surface.__code__.co_varnames \
        else trimesh.sample.sample_surface(mesh, n)[0]
    pts = np.vstack([mesh.vertices, smp])
    T = transform_for(driver, period)
    moved = trimesh.transform_points(pts, T)
    _, dist, _ = trimesh.proximity.closest_point(mesh, moved)
    return float(np.max(dist)) <= tol


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
    """Same case-insensitive exact-name convention as match_part() (P26 / AC-3b)."""
    return str(declared).lower() == str(driver_part).lower()


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
                    f"the ratio was set intentionally. Hint: give the driver a non-zero ratio in joints.json.")
            elif (ratio_a > 0) == (ratio_b > 0):
                failures.append(
                    f"gear_mesh '{name_a}'<->'{name_b}' in motion '{motion.get('id', '?')}': "
                    f"both drivers have SAME-sign ratio ({ratio_a}, {ratio_b}). External "
                    f"gears mesh in OPPOSITE rotational directions -- a same-sign ratio is "
                    f"almost always the sign gotten backwards, and the sweep below would "
                    f"prove nothing about a real collision between real meshing teeth. If "
                    f"this is a genuine internal/planetary mesh (same-direction by design), "
                    f"declare it with \"joint_type\": \"internal_gear_mesh\" instead of "
                    f"\"gear_mesh\" to opt out of this check. Hint: flip the sign of one driver's ratio in joints.json.")
    return failures


AXIS_TOL_MM = 0.05      # P29: a gear 0.05 mm off its axis or its centre distance already changes backlash


def _unit(v):
    v = np.array(v, dtype=float)
    return v / np.linalg.norm(v)


def _bosl2_gear_dist(mod, z1, z2, pressure_angle, ps1, ps2, helical=0.0):
    """BOSL2 gear_dist() via OpenSCAD; ps None = BOSL2's auto profile shift. Returns (mm, error)."""
    import shutil, subprocess, tempfile
    exe = os.environ.get("OPENSCAD") or shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
    kw = f"mod={mod}, teeth1={z1}, teeth2={z2}, pressure_angle={pressure_angle}, helical={helical}"
    if ps1 is not None:
        kw += f", profile_shift1={ps1}, profile_shift2={ps2}"
    with tempfile.TemporaryDirectory() as d:
        src, out = os.path.join(d, "g.scad"), os.path.join(d, "g.echo")
        with open(src, "w") as f:
            f.write("include <BOSL2/std.scad>\ninclude <BOSL2/gears.scad>\n"
                    f"echo(P29_DIST=gear_dist({kw}));\n")
        try:
            subprocess.run([exe, "-o", out, src], capture_output=True, timeout=120)
            txt = open(out).read()
        except Exception as e:
            return None, str(e)
    for line in txt.splitlines():
        if "P29_DIST" in line:
            try:
                return float(line.split("=")[-1]), None
            except ValueError:
                return None, line.strip()
    return None, "no gear_dist echo (BOSL2 missing?)"


def _bosl2_echo(expr):
    """Evaluate one BOSL2 expression via OpenSCAD echo. Returns (float, error)."""
    import shutil, subprocess, tempfile
    exe = os.environ.get("OPENSCAD") or shutil.which("openscad") or "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
    with tempfile.TemporaryDirectory() as d:
        src, out = os.path.join(d, "g.scad"), os.path.join(d, "g.echo")
        with open(src, "w") as f:
            f.write(f"include <BOSL2/std.scad>\ninclude <BOSL2/gears.scad>\necho(P32_VAL={expr});\n")
        try:
            subprocess.run([exe, "-o", out, src], capture_output=True, timeout=120)
            txt = open(out).read()
        except Exception as e:
            return None, str(e)
    for line in txt.splitlines():
        if "P32_VAL" in line:
            try:
                return float(line.split("=")[-1]), None
            except ValueError:
                return None, line.strip()
    return None, "no echo (BOSL2 missing?)"


def _axis_geometry(e1, e2):
    """Common-normal distance (mm) and the angle (deg, 0..90) between two axis lines."""
    n = np.cross(e1["dir"], e2["dir"])
    sin = float(np.linalg.norm(n))
    angle = math.degrees(math.asin(min(1.0, sin)))
    if float(e1["dir"] @ e2["dir"]) < 0:
        angle = 180.0 - angle
    dist = abs(float((e2["point"] - e1["point"]) @ n)) / sin if sin > 1e-9 else float("nan")
    return dist, angle


def _check_kind_pair(c, kind, n1, n2, e1, e2, failures, notes, usage):
    """P32 AC-G1/G2: bevel (axes intersect, shaft angle) and worm (perpendicular, worm_dist()) contacts."""
    dist, ang = _axis_geometry(e1, e2)
    src = "measured axes" if e1["measured"] and e2["measured"] else "declared origin(s)"
    ang = min(ang, 180.0 - ang)   # axis lines, not directed vectors
    if kind == "bevel":
        try:
            sa = float(c.get("shaft_angle", 90))
        except (TypeError, ValueError):
            usage.append(f"gear_mesh {n1}<->{n2}: \"shaft_angle\" must be a number")
            return
        sa = min(sa, 180.0 - sa)
        if not dist == dist:   # parallel axes never meet at a shaft angle
            failures.append(f"bevel axes {n1}<->{n2}: parallel axes ({src}); shaft angle {sa:g} deg declared -- Hint: tilt one gear axis (driver axis + part rotation) to the declared shaft angle")
        elif dist > AXIS_TOL_MM:
            failures.append(f"bevel axes {n1}<->{n2}: axes do not intersect, {dist:.3f} mm apart ({src}), limit "
                            f"{AXIS_TOL_MM} mm -- both pitch-cone apexes must sit at the axes' intersection -- Hint: move one gear so the axes meet")
        elif abs(ang - sa) > 0.1:
            failures.append(f"bevel axes {n1}<->{n2}: shaft angle is {ang:.2f} deg ({src}), declared {sa:g} deg "
                            f"(+-0.1 deg) -- Hint: rotate one gear's axis to the declared shaft angle, or correct shaft_angle in joints.json")
        else:
            notes.append(f"OK: bevel axes {n1}<->{n2} intersect ({dist:.3f} mm) at {ang:.2f} deg ({src}), declared {sa:g} deg")
        return
    # worm: the worm is the "worm" part named in the contact, default first of the pair; its "teeth" = starts
    try:
        mod, pa = float(c["module"]), float(c.get("pressure_angle", 20))
        d_w, ps = float(c["worm_diam"]), float(c.get("profile_shift", 0))
    except (KeyError, TypeError, ValueError):
        usage.append(f"gear_mesh {n1}<->{n2} kind worm: needs numeric \"module\" and \"worm_diam\" (worm pitch diameter, mm); "
                     f"\"pressure_angle\" and a numeric \"profile_shift\" are optional")
        return
    w, g = (e1, e2) if str(c.get("worm", n1)).lower() == n1 else (e2, e1)
    want, err = _bosl2_echo(f"worm_dist(d={d_w}, starts={w['teeth']}, teeth={g['teeth']}, mod={mod}, "
                            f"profile_shift={ps}, pressure_angle={pa})")
    if abs(ang - 90.0) > 0.1:
        failures.append(f"worm axes {n1}<->{n2}: not perpendicular, {ang:.2f} deg ({src}); worm and worm gear need 90 deg +-0.1 -- Hint: rotate the worm or worm gear so their axes are perpendicular")
    elif want is None:
        notes.append(f"NOT CHECKED: worm centre distance {n1}<->{n2} -- worm_dist() unavailable ({err})")
        return True   # degraded, like the spur gear_dist() path
    elif abs(dist - want) > AXIS_TOL_MM:
        failures.append(f"worm centre distance {n1}<->{n2}: common normal is {dist:.3f} mm ({src}), BOSL2 worm_dist("
                        f"d {d_w:g}, {w['teeth']} start(s), {g['teeth']}T, module {mod:g}, profile shift {ps:g}) = "
                        f"{want:.3f} mm ({dist - want:+.3f} mm) -- Hint: move the worm to the worm_dist() centre distance in the layout")
    else:
        notes.append(f"OK: worm centre distance {n1}<->{n2} {dist:.3f} mm ({src}) = worm_dist() {want:.3f} mm, axes 90 deg")


def check_gear_axes(contacts, motions, meshes, paths):
    """P29 (2026-11-27): a toothed driver must turn about the part's real axis, and a gear_mesh with
    "module" must sit at BOSL2 gear_dist(). Real case: examples/gear_reduction sat 0.345 mm too close
    (11T pinion auto profile shift ignored) and a spur moved a further 1.2 mm in the layout -- the sweep
    still rotated it about the stale joints.json origin and passed. P29b (fresh review): the distance is
    measured between the REAL axes when known, a gear whose axis cannot be measured still gets its
    centre distance checked from the declared origins, direction is checked too, and every gear_mesh
    that is not checked says why. Returns (failures, notes, degraded, usage_errors)."""
    failures, notes, usage, degraded = [], [], [], False
    axes = {}   # (motion id, part) -> dict(point, dir, teeth, measured)
    worms = {str(c.get("worm", (c.get("pair") or [""])[0])).lower() for c in contacts
             if str(c.get("kind", "")).lower() == "worm"}   # helical: no symmetry axis to measure from the mesh
    for mi, motion in enumerate(motions):
        mid = motion.get("id", f"#{mi}")
        for d in motion.get("drivers", []):
            z = d.get("teeth")
            if not z or d.get("type", "revolute") != "revolute":
                continue
            name = str(d.get("part", "")).lower()
            a, o = _unit(d.get("axis", [0, 0, 1])), np.array(d.get("origin", [0, 0, 0]), float)
            entry = {"point": o, "dir": a, "teeth": int(z), "measured": False}
            axes[(mid, name)] = entry
            path = match_part(paths, d.get("part", ""))
            if name in worms:
                # helical: no tooth-pitch symmetry; instead the mesh bbox centre of a (rotationally symmetric) worm
                # must lie on the declared axis, else the STL moved while joints.json kept the old origin
                if path is not None and path in meshes:
                    cen = (meshes[path].bounds[0] + meshes[path].bounds[1]) / 2 - o
                    off = float(np.linalg.norm(cen - np.dot(cen, a) * a))
                    if off > AXIS_TOL_MM:
                        failures.append(f"axis: worm '{d['part']}' in motion '{mid}': its mesh centre is {off:.3f} mm "
                                        f"off the declared axis (limit {AXIS_TOL_MM} mm). The layout and joints.json "
                                        f"disagree -- fix the one that is wrong. Hint: move the part onto the declared axis, or correct origin in joints.json.")
                        continue
                notes.append(f"NOT CHECKED: tooth-pitch symmetry of '{d['part']}' -- a worm has none; its axis is the "
                             f"declared one, checked only against its mesh bbox centre")
                continue
            if path is None or path not in meshes:
                notes.append(f"NOT CHECKED: axis of '{d['part']}' -- no single STL named like it")
                continue
            mesh = meshes[path]
            entry["mesh"] = mesh
            radius = float(np.max(np.linalg.norm(np.cross(mesh.vertices - mesh.center_mass, a), axis=1)))
            # direction: the inertia axis nearest the declared one (a gear's symmetry axis is a principal axis)
            vals, vecs = mesh.principal_inertia_components, mesh.principal_inertia_vectors
            k = int(np.argmax(np.abs(vecs @ a)))
            others = [v for i, v in enumerate(vals) if i != k]
            distinct = min(abs(vals[k] - v) for v in others) > 1e-3 * max(abs(vals[k]), 1e-9)
            if distinct:
                tilt = math.degrees(math.acos(min(1.0, abs(float(vecs[k] @ a)))))
                rim = radius * math.sin(math.radians(tilt))
                if rim > AXIS_TOL_MM:
                    failures.append(f"axis: driver '{d['part']}' in motion '{mid}' declares axis "
                                    f"{list(np.round(a, 4))}, but the part's symmetry axis is tilted {tilt:.2f} deg "
                                    f"from it ({rim:.3f} mm at its rim). Hint: fix the part's rotation or the driver axis in joints.json.")
                    continue
            rel = mesh.center_mass - o
            off = rel - np.dot(rel, a) * a
            probe = dict(d, origin=list(o + off), ratio=1.0)
            if not symmetric_under(mesh, probe, 360.0 / float(z)):
                notes.append(f"NOT CHECKED: axis of '{d['part']}' -- not symmetric under one tooth pitch about the "
                             f"declared axis through its centre of mass (keyway, flat, hub feature -- or a wrong "
                             f"axis direction); its centre distance below uses the declared origin")
                continue
            dist = float(np.linalg.norm(off))
            if dist > AXIS_TOL_MM:
                failures.append(f"axis: driver '{d['part']}' in motion '{mid}' turns about "
                                f"{list(np.round(o, 3))}, but the part's real axis is {dist:.3f} mm away (through "
                                f"{list(np.round(o + off, 3))}). The layout and joints.json disagree -- fix the one "
                                f"that is wrong; the sweep would rotate the part about a point it does not turn on. "
                                f"Hint: correct the driver origin in joints.json to the part's real axis, or move the part.")
            entry.update(point=o + off, measured=True)
    for c in contacts:
        if str(c.get("joint_type", "")).lower() != "gear_mesh" or len(c.get("pair", [])) != 2:
            continue
        n1, n2 = (str(x).lower() for x in c["pair"])
        pairs = [(axes[(m, n1)], axes[(m, n2)]) for (m, n) in list(axes) if n == n1 and (m, n2) in axes]
        if not pairs:
            notes.append(f"NOT CHECKED: centre distance {n1}<->{n2} -- both need a revolute driver with \"teeth\" "
                         f"in the same motion block")
            continue
        kind = str(c.get("kind", "")).lower()
        if kind in ("bevel", "worm"):
            for e1, e2 in pairs:
                degraded |= bool(_check_kind_pair(c, kind, n1, n2, e1, e2, failures, notes, usage))
            continue
        if kind:
            usage.append(f"gear_mesh {n1}<->{n2}: \"kind\" must be \"bevel\" or \"worm\", got {c['kind']!r}")
            continue
        if "module" not in c:
            notes.append(f"NOT CHECKED: centre distance {n1}<->{n2} -- the gear_mesh contact has no \"module\"")
            continue
        ps = c.get("profile_shift", "auto")
        if ps == "auto":
            ps1 = ps2 = None
        elif isinstance(ps, list) and len(ps) == 2 and all(isinstance(x, (int, float)) for x in ps):
            ps1, ps2 = float(ps[0]), float(ps[1])
        else:
            usage.append(f"gear_mesh {n1}<->{n2}: \"profile_shift\" must be \"auto\" or [x1, x2], got {ps!r}")
            continue
        try:
            mod, pa, hel = float(c["module"]), float(c.get("pressure_angle", 20)), float(c.get("helical", 0))
        except (TypeError, ValueError):
            usage.append(f"gear_mesh {n1}<->{n2}: \"module\", \"pressure_angle\" and \"helical\" must be numbers")
            continue
        for e1, e2 in pairs:
            if abs(float(e1["dir"] @ e2["dir"])) < math.cos(math.radians(0.1)):
                notes.append(f"NOT CHECKED: centre distance {n1}<->{n2} -- the axes are not parallel "
                             f"(bevel/crossed gears are not spur gear_dist())")
                continue
            want, err = _bosl2_gear_dist(mod, e1["teeth"], e2["teeth"], pa, ps1, ps2, hel)
            if want is None:
                notes.append(f"NOT CHECKED: centre distance {n1}<->{n2} -- gear_dist() unavailable ({err})")
                degraded = True
                continue
            rel = e2["point"] - e1["point"]
            have = float(np.linalg.norm(rel - np.dot(rel, e1["dir"]) * e1["dir"]))
            src = "measured axes" if e1["measured"] and e2["measured"] else "declared origin(s)"
            if abs(have - want) > AXIS_TOL_MM:
                failures.append(f"centre distance {n1}<->{n2}: axes are {have:.3f} mm apart ({src}), BOSL2 "
                                f"gear_dist(module {mod}, {e1['teeth']}T/{e2['teeth']}T, profile shift {ps}, "
                                f"helical {hel}) = {want:.3f} mm ({have - want:+.3f} mm). Take the distance from "
                                f"gear_dist(), not m*(z1+z2)/2 (BOSL2 shifts small pinions automatically). Hint: move one gear to the gear_dist() centre distance in the layout.")
            else:
                notes.append(f"OK: centre distance {n1}<->{n2} {have:.3f} mm ({src}) = gear_dist() {want:.3f} mm")
            # Audit A1 (2026-11-28): centre distance is radial only; a gear lifted past its partner's face still
            # "meshes" by distance. Compare the axial extents of the tooth-tip zones (radius within one module of the tip).
            if "mesh" not in e1 or "mesh" not in e2:
                notes.append(f"NOT CHECKED: face overlap {n1}<->{n2} -- a gear has no single STL")
                continue
            spans = []
            for e in (e1, e2):
                v = e["mesh"].vertices - e["point"]
                r = np.linalg.norm(v - np.outer(v @ e1["dir"], e1["dir"]), axis=1)
                z = (e["mesh"].vertices @ e1["dir"])[r >= r.max() - mod]
                spans.append((float(z.min()), float(z.max())))
            ov = min(spans[0][1], spans[1][1]) - max(spans[0][0], spans[1][0])
            need = float(c.get("min_face_overlap_mm", min(b - a for a, b in spans)))
            if ov < need - AXIS_TOL_MM:
                failures.append(f"face overlap {n1}<->{n2}: the teeth share {max(ov, 0.0):.3f} mm of face width along the axis "
                                f"(tooth zones {spans[0][0]:.2f}..{spans[0][1]:.2f} and {spans[1][0]:.2f}..{spans[1][1]:.2f} mm), "
                                f"need {need:.3f} mm (the narrower face; set \"min_face_overlap_mm\" for a deliberate partial mesh). "
                                "Hint: align the gears along their axis in the layout.")
            else:
                notes.append(f"OK: face overlap {n1}<->{n2} {ov:.3f} mm (need {need:.3f})")
    return failures, notes, degraded, usage


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

    def __init__(self, meshes, pairs, allow=None, req=None, default_req=0.0):
        self.mgr, self.pairs, self.meshes, self.allow = {}, pairs, meshes, allow or {}
        self.req, self.default_req = req or {}, default_req
        for a, b in pairs:
            m = CollisionManager()
            m.add_object(a, meshes[a])
            m.add_object(b, meshes[b])
            self.mgr[(a, b)] = m

    def need(self, pair):
        return self.req.get(pair, self.default_req)

    def evaluate(self, transforms):
        """Returns (worst_clearance, worst_pair, colliding_pairs); worst = smallest margin over each pair's
        own required clearance (P27b: a declared contact may state its own, else the motion's applies)."""
        worst, worst_pair, colliding, margin = float("inf"), None, [], float("inf")
        for (a, b), m in self.mgr.items():
            for name in (a, b):
                if name in transforms:
                    m.set_transform(name, transforms[name])
            if m.in_collision_internal():
                if (a, b) in self.allow and self.depth(a, b, transforms) <= self.allow[(a, b)]:
                    d = 0.0          # overlap within its declared range: clearance 0
                else:
                    colliding.append((a, b))
                    worst, worst_pair, margin = -1.0, (a, b), -float("inf")
                    continue
            else:
                d = float(m.min_distance_internal())
            if d - self.need((a, b)) < margin:
                worst, worst_pair, margin = d, (a, b), d - self.need((a, b))
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
    group = {d["_path"]: d["_group"] for d in drivers if "_group" in d}
    pairs = [(a, b) for a, b in itertools.combinations(sorted(meshes), 2)
             if (a in moving or b in moving) and not (a in group and group.get(b) == group[a])]
    allow = {(a, b): allowed_depth(declared_entry(contacts, a, b))
             for a, b in pairs if is_declared(contacts, a, b)}
    # P27b (Fable review): exempting every declared pair from min_clearance_mm hid near-misses elsewhere
    # on the same two bodies. A declared contact keeps the motion's clearance unless it states its own.
    req = {(a, b): float(declared_entry(contacts, a, b)["min_clearance_mm"])
           for a, b in pairs if is_declared(contacts, a, b) and "min_clearance_mm" in declared_entry(contacts, a, b)}
    if not pairs:
        print(f"  '{motion.get('id', 'motion')}': nothing to check -- every pair "
              f"involving a moving part is a declared contact.")
        return {"id": motion.get("id"), "pass": True, "samples": 0}

    lo, hi = sorted(float(x) for x in motion.get("range_deg", [0.0, 360.0]))   # P27 / AC-3: [0, -90] is [-90, 0]
    step = step_override or float(motion.get("step_deg", 2.0))
    if not step > 0:
        print(f"ERROR: motion '{motion.get('id')}': step_deg must be > 0 (got {step:g})", file=sys.stderr)
        return None
    min_clear = float(motion.get("min_clearance_mm", 0.0))
    stops = motion.get("stops")
    if stops is not None:
        ends, within = stops.get("ends"), stops.get("within_deg")
        if not (isinstance(ends, list) and ends and set(ends) <= {"low", "high"}
                and isinstance(within, (int, float)) and within > 0):
            print(f"ERROR: motion '{motion.get('id')}': stops needs \"ends\" from [\"low\", \"high\"] and "
                  f"\"within_deg\" > 0 (got {stops})", file=sys.stderr)
            return None
    lo0, hi0 = lo, hi

    period = sweep_period(motion)
    if period and period < (hi - lo) and not all(symmetric_under(meshes[d["_path"]], d, period) for d in drivers):
        # P27 / AC-5: `teeth` is a claim; a part that does not repeat every pitch gets the full sweep
        if verbose:
            print(f"  gear periodicity refused: a driven part does not repeat after {period:.3f}deg -- full range swept")
        period = None
    if period and period < (hi - lo):
        if verbose:
            z = [d.get("teeth") for d in drivers]
            print(f"  gear periodicity: sweeping {period:.3f}deg instead of "
                  f"{hi - lo:.0f}deg (teeth {z}) -- one tooth pitch repeats")
        hi = lo + period

    engine = Pairwise(meshes, pairs, allow, req, min_clear)

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
    violations = [r for r in results if not r[3] and r[2] and r[1] < engine.need(r[2]) - 1e-12]

    # P28 stops: a motion that claims mechanical end stops must be stopped BY THE PARTS just past each end;
    # otherwise the declared range is a promise nothing enforces (servo limits are software, not stops)
    stop_fail, stop_info = [], []
    for end in (stops or {}).get("ends", []):
        sign, edge = (1, hi0) if end == "high" else (-1, lo0)
        n = max(2, int(math.ceil(stops["within_deg"] / step)))
        hit = None
        for i in range(1, n + 1):
            t = edge + sign * stops["within_deg"] * i / n
            w, _, coll = sample(t)
            if coll or w <= 0.05:   # touching (within 0.05 mm) or interfering counts as the stop
                hit = t
                break
        if hit is None:
            stop_fail.append(f"nothing stops '{motion.get('id', 'motion')}' within {float(stops['within_deg']):.1f} deg past its "
                             f"{end} end ({edge:.1f}) -- the range is not enforced by the parts -- Hint: add an end stop "
                             "that the moving part meets there, or drop that end from \"stops\"")
        else:
            stop_info.append(f"stop at the {end} end: parts meet at t={hit:.1f}deg ({abs(hit - edge):.1f} deg past {edge:.1f})")

    ok = not clashes and not violations and not stop_fail
    out = {
        "id": motion.get("id"), "pass": ok, "samples": len(results),
        "swept_deg": [lo, hi], "step_deg": step,
        "min_clearance_required_mm": min_clear,
        "worst": {"t_deg": round(worst[0], 4),
                  "clearance_mm": (None if worst[1] < 0 or math.isinf(worst[1]) else round(worst[1], 4)),
                  "pair": [os.path.basename(x) for x in worst[2]] if worst[2] else None,
                  "interfering": worst[1] < 0},
        "clash_t_deg": [round(r[0], 3) for r in clashes],
        "violation_t_deg": [round(r[0], 3) for r in violations],
        "stop_failures": stop_fail,
    }

    if verbose:
        label = motion.get("id", "motion")
        for m in stop_info:
            print(f"  {m}")
        for m in stop_fail:
            print(f"  FAIL  {m}")
        if ok:
            print(f"  PASS  '{label}': {len(results)} positions, worst clearance "
                  f"{worst[1]:.3f} mm at t={worst[0]:.2f}deg "
                  f"({' <-> '.join(out['worst']['pair'] or [])})")
        else:
            if clashes or violations:
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
            if clashes or violations:
                print("    Hint: change the centre distance, backlash or layout position of the pair named, "
                      "or correct the driver axis/range in joints.json motion")
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
    motions = expand_groups(motions)
    static = None
    try:
        with open(args.joints, encoding="utf-8") as f:
            raw = json.load(f)
        static = raw.get("static") if isinstance(raw, dict) else None
    except (OSError, ValueError):
        pass
    if not motions:
        print(f"No 'motion' section in {args.joints} -- nothing to sweep. "
              f"(check_collisions.py covers the static pose.)")
        return EXIT_OK

    bad = [m.get("id", f"#{i}") for i, m in enumerate(motions)
           if not isinstance(m.get("drivers"), list) or not m["drivers"]]
    if bad:
        print(f"FAIL: motion entry {', '.join(map(str, bad))} has no \"drivers\" list, so nothing "
              f"can be swept -- Hint: add a \"drivers\" list to that motion in joints.json. Expected shape (see DECLARING MOTION in this script's --help):")
        print('  {"id": "lid_open", "range_deg": [0, 110], "step_deg": 2.0, "drivers": '
              '[{"part": "lid", "type": "revolute", "axis": [1, 0, 0], "origin": [0, 60, 20], "ratio": 1.0}]}')
        return EXIT_FAIL

    sign_failures = check_gear_mesh_signs(contacts, motions)
    if sign_failures:
        print("FAIL: gear-ratio sign check (before any sweep runs):")
        for f in sign_failures:
            print(f"  - {f}")
        print("  Hint: set opposite-sign ratios on the two drivers (or declare internal_gear_mesh).")
        print("Fix the ratio sign at the source -- do not sweep with a sign "
              "known to be wrong; the result would not mean anything.")
        return EXIT_FAIL

    if static is not None:
        loose, dead = unassigned(args.stls, motions, static)
        if loose or dead:
            for p in loose:
                print(f"FAIL: unassigned part {os.path.basename(p)} -- not in any driver and not in \"static\" -- Hint: add it to a driver group or to \"static\" in joints.json")
            for n in dead:
                print(f"FAIL: static entry {n!r} matches no STL (or several) -- Hint: name exactly one positioned STL in \"static\" in joints.json")
            print("Name every part in a driver group or in \"static\" -- an unassigned part is "
                  "exactly the one a sweep would silently treat as static.")
            return EXIT_FAIL
    else:
        print("NOTE: no \"static\" list in the joints file -- parts not named by a driver are "
              "treated as static without a check (declare \"static\" to enforce assignment).")

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

    axis_failures, axis_notes, axis_degraded, axis_usage = check_gear_axes(contacts, motions, meshes, args.stls)
    for n in axis_notes:
        print(n)
    if axis_usage:
        for u in axis_usage:
            print(f"ERROR: {u}")
        return EXIT_USAGE
    if axis_failures:
        print("FAIL: gear axis / centre distance check (before any sweep runs):")
        for f in axis_failures:
            print(f"  - {f}")
        return EXIT_FAIL
    degraded = degraded or axis_degraded

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
