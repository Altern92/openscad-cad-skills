#!/usr/bin/env python3
"""Approved acceptance criteria the agent cannot weaken (P5, 2026-11-01).

Since P15 every part declares `// EXPECTED_BBOX` and `// EXPECTED_THROUGH_HOLES`,
but the same agent writes those lines next to the geometry, so a part that
fails can be "fixed" by editing its declaration. acceptance.json holds the
numbers the USER agreed to before any geometry; acceptance.lock pins them.

    {"parts": {"plate": {"bbox": [20, 10, 5], "through_holes": 0}}}

Usage (from the project root):
    acceptance.py approve --quote "<the user's own words approving it>"
        writes acceptance.lock = sha256 of acceptance.json + the quote. Run it only
        after the user said yes; the stop hook checks the quote is in a user message.
    acceptance.py emit      prints the declaration lines for each part
    acceptance.py check     the gate validate_scad.sh runs

Exit codes:
    0  pass (approve/emit done)
    2  no acceptance.json (check: SKIP)
    3  fail -- not approved, changed after approval, or a part disagrees
    4  usage error
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

EXIT_OK, EXIT_NONE, EXIT_FAIL, EXIT_USAGE = 0, 2, 3, 4
SPEC, LOCK = "acceptance.json", "acceptance.lock"
BBOX_RE = re.compile(r"^\s*//\s*EXPECTED_BBOX\s*:\s*\[([^\]]*)\]", re.M)
HOLES_RE = re.compile(r"^\s*//\s*EXPECTED_THROUGH_HOLES\s*:\s*(\d+)", re.M)


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_spec(d):
    with open(os.path.join(d, SPEC), encoding="utf-8") as f:
        spec = json.load(f)
    parts = spec.get("parts") if isinstance(spec, dict) else None
    if not isinstance(parts, dict) or not parts:
        raise ValueError(f'{SPEC} needs {{"parts": {{"<part>": {{"bbox": [x, y, z], "through_holes": N}}}}}}')
    return parts


def fmt(v):
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def check(d):
    spec_path, lock_path = os.path.join(d, SPEC), os.path.join(d, LOCK)
    if not os.path.isfile(spec_path):
        print(f"SKIP: acceptance, no {SPEC}")
        return EXIT_NONE
    try:
        parts = load_spec(d)
    except (ValueError, OSError) as e:
        print(f"FAIL: acceptance, {SPEC} unreadable: {e}")
        return EXIT_FAIL
    if not os.path.isfile(lock_path):
        print(f"FAIL: acceptance, {SPEC} is not approved (no {LOCK}). Show it to the user; after their "
              f"yes run: acceptance.py approve --quote \"<their words>\"")
        return EXIT_FAIL
    with open(lock_path, encoding="utf-8") as f:
        lock = json.load(f)
    if lock.get("sha256") != sha256(spec_path):
        print(f"FAIL: acceptance, {SPEC} changed after approval ({lock.get('when', '?')}, "
              f"\"{lock.get('quote', '')}\"). Show the user the change and re-approve -- never edit the "
              f"spec to match a part.")
        return EXIT_FAIL
    errors = []
    for name, want in parts.items():
        scad = os.path.join(d, "parts", f"{name}.scad")
        if not os.path.isfile(scad):
            errors.append(f"{name}: approved in {SPEC} but parts/{name}.scad does not exist")
            continue
        with open(scad, encoding="utf-8", errors="replace") as f:
            src = f.read()
        if "bbox" in want:
            m = BBOX_RE.search(src)
            got = [float(x) for x in m.group(1).split(",")] if m else None
            if got is None or len(got) != 3 or any(abs(a - float(b)) > 1e-9 for a, b in zip(got, want["bbox"])):
                errors.append(f"{name}: EXPECTED_BBOX is {('[' + ', '.join(map(fmt, got)) + ']') if got else 'not declared'}"
                              f", approved [{', '.join(map(fmt, want['bbox']))}]")
        if "through_holes" in want:
            m = HOLES_RE.search(src)
            got = int(m.group(1)) if m else None
            if got != int(want["through_holes"]):
                errors.append(f"{name}: EXPECTED_THROUGH_HOLES is {got if got is not None else 'not declared'}"
                              f", approved {want['through_holes']}")
    if errors:
        for e in errors:
            print(f"FAIL: acceptance, {e}")
        print("  -> fix the PART to meet the approved numbers, or ask the user to change acceptance.json.")
        return EXIT_FAIL
    print(f"PASS: acceptance, {len(parts)} part(s) match the approved spec (\"{lock.get('quote', '')}\")")
    return EXIT_OK


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("approve", "emit", "check"))
    ap.add_argument("--quote", default=None)
    ap.add_argument("--project-dir", default=".")
    a = ap.parse_args()
    d = a.project_dir
    if a.cmd == "check":
        return check(d)
    if not os.path.isfile(os.path.join(d, SPEC)):
        print(f"ERROR: no {SPEC} in {os.path.abspath(d)}", file=sys.stderr)
        return EXIT_USAGE
    try:
        parts = load_spec(d)
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_USAGE
    if a.cmd == "emit":
        for name, want in parts.items():
            print(f"parts/{name}.scad:")
            if "bbox" in want:
                print(f"// EXPECTED_BBOX: [{', '.join(map(fmt, want['bbox']))}]")
            if "through_holes" in want:
                print(f"// EXPECTED_THROUGH_HOLES: {int(want['through_holes'])}")
        return EXIT_OK
    if not (a.quote or "").strip():
        print("ERROR: approve needs --quote \"<the user's own words>\"; the stop hook checks it", file=sys.stderr)
        return EXIT_USAGE
    lock = {"sha256": sha256(os.path.join(d, SPEC)), "quote": a.quote.strip(),
            "when": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    tmp = os.path.join(d, LOCK + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lock, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, os.path.join(d, LOCK))
    print(f"approved {SPEC} ({lock['sha256'][:12]}): \"{lock['quote']}\"")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
