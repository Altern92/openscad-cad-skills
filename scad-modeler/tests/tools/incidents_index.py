#!/usr/bin/env python3
"""incidents_index.py -- validate or normalize INCIDENTS.json (compatibility wrapper for scripts/incidents.py).

Usage:
    incidents_index.py check   <INCIDENTS.json>
    incidents_index.py rebuild <INCIDENTS.json>
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "scripts"))
sys.path.insert(0, SCRIPTS_DIR)

import incidents  # noqa: E402


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("check", "rebuild"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    cmd, path = sys.argv[1], sys.argv[2]
    doc = incidents.load_doc(path)
    errors = incidents.validate_doc(doc)
    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1
    if cmd == "rebuild":
        incidents.save_doc(path, doc)
    print(f"entries: {len(doc['entries'])}, valid: {len(doc['entries'])}, invalid: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
