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
            out += [w for w in args if w.endswith((".scad", ".json"))]
        elif prog in ("cp", "mv", "install") and args and args[-1].endswith((".scad", ".json")):
            out.append(args[-1])
    return out


def edited_scad(transcript, cwd):
    """.scad and .json paths written this session (Edit/Write tools, shell writes)."""
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
                    if p.endswith((".scad", ".json")):
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


def project_root(path):
    """Nearest directory (walking up) holding build/.validation_state.json, else None."""
    d = os.path.dirname(path)
    while True:
        if os.path.isfile(os.path.join(d, "build", ".validation_state.json")):
            return d
        if os.path.dirname(d) == d:
            return None
        d = os.path.dirname(d)


def stale_declarations(paths):
    """P25 / AC-2: root *.json of every touched project whose sha256 differs from the last
    validate --all receipt. Single-file receipts are skipped; a pre-P25 --all receipt (no
    "declarations") flags only the root *.json this session wrote.
    shortcut: a project counts as touched only through a .scad/.json path written this session;
    a generator run alone (python gen_decl.py) is not seen -- record its outputs via a touched file."""
    out = []
    for root in dict.fromkeys(r for r in map(project_root, paths) if r):
        try:
            rec = json.load(open(os.path.join(root, "build", ".validation_state.json"), encoding="utf-8"))
        except ValueError:
            continue
        if rec.get("mode") != "--all":  # a single-file receipt (scratch dir, /tmp) is not a project
            continue
        decl = rec.get("declarations")
        for f in sorted(os.listdir(root)):
            fp = os.path.join(root, f)
            if not f.endswith(".json") or not os.path.isfile(fp):
                continue
            if decl is None:  # pre-P25 receipt cannot tell: flag only declarations written this session
                if fp in paths:
                    out.append(fp)
                continue
            if decl.get(f) != hashlib.sha256(open(fp, "rb").read()).hexdigest():
                out.append(fp)
    return out


def norm(t):
    return " ".join(t.split()).casefold()


TAG_RE = re.compile(r"<(system-reminder|task-notification|command-[a-z]+|local-command-[a-z]+)>.*?</\1>", re.S)
RECEIPT_RE = re.compile(r">>?\s*['\"]?([^\s'\";|&<>]*\.validation_state\.json)")
MIN_QUOTE = 8


def human_texts(rec):
    """Text the human typed in one transcript record, or [] (tool output, injected context, summaries)."""
    msg = rec.get("message") or {}
    if not (rec.get("type") == "user" or msg.get("role") == "user"):
        return []
    if rec.get("isMeta") or rec.get("isCompactSummary") or rec.get("toolUseResult") is not None:
        return []
    content = msg.get("content")
    parts = [content] if isinstance(content, str) else \
        [b.get("text") or "" for b in content if isinstance(b, dict) and b.get("type") == "text"] \
        if isinstance(content, list) else []
    out = []
    for t in parts:
        t = TAG_RE.sub("", t).strip()
        if t and not t.startswith("<"):
            out.append(t)
    return out


def session_start(transcript):
    import datetime
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                ts = json.loads(line).get("timestamp")
            except (ValueError, AttributeError):
                continue
            if ts:
                try:
                    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                except ValueError:
                    continue
    return 0.0


def unquoted_approvals(transcript, cwd, edited=()):
    """P5 / P26 AC-11: acceptance.lock / limits.lock written this session whose quote is not a whole
    message (or a whole line of one) the human typed. Checked by lock FILE, not by command shape:
    Write-tool locks, `cd x && approve` and continuation lines all count (Fable audit 2026-11-19)."""
    said, dirs = set(), {cwd}
    dirs.update(r for r in map(project_root, edited) if r)
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            for t in human_texts(rec):
                said.add(norm(t))
                said.update(norm(l) for l in t.splitlines() if l.strip())
            content = (rec.get("message") or {}).get("content")
            for b in content if isinstance(content, list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") or {}
                if b.get("name") in EDIT_TOOLS and str(inp.get("file_path", "")).endswith(".lock"):
                    dirs.add(os.path.dirname(os.path.join(cwd, os.path.expanduser(inp["file_path"]))))
                elif b.get("name") == "Bash" and "approve" in (inp.get("command") or ""):
                    cmd = inp.get("command") or ""
                    for m in re.finditer(r"(?:--project-dir[ =]+|\bcd\s+)['\"]?([^\s'\";&|]+)", cmd):
                        dirs.add(os.path.join(cwd, os.path.expanduser(m.group(1))))
    t0 = session_start(transcript)
    bad = []
    for d in sorted(dirs):
        for lockname in ("acceptance.lock", "limits.lock"):
            lock = os.path.realpath(os.path.join(d, lockname))
            if not os.path.isfile(lock) or os.path.getmtime(lock) < t0:
                continue
            try:
                quote = norm(json.load(open(lock, encoding="utf-8")).get("quote") or "")
            except (OSError, ValueError, AttributeError):
                bad.append(lock); continue
            if len(quote) < MIN_QUOTE or quote not in said:
                bad.append(lock)
    return sorted(set(bad))


def hand_written_receipts(transcript, cwd):
    """P26 / AC-12: a validation receipt the session wrote itself (Edit/Write or a shell redirect)."""
    out = []
    with open(transcript, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                content = (json.loads(line).get("message") or {}).get("content")
            except (ValueError, AttributeError):
                continue
            for b in content if isinstance(content, list) else []:
                if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                    continue
                inp = b.get("input") or {}
                paths = [inp.get("file_path") or ""] if b.get("name") in EDIT_TOOLS else \
                    RECEIPT_RE.findall(inp.get("command") or "") if b.get("name") == "Bash" else []
                for p in paths:
                    if p.endswith(".validation_state.json"):
                        p = os.path.realpath(os.path.join(cwd, os.path.expanduser(p)))
                        if os.path.isfile(p) and "/tests/fixtures/" not in p and p not in out:
                            out.append(p)
    return out


def command_for(path):
    d, name = os.path.split(path)
    if os.path.basename(d) == "parts":
        return f"cd '{os.path.dirname(d)}' && bash '{SCRIPTS}/validate_scad.sh' --all"
    return f"cd '{d}' && bash '{SCRIPTS}/validate_scad.sh' '{name}'"


def cmd_all(path):
    return f"cd '{os.path.dirname(path)}' && bash '{SCRIPTS}/validate_scad.sh' --all"


def main():
    if os.environ.get("SCAD_STOP_GATE") == "0":
        return
    h = json.load(sys.stdin)
    if h.get("stop_hook_active"):
        return
    cwd = h.get("cwd") or os.getcwd()
    edited = [p for p in edited_scad(h["transcript_path"], cwd) if "/tests/fixtures/" not in p]
    forged = hand_written_receipts(h["transcript_path"], cwd)
    if forged:
        print(json.dumps({"decision": "block", "reason":
            "SCAD stop gate: this session wrote a validation receipt itself:\n" + "\n".join(f"- {p}" for p in forged) +
            "\nOnly validate_scad.sh writes build/.validation_state.json. Delete it and run validate_scad.sh --all."}))
        return
    bad = unquoted_approvals(h["transcript_path"], cwd, edited)
    if bad:
        print(json.dumps({"decision": "block", "reason":
            "SCAD stop gate: acceptance.lock / limits.lock was approved with words that are in no user message "
            "of this session:\n" + "\n".join(f"- {b}" for b in bad) +
            "\nOnly the user approves acceptance numbers and limits. Show them the numbers, wait for their "
            "answer, and run approve --quote with one whole message (or one whole line) they typed, at least "
            f"{MIN_QUOTE} characters."}))
        return
    stale = [p for p in edited if p.endswith(".scad") and os.path.isfile(p) and not validated(p)]
    stale += [p for p in stale_declarations(edited) if p not in stale]
    if not stale:
        return
    lines = [f"- {p}\n  run: {command_for(p) if p.endswith('.scad') else cmd_all(p)}" for p in stale]
    print(json.dumps({"decision": "block", "reason":
        "SCAD stop gate: these .scad / declaration files changed after their last validate_scad.sh run "
        "(no matching sha256 in build/.validation_state.json):\n" + "\n".join(lines) +
        "\nRun it, then report its CHECK_RESULT and COVERAGE lines to the user. If it cannot "
        "run (CHECK_RESULT env=FAIL), say so plainly and do not call the part done."}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
