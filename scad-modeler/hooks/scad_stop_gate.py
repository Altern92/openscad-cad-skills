#!/usr/bin/env python3
"""Claude Code Stop hook (P9, 2026-11-01): no ending a session that edited a
.scad file until validate_scad.sh has run on that file's current content.

Why: 31 of 95 incidents were a false PASS or a check that never ran -- an agent
ran one checker by hand, or none, and reported the part done. validate_scad.sh
writes build/.validation_state.json with a sha256 per source; this hook trusts
only those hashes, never the agent's own words.

Rules: files come from Edit/Write/MultiEdit calls in the transcript. A file whose
current sha256 is not in the nearest build/.validation_state.json (walking up
from its directory) blocks the stop once. A FAIL verdict does not block -- a FAIL
that is reported is a legitimate end. Never blocks when stop_hook_active is set
(Claude Code's loop guard), when SCAD_STOP_GATE=0, for files that no longer exist
or live under tests/fixtures/, or on any error (always exits 0).
shortcut: .scad written through Bash (heredoc, cp) is not seen; add a Bash
command scan if that turns out to happen in practice.

Install: a Stop hook entry running `python3 <this file>`.
"""
import hashlib, json, os, sys

EDIT_TOOLS = ("Edit", "Write", "MultiEdit")
SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


def edited_scad(transcript, cwd):
    seen = []
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                content = (json.loads(line).get("message") or {}).get("content")
            except (ValueError, AttributeError):
                continue
            if not isinstance(content, list):
                continue
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in EDIT_TOOLS:
                    p = (b.get("input") or {}).get("file_path") or ""
                    if p.endswith(".scad"):
                        p = os.path.realpath(os.path.join(cwd, p))
                        if p not in seen:
                            seen.append(p)
    return seen


def validated(path):
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    d = os.path.dirname(path)
    while True:
        state = os.path.join(d, "build", ".validation_state.json")
        if os.path.isfile(state):
            try:
                sources = json.load(open(state, encoding="utf-8")).get("sources") or {}
            except ValueError:
                return False
            return any(v == h and os.path.realpath(os.path.join(d, k)) == path for k, v in sources.items())
        if os.path.dirname(d) == d:
            return False
        d = os.path.dirname(d)


def command_for(path):
    d, name = os.path.split(path)
    if os.path.basename(d) == "parts":
        return f"cd '{os.path.dirname(d)}' && bash '{SCRIPTS}/validate_scad.sh' --all"
    return f"cd '{d}' && bash '{SCRIPTS}/validate_scad.sh' '{name}'"


def main():
    if os.environ.get("SCAD_STOP_GATE") == "0":
        return
    h = json.load(sys.stdin)
    if h.get("stop_hook_active"):
        return
    cwd = h.get("cwd") or os.getcwd()
    stale = [p for p in edited_scad(h["transcript_path"], cwd)
             if os.path.isfile(p) and "/tests/fixtures/" not in p and not validated(p)]
    if not stale:
        return
    lines = [f"- {p}\n  run: {command_for(p)}" for p in stale]
    print(json.dumps({"decision": "block", "reason":
        "SCAD stop gate: these .scad files changed after their last validate_scad.sh run "
        "(no matching sha256 in build/.validation_state.json):\n" + "\n".join(lines) +
        "\nRun it, then report its CHECK_RESULT and COVERAGE lines to the user. If it cannot "
        "run (CHECK_RESULT env=FAIL), say so plainly and do not call the part done."}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
