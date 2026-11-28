#!/usr/bin/env python3
"""Protected limits: the agent may tighten a gate's limit, never loosen it (P25, 2026-11-18).

The gates read their limits from files the same agent writes: behavior.json (max_gap, angle
max_deg, clearance, ground tol), loads.json (safety, force), joints.json (interference range,
min clearance) and the part files (EXPECTED_BBOX_TOL, NO_* / MARGIN_EXCLUDES_OK / PREVIEW_FILE
opt-outs). One edited number turns a FAIL into a PASS. On 2026-11-18 the agent itself picked the
15 deg ball-joint limit while params.scad said 25. limits.lock pins every limit with the user's words.

Usage (from the project root):
    check_limits.py approve --quote "<the user's own words>"   writes limits.lock (stop hook checks
                                                               the quote is in a user message)
    check_limits.py check                                      the gate validate_scad.sh runs
A limit whose source says estimate / ◇ / PATIKRINTI is printed as OPEN QUESTION: ask the user or
measure the part -- the answer goes through approve, never through an edit.

Exit: 0 pass, 2 no limits.lock (SKIP), 3 a limit was loosened or removed, 4 usage / bad JSON.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import sys

EXIT_OK, EXIT_NONE, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4
LOCK = "limits.lock"
SCHEMA = 2   # 2 = P27b inventory (implicit defaults, motion, drivers, contacts, force direction)
# colon optional (P26 / AC-13): validate_scad.sh honours a bare `// PREVIEW_FILE`; LIBRARY_FILE drops a part too
OPT_OUT = re.compile(r"^\s*//\s*(NO_JOINT|NO_RETENTION|NO_BBOX|NO_THROUGH_HOLES_CHECK|PREVIEW_FILE|LIBRARY_FILE"
                     r"|MARGIN_EXCLUDES_OK)\b(?:[ \t]*:[ \t]*(\S*))?", re.M)
COUNTS = re.compile(r"^\s*//\s*(EXPECTED_BODIES|EXPECTED_CAVITIES)\s*:\s*([0-9]+)", re.M)
BBOX_TOL = re.compile(r"^\s*//\s*EXPECTED_BBOX_TOL\s*:\s*(\[[^\]]*\]|[-0-9.eE]+)", re.M)
ESTIMATE = re.compile(r"estimate|◇|PATIKRINTI|unverified|guess", re.I)
# direction: "max" = a bigger value is looser, "min" = a smaller value is looser, "flag" = presence is looser,
# "eq" = any change is a different check (material, print direction, support/load points; value = hash)


def load(d, name):
    p = os.path.join(d, name)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(usage(f"{name}: not valid JSON ({e})"))


def rows(doc, key):
    """A declaration file is either {"key": [...]} or the bare list (attachments.json in practice)."""
    return doc if isinstance(doc, list) else (doc or {}).get(key, []) if isinstance(doc, dict) else []


def usage(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    return EXIT_USAGE


def inventory(d):
    """{key: (value, direction)} for every limit a gate reads; questions = [(key, text)]."""
    inv, questions = {}, []

    def put_eq(key, obj):
        if obj is not None:
            h = hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:12]
            inv[key] = (float(int(h, 16)), "eq")

    def put(key, val, direction, note=""):
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            inv[key] = (float(val), direction)
            if note and ESTIMATE.search(note):
                questions.append((key, val, note))

    b = load(d, "behavior.json") or {}
    b = b if isinstance(b, dict) else {}
    for j in rows(b, "joints"):
        k = f"behavior.json joints[{j.get('a')}|{j.get('b')}]"
        put(k + ".max_gap", j.get("max_gap"), "max", j.get("why", ""))
        an = j.get("angle") or {}
        put(k + ".angle.max_deg", an.get("max_deg"), "max", an.get("source", ""))
    # P27 / AC-12 (Fable calculation audit): implicit defaults are inventoried (check_behavior.py's values),
    # so writing one after approval is a change of a locked limit, not a "new" one that never fails
    cl = b.get("clearance") or {}
    if b:
        put("behavior.json clearance.default", cl.get("default", 0.0), "min")
    for p in cl.get("pairs", []):
        put(f"behavior.json clearance[{p.get('a')}|{p.get('b')}].min", p.get("min"), "min", p.get("why", ""))
    if b.get("ground") is not None:
        put("behavior.json ground.tol", (b.get("ground") or {}).get("tol", 0.5), "max")

    for c in rows(load(d, "loads.json"), "cases"):
        k = f"loads.json cases[{c.get('name')}]"
        put(k + ".safety", c.get("safety", 2.0), "min", c.get("source", ""))
        put(k + ".reach", c.get("reach", 30.0), "max", c.get("source", ""))  # wider reach unions more material
        defaults = {"material": "PETG Basic", "print_up": [0, 0, 1]}  # check_strength.py's defaults
        for fld in ("material", "print_up", "support", "at", "part"):
            put_eq(f"{k}.{fld}", c.get(fld, defaults.get(fld)))
        f = c.get("force_N")
        if isinstance(f, (int, float)) and not isinstance(f, bool):   # wave2 AC-E1: screw_pullout carries a scalar force
            put(k + ".force_N", f, "min", c.get("source", ""))
        # wave2 review: analytic inputs of check_strength. A larger engagement / thread Ø = more shear area = looser;
        # the rest (pitch, hub OD, E, nu, axis) move the result either way, so any change is a change of the check
        put(k + ".engagement_mm", c.get("engagement_mm"), "max", c.get("source", ""))
        put(k + ".thread_d_mm", c.get("thread_d_mm"), "max", c.get("source", ""))
        for fld in ("pitch_mm", "shaft_d_mm", "hub_od_mm", "hub_E_mpa", "hub_nu", "shaft_E_mpa", "shaft_nu"):
            put_eq(f"{k}.{fld}", c.get(fld))
        if c.get("type") == "press_fit" or "interference_mm" in c:
            put_eq(k + ".axis", c.get("axis", [0, 0, 1]))   # check_strength.py's default
        put(k + ".shear_mpa", c.get("shear_mpa"), "max", c.get("source", ""))             # bigger = looser
        put(k + ".interference_mm", c.get("interference_mm"), "min", c.get("source", ""))  # press_fit: smaller = looser
        if isinstance(f, list) and len(f) == 3:
            mag = sum(float(x) ** 2 for x in f) ** 0.5
            put(k + ".force_N", mag, "min", c.get("source", ""))
            if mag > 0:   # P27 / AC-12: the direction is the check too (bending -> axial passed on magnitude)
                put_eq(k + ".force_dir", [round(float(x) / mag, 6) + 0.0 for x in f])   # + 0.0: -0.0 is 0.0

    jj = load(d, "joints.json") or {}
    for m in rows(jj, "motion"):  # motion_sweep.py reads motion[].min_clearance_mm (P26 / AC-14)
        k = f"joints.json motion[{m.get('id')}]"
        put(k + ".min_clearance_mm", m.get("min_clearance_mm", 0.0), "min")
        put(k + ".step_deg", m.get("step_deg", 2.0), "max")          # P27 / AC-12: coarser = looser
        rg = m.get("range_deg", [0.0, 360.0])
        if isinstance(rg, list) and len(rg) == 2 and all(isinstance(x, (int, float)) for x in rg):
            put(k + ".range_deg[lo]", min(rg), "max")                 # a narrower range is looser
            put(k + ".range_deg[hi]", max(rg), "min")
        # P27b (Fable review): the whole driver is the check -- teeth added, ratio 0.001, a moved axis or a
        # dropped driver (the part turns static) all passed; one hash over the motion's driver set
        put_eq(k + ".drivers", sorted((json.dumps(dv, sort_keys=True) for dv in m.get("drivers", [])), key=str))
    for c in rows(jj, "contacts"):
        # P27b: a declared contact is itself a waiver (overlap allowed, may set its own clearance): a new one is
        # a new opt-out; its own min_clearance_mm overrides the motion's
        inv[f"joints.json contact[{'|'.join(sorted(map(str, c.get('pair', []))))}]"] = (1.0, "flag")
        if "min_clearance_mm" in c:
            put(f"joints.json contacts[{'|'.join(map(str, c.get('pair', [])))}].min_clearance_mm", c["min_clearance_mm"], "min")
        r = c.get("expected_interference_mm", [0.0, 0.0])   # P27 / AC-12: an undeclared range is [0, 0]
        if isinstance(r, list) and len(r) == 2:
            k = f"joints.json contacts[{'|'.join(map(str, c.get('pair', [])))}].expected_interference_mm"
            put(k + "[lo]", r[0], "min", c.get("derivation", ""))
            put(k + "[hi]", r[1], "max", c.get("derivation", ""))

    for c in rows(load(d, "attachments.json"), "attachments"):
        put(f"attachments.json [{c.get('name')}].min_material_mm", c.get("min_material_mm"), "min")

    for f in sorted(glob.glob(os.path.join(d, "parts", "*.scad")) + glob.glob(os.path.join(d, "*.scad"))):
        rel = os.path.relpath(f, d)
        text = open(f, encoding="utf-8", errors="replace").read()
        for m in BBOX_TOL.finditer(text):
            vals = json.loads(m.group(1)) if m.group(1).startswith("[") else [float(m.group(1))] * 3
            for axis, v in zip("xyz", vals):
                put(f"{rel} EXPECTED_BBOX_TOL.{axis}", v, "max")
        for m in COUNTS.finditer(text):
            put(f"{rel} {m.group(1)}", int(m.group(2)), "max")
        for m in OPT_OUT.finditer(text):
            arg = m.group(2) if m.group(1) == "MARGIN_EXCLUDES_OK" else ""
            inv[f"{rel} {m.group(1)}{(':' + arg) if arg else ''}"] = (1.0, "flag")
    return inv, questions


def default_for(k, locked):
    """The approved value a NEW key overrides (P27 / AC-12), or None when the key is a genuinely new check
    (a new joint, load case or motion adds a test). A new contact's interference range overrides [0, 0]."""
    if re.match(r"behavior\.json clearance\[.*\]\.min$", k) and "behavior.json clearance.default" in locked:
        return float(locked["behavior.json clearance.default"][0])
    if re.match(r"joints\.json contacts\[.*\]\.expected_interference_mm\[(lo|hi)\]$", k):
        return 0.0
    m = re.match(r"joints\.json contacts\[.*\]\.min_clearance_mm$", k)
    if m:   # a contact's own clearance overrides the smallest motion clearance that was approved
        vals = [float(v[0]) for kk, v in locked.items() if kk.endswith("].min_clearance_mm") and kk.startswith("joints.json motion[")]
        return min(vals) if vals else 0.0
    return None


def check(d, brief=False):
    inv, questions = inventory(d)
    for key, val, note in questions:
        print(f"OPEN QUESTION: {key} = {val:g} rests on an estimate ({note}) -- ask the user or measure; "
              f"the answer goes through check_limits.py approve, never through an edit")
    lock_path = os.path.join(d, LOCK)
    if not os.path.isfile(lock_path):
        try:
            was = json.load(open(os.path.join(d, "build", ".validation_state.json"))).get("limits_locked")
        except (OSError, ValueError, AttributeError):
            was = False
        if was:  # P26 / AC-13: deleting the lock must not turn the gate into a SKIP
            print(f"FAIL limits: {LOCK} existed at the last validate --all and is gone -- restore it or "
                  f"re-approve with the user's words (check_limits.py approve --quote) -- Hint: restore {LOCK} "
                  f"from version control, or re-approve the limits with approve --quote")
            return EXIT_FAIL
        print(f"SKIP: {len(inv)} limit(s) not locked: no {LOCK}. Show the user the limits "
              f"(check_limits.py check lists them) and run approve --quote with their words.")
        for k, (v, dr) in ([] if brief else sorted(inv.items())):
            print(f"  {k} = " + ("(value pinned; any change)" if dr == "eq" else
                  f"{v:g} ({'bigger' if dr == 'max' else 'smaller' if dr == 'min' else 'present'} = looser)"))
        return EXIT_NONE
    try:
        lock = json.load(open(lock_path, encoding="utf-8"))
        locked = lock["limits"]
    except (ValueError, KeyError) as e:
        return usage(f"{LOCK}: unreadable ({e})")
    quote = lock.get("quote", "")
    if lock.get("schema", 1) < SCHEMA:
        print(f"OPEN QUESTION: {LOCK} was approved before schema {SCHEMA} (P27b): implicit defaults, motion step/range, "
              f"drivers, contacts and force direction are NOT protected until the user re-approves (approve --quote)")
    bad, tight = [], []
    for k, (v0, dr) in sorted(((k, tuple(v)) for k, v in locked.items())):
        if k not in inv:
            if dr == "eq":
                bad.append(f"{k}: removed (approved by \"{quote}\") -- Hint: put the declaration back in the source")
            elif dr != "flag":
                bad.append(f"{k}: removed (approved {v0:g} by \"{quote}\") -- Hint: put the limit back at {v0:g} or tighter")
            continue
        v = inv[k][0]
        if dr == "eq":
            if v != v0:
                bad.append(f"{k}: changed (approved by \"{quote}\") -- a different check, not the approved one -- Hint: restore the approved value in the source")
            continue
        if (dr == "max" and v > v0 + 1e-9) or (dr == "min" and v < v0 - 1e-9):
            bad.append(f"{k}: {v0:g} -> {v:g} (loosened; approved {v0:g} by \"{quote}\") -- Hint: restore {v0:g} or tighter, fix the geometry instead")
        elif v != v0 and dr != "flag":
            tight.append(f"{k}: {v0:g} -> {v:g}")
    for k, (v, dr) in sorted(inv.items()):
        if k not in locked and dr == "flag":
            bad.append(f"{k}: new opt-out (loosened; not in the approved limits) -- Hint: remove the opt-out, or show the user and approve --quote")
        elif k not in locked:
            base = default_for(k, locked)
            if base is not None and ((dr == "max" and v > base + 1e-9) or (dr == "min" and v < base - 1e-9)):
                bad.append(f"{k}: new limit {v:g} looser than the approved default {base:g} it overrides "
                           f"(approved by \"{quote}\") -- Hint: use the approved default or tighter, or re-approve with approve --quote")
    for t in tight:
        print(f"NOTE: tightened {t}")
    for x in bad:
        print(f"FAIL limits: {x}")
    new = [k for k in inv if k not in locked and inv[k][1] != "flag"]
    print(f"LIMITS: {len(locked)} locked, {len(tight)} tightened, {len(new)} new (unlocked), "
          f"{len(bad)} loosened/removed, {len(questions)} open question(s)")
    if bad:
        print("Never edit a limit to pass a gate: fix the geometry, or show the user the change and "
              "re-approve with their words.")
        return EXIT_FAIL
    return EXIT_OK


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("approve", "check"))
    ap.add_argument("--quote", default=None)
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--brief", action="store_true", help="check: do not list unlocked limits (validate_scad.sh)")
    a = ap.parse_args()
    if a.cmd == "check":
        return check(a.project_dir, a.brief)
    if not (a.quote or "").strip():
        return usage("approve needs --quote \"<the user's own words>\"; the stop hook checks it")
    inv, _ = inventory(a.project_dir)
    lock = {"schema": SCHEMA, "limits": {k: list(v) for k, v in sorted(inv.items())}, "quote": a.quote.strip(),
            "when": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    p = os.path.join(a.project_dir, LOCK)
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(p + ".tmp", p)
    print(f"approved {len(inv)} limit(s): \"{lock['quote']}\"")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
