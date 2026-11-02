#!/usr/bin/env python3
"""incidents.py -- structured JSON incident log manager for OpenSCAD skills.

Usage:
    python3 scripts/incidents.py check  [--file <INCIDENTS.json>]
    python3 scripts/incidents.py list   [--date YYYY-MM-DD] [--file <INCIDENTS.json>]
    python3 scripts/incidents.py search <query> [--file <INCIDENTS.json>]
    python3 scripts/incidents.py show   <id> [--file <INCIDENTS.json>]
    python3 scripts/incidents.py add    --title "..." --where "..." --symptom "..." \
                                        --root-cause "..." --fix "..." \
                                        [--promoted-to-rule "..."] [--date YYYY-MM-DD] \
                                        [--file <INCIDENTS.json>]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "INCIDENTS.json"))

DATE_RE = re.compile(r"^20[0-9]{2}-[0-9]{2}-[0-9]{2}$")
ID_RE = re.compile(r"^INC-20[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2,}$")
REQUIRED_FIELDS = ("id", "date", "title", "where", "symptom", "root_cause", "fix", "promoted_to_rule")


def resolve_path(explicit_path=None):
    if explicit_path:
        return explicit_path
    return DEFAULT_JSON


def load_doc(path):
    if not os.path.isfile(path):
        raise SystemExit(f"ERROR: INCIDENTS.json not found at {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        raise SystemExit(f"ERROR: invalid JSON in {path}: {exc}")


def save_doc(path, doc):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def validate_doc(doc):
    errors = []
    if not isinstance(doc, dict):
        return ["root must be a JSON object"]
    if doc.get("schema_version") != 1:
        errors.append(f"schema_version must be 1, got {doc.get('schema_version')!r}")
    entries = doc.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list")
        return errors

    seen_ids = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{idx}] is not an object")
            continue
        for field in REQUIRED_FIELDS:
            if field not in entry or not isinstance(entry[field], str):
                errors.append(f"entries[{idx}] ({entry.get('id', '?')}): missing or non-string '{field}'")
        eid = entry.get("id", "")
        date = entry.get("date", "")
        title = entry.get("title", "")
        if not ID_RE.match(eid):
            errors.append(f"entries[{idx}]: invalid id {eid!r} (expected INC-YYYY-MM-DD-NN)")
        if eid in seen_ids:
            errors.append(f"entries[{idx}]: duplicate id {eid!r}")
        seen_ids.add(eid)
        if not DATE_RE.match(date):
            errors.append(f"entries[{idx}] ({eid}): invalid date {date!r} (expected YYYY-MM-DD)")
        if date and eid.startswith("INC-") and not eid.startswith(f"INC-{date}-"):
            errors.append(f"entries[{idx}] ({eid}): id date prefix does not match date {date!r}")
        if not title.strip():
            errors.append(f"entries[{idx}] ({eid}): empty title")
        if not any(entry.get(k, "").strip() for k in ("where", "symptom", "root_cause", "fix", "details")):
            errors.append(f"entries[{idx}] ({eid}): entry has no content fields populated")
    return errors


def cmd_check(args):
    path = resolve_path(args.file)
    doc = load_doc(path)
    errors = validate_doc(doc)
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    entries = doc["entries"]
    print(f"OK: {len(entries)} incidents validated in {os.path.basename(path)} (schema_version=1)")
    return 0


def cmd_list(args):
    path = resolve_path(args.file)
    doc = load_doc(path)
    entries = doc.get("entries", [])
    if args.date:
        entries = [e for e in entries if e.get("date") == args.date]
    for e in entries:
        print(f"{e['id']} | {e['date']} | {e['title']}")
    print(f"Total: {len(entries)} incident(s)")
    return 0


def cmd_search(args):
    path = resolve_path(args.file)
    doc = load_doc(path)
    q = args.query.lower()
    hits = []
    for e in doc.get("entries", []):
        haystack = " ".join(
            str(e.get(k, "")) for k in ("id", "date", "title", "where", "symptom", "root_cause", "fix", "promoted_to_rule", "details")
        ).lower()
        if q in haystack:
            hits.append(e)
    if getattr(args, "json", False):
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return 0
    for e in hits:
        print(f"=== {e['id']} ({e['date']}) -- {e['title']} ===")
        if e.get("where"):
            print(f"  where:            {e['where']}")
        if e.get("symptom"):
            print(f"  symptom:          {e['symptom']}")
        if e.get("root_cause"):
            print(f"  root_cause:       {e['root_cause']}")
        if e.get("fix"):
            print(f"  fix:              {e['fix']}")
        if e.get("promoted_to_rule"):
            print(f"  promoted_to_rule: {e['promoted_to_rule']}")
    print(f"Matches: {len(hits)}")
    return 0


def cmd_show(args):
    path = resolve_path(args.file)
    doc = load_doc(path)
    for e in doc.get("entries", []):
        if e.get("id") == args.id:
            print(json.dumps(e, ensure_ascii=False, indent=2))
            return 0
    print(f"ERROR: incident {args.id!r} not found", file=sys.stderr)
    return 1


def cmd_add(args):
    path = resolve_path(args.file)
    doc = load_doc(path)
    date = args.date or dt.date.today().isoformat()
    if not DATE_RE.match(date):
        print(f"ERROR: invalid --date {date!r} (expected YYYY-MM-DD)", file=sys.stderr)
        return 2
    existing_for_date = [
        e["id"] for e in doc.get("entries", []) if e.get("date") == date and e.get("id", "").startswith(f"INC-{date}-")
    ]
    seq = 1
    for eid in existing_for_date:
        try:
            seq = max(seq, int(eid.rsplit("-", 1)[-1]) + 1)
        except ValueError:
            pass
    new_id = f"INC-{date}-{seq:02d}"
    entry = {
        "id": new_id,
        "date": date,
        "title": args.title.strip(),
        "where": args.where.strip(),
        "symptom": args.symptom.strip(),
        "root_cause": args.root_cause.strip(),
        "fix": args.fix.strip(),
        "promoted_to_rule": (args.promoted_to_rule or "not yet").strip(),
    }
    if args.details:
        entry["details"] = args.details.strip()
    # Insert newest at top of entries list (or append if chronological; keep newest-first by date, then seq)
    doc["entries"].insert(0, entry)
    errors = validate_doc(doc)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    save_doc(path, doc)
    print(f"ADDED {new_id}: {entry['title']}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manage structured OpenSCAD skill incidents (INCIDENTS.json).")
    sub = parser.add_subparsers(dest="cmd")

    p_check = sub.add_parser("check", help="Validate INCIDENTS.json schema and entries")
    p_check.add_argument("positional_file", nargs="?", help="Optional path to INCIDENTS.json")
    p_check.add_argument("--file", help="Path to INCIDENTS.json")

    p_list = sub.add_parser("list", help="List compact 1-line index of incidents")
    p_list.add_argument("--date", help="Filter by YYYY-MM-DD")
    p_list.add_argument("--file", help="Path to INCIDENTS.json")

    p_search = sub.add_parser("search", help="Search incidents by keyword")
    p_search.add_argument("query", help="Case-insensitive search term")
    p_search.add_argument("--json", action="store_true", help="Output matching entries as JSON")
    p_search.add_argument("--file", help="Path to INCIDENTS.json")

    p_show = sub.add_parser("show", help="Show full JSON for one incident ID")
    p_show.add_argument("id", help="Incident ID (e.g. INC-2026-11-02-01)")
    p_show.add_argument("--file", help="Path to INCIDENTS.json")

    p_add = sub.add_parser("add", help="Append a new structured incident to INCIDENTS.json")
    p_add.add_argument("--title", required=True, help="One-line summary of what broke")
    p_add.add_argument("--where", required=True, help="File/project where it occurred")
    p_add.add_argument("--symptom", required=True, help="What was observed")
    p_add.add_argument("--root-cause", required=True, help="Underlying root cause")
    p_add.add_argument("--fix", required=True, help="What changed to fix it")
    p_add.add_argument("--promoted-to-rule", default="not yet", help="Rule/fixture it was promoted to")
    p_add.add_argument("--details", default="", help="Optional additional notes")
    p_add.add_argument("--date", default="", help="Incident date YYYY-MM-DD (defaults to today)")
    p_add.add_argument("--file", help="Path to INCIDENTS.json")

    args = parser.parse_args(argv)
    if args.cmd == "check":
        if getattr(args, "positional_file", None) and not args.file:
            args.file = args.positional_file
        return cmd_check(args)
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "search":
        return cmd_search(args)
    if args.cmd == "show":
        return cmd_show(args)
    if args.cmd == "add":
        return cmd_add(args)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

