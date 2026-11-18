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
import json
import os
import re
import sys

EXIT_OK, EXIT_NONE, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4
LOCK = "limits.lock"
OPT_OUT = re.compile(r"^\s*//\s*(NO_JOINT|NO_RETENTION|NO_BBOX|NO_THROUGH_HOLES_CHECK|PREVIEW_FILE"
                     r"|MARGIN_EXCLUDES_OK)\s*:\s*(\S*)", re.M)
BBOX_TOL = re.compile(r"^\s*//\s*EXPECTED_BBOX_TOL\s*:\s*(\[[^\]]*\]|[-0-9.eE]+)", re.M)
ESTIMATE = re.compile(r"estimate|◇|PATIKRINTI|unverified|guess", re.I)
# direction: "max" = a bigger value is looser, "min" = a smaller value is looser, "flag" = presence is looser


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
    cl = b.get("clearance") or {}
    put("behavior.json clearance.default", cl.get("default"), "min")
    for p in cl.get("pairs", []):
        put(f"behavior.json clearance[{p.get('a')}|{p.get('b')}].min", p.get("min"), "min", p.get("why", ""))
    put("behavior.json ground.tol", (b.get("ground") or {}).get("tol"), "max")

    for c in rows(load(d, "loads.json"), "cases"):
        k = f"loads.json cases[{c.get('name')}]"
        put(k + ".safety", c.get("safety", 2.0), "min", c.get("source", ""))
        f = c.get("force_N")
        if isinstance(f, list) and len(f) == 3:
            put(k + ".force_N", sum(float(x) ** 2 for x in f) ** 0.5, "min", c.get("source", ""))

    jj = load(d, "joints.json") or {}
    if isinstance(jj, dict):
        put("joints.json min_clearance_mm", jj.get("min_clearance_mm"), "min")
    for c in rows(jj, "contacts"):
        r = c.get("expected_interference_mm")
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
        for m in OPT_OUT.finditer(text):
            arg = m.group(2) if m.group(1) == "MARGIN_EXCLUDES_OK" else ""
            inv[f"{rel} {m.group(1)}{(':' + arg) if arg else ''}"] = (1.0, "flag")
    return inv, questions


def check(d, brief=False):
    inv, questions = inventory(d)
    for key, val, note in questions:
        print(f"OPEN QUESTION: {key} = {val:g} rests on an estimate ({note}) -- ask the user or measure; "
              f"the answer goes through check_limits.py approve, never through an edit")
    lock_path = os.path.join(d, LOCK)
    if not os.path.isfile(lock_path):
        print(f"SKIP: {len(inv)} limit(s) not locked: no {LOCK}. Show the user the limits "
              f"(check_limits.py check lists them) and run approve --quote with their words.")
        for k, (v, dr) in ([] if brief else sorted(inv.items())):
            print(f"  {k} = {v:g} ({'bigger' if dr == 'max' else 'smaller' if dr == 'min' else 'present'} = looser)")
        return EXIT_NONE
    try:
        lock = json.load(open(lock_path, encoding="utf-8"))
        locked = lock["limits"]
    except (ValueError, KeyError) as e:
        return usage(f"{LOCK}: unreadable ({e})")
    quote = lock.get("quote", "")
    bad, tight = [], []
    for k, (v0, dr) in sorted(((k, tuple(v)) for k, v in locked.items())):
        if k not in inv:
            if dr != "flag":
                bad.append(f"{k}: removed (approved {v0:g} by \"{quote}\")")
            continue
        v = inv[k][0]
        if (dr == "max" and v > v0 + 1e-9) or (dr == "min" and v < v0 - 1e-9):
            bad.append(f"{k}: {v0:g} -> {v:g} (loosened; approved {v0:g} by \"{quote}\")")
        elif v != v0 and dr != "flag":
            tight.append(f"{k}: {v0:g} -> {v:g}")
    for k, (v, dr) in sorted(inv.items()):
        if k not in locked and dr == "flag":
            bad.append(f"{k}: new opt-out (loosened; not in the approved limits)")
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
    lock = {"limits": {k: list(v) for k, v in sorted(inv.items())}, "quote": a.quote.strip(),
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
