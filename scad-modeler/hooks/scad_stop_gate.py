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
Bash commands count too (P17b): a .scad that is the target of >, >>, tee, sed -i,
or the last argument of cp/mv/install. shortcut: a write from inside a script
(python -c open(...,'w')) or a cd before a relative path is not seen; the path is
resolved against the session cwd.

Install: a Stop hook entry running `python3 <this file>`.
"""
import hashlib, json, os, re, shlex, sys

EDIT_TOOLS = ("Edit", "Write", "MultiEdit")
SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


REDIRECT_RE = re.compile(r">>?\s*['\"]?([^\s'\";|&<>]+\.scad)\b")


def bash_written_scad(cmd):
    """.scad paths a shell command writes to (redirect, tee, sed -i, cp/mv/install target)."""
    out = REDIRECT_RE.findall(cmd)
    for seg in re.split(r"[;&|\n]+", cmd):
        try:
            words = shlex.split(seg)
        except ValueError:
            words = seg.split()
        if not words:
            continue
        prog, args = os.path.basename(words[0]), words[1:]
        if prog == "tee":
            out += [w for w in args if w.endswith(".scad")]
        elif prog == "sed" and any(w.startswith("-i") for w in args):
            out += [w for w in args if w.endswith(".scad")]
        elif prog in ("cp", "mv", "install") and args and args[-1].endswith(".scad"):
            out.append(args[-1])
    return out


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
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") or {}
                if b.get("name") in EDIT_TOOLS:
                    paths = [inp.get("file_path") or ""]
                elif b.get("name") == "Bash":
                    paths = bash_written_scad(inp.get("command") or "")
                else:
                    continue
                for p in paths:
                    if p.endswith(".scad"):
                        p = os.path.realpath(os.path.join(cwd, os.path.expanduser(p)))
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


def norm(t):
    return " ".join(t.split()).casefold()


def unquoted_approvals(transcript, cwd):
    """P5: acceptance.lock files approved this session whose quote is in no user message.
    The agent may run `acceptance.py approve` only with the user's own words."""
    user_text, dirs = [], []
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
                msg = rec.get("message") or {}
            except (ValueError, AttributeError):
                continue
            content = msg.get("content")
            if rec.get("type") == "user" or msg.get("role") == "user":
                if isinstance(content, str):
                    user_text.append(norm(content))
                elif isinstance(content, list):  # tool_result blocks are tool output, not the user
                    user_text += [norm(b.get("text") or "") for b in content
                                  if isinstance(b, dict) and b.get("type") == "text"]
                continue
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                    cmd = (b.get("input") or {}).get("command") or ""
                    if re.search(r"acceptance\.py\b.*\bapprove\b", cmd):
                        m = re.search(r"--project-dir[ =]+['\"]?([^\s'\"]+)", cmd) or \
                            re.search(r"\bcd\s+['\"]?([^\s'\";&]+)", cmd)
                        dirs.append(os.path.join(cwd, os.path.expanduser(m.group(1))) if m else cwd)
    bad = []
    for d in dict.fromkeys(dirs):
        lock = os.path.join(d, "acceptance.lock")
        try:
            quote = norm(json.load(open(lock, encoding="utf-8")).get("quote") or "")
        except (OSError, ValueError):
            continue
        if not quote or not any(quote in t for t in user_text):
            bad.append(lock)
    return bad


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
    bad = unquoted_approvals(h["transcript_path"], cwd)
    if bad:
        print(json.dumps({"decision": "block", "reason":
            "SCAD stop gate: acceptance.json was approved with words that are in no user message "
            "of this session:\n" + "\n".join(f"- {b}" for b in bad) +
            "\nOnly the user approves acceptance numbers. Show them acceptance.json, wait for their "
            "answer, and run acceptance.py approve --quote with their exact words."}))
        return
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
