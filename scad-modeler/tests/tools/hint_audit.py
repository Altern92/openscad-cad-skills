#!/usr/bin/env python3
"""P39: every checker FAIL message must say what to change ("Hint: ...").
A FAIL block = a line starting with FAIL (after optional whitespace) plus the directly following lines that
start with whitespace. Each block must contain "Hint:".

  hint_audit.py make <scripts_dir> <out_root>   build <out_root>/<scripts basename>/ whose check_*.py and
        motion_sweep.py are shims that run the REAL script (same argv/stdin/cwd/env), pass stdout/stderr through
        unchanged, return its exit code and append every hint-less FAIL block to $HINT_AUDIT_LOG. Everything
        else (and everything next to scripts/, e.g. references/) is symlinked, so validate_scad.sh finds the
        shims through its own dirname. Prints the shim scripts dir.
  hint_audit.py blocks <file>                   print the FAIL blocks of a file as `<hinted 0|1>\t<block>`"""
import os
import re
import sys

FAIL_RE = re.compile(r"^\s*FAIL")


def fail_blocks(text):
    blocks, cur = [], None
    for line in text.splitlines():
        if FAIL_RE.match(line):
            cur = [line]
            blocks.append(cur)
        elif cur is not None and line[:1] in (" ", "\t"):
            cur.append(line)
        else:
            cur = None
    return ["\n".join(b) for b in blocks]


def audit(script, text, log):
    """Count FAIL blocks of one run (HINT_AUDIT_LOG gets a `SEEN` line per block, a `MISSING` entry per bad one)."""
    with open(log, "a", encoding="utf-8") as f:
        for b in fail_blocks(text):
            f.write(f"SEEN {script}\n")
            if "Hint:" not in b:
                f.write("MISSING " + script + "\n" + b + "\n---\n")


SHIM = '''#!/usr/bin/env python3
import importlib.util, os, subprocess, sys
REAL = {real!r}
TOOL = {tool!r}
if __name__ != "__main__":      # fixtures import check_collisions / load check_fits by path: run the real code in this module
    __file__ = REAL
    exec(compile(open(REAL, encoding="utf-8").read(), REAL, "exec"), globals())
else:
    r = subprocess.run([sys.executable, REAL] + sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    sys.stderr.write(err); sys.stderr.flush()
    sys.stdout.write(out); sys.stdout.flush()
    log = os.environ.get("HINT_AUDIT_LOG")
    if log:
        s = importlib.util.spec_from_file_location("hint_audit", TOOL)
        m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
        m.audit({name!r}, out + "\\n" + err, log)
    sys.exit(r.returncode)
'''


def make(scripts, root):
    """Mirror <repo>/<skill>/<scripts>: repo and skill entries are symlinks (docs, INCIDENTS.json, references),
    scripts/ is a real dir of symlinks and shims."""
    scripts = os.path.realpath(scripts)
    skill, base = os.path.split(scripts)
    repo, sname = os.path.split(skill)
    top = os.path.join(root, os.path.basename(repo))
    os.makedirs(os.path.join(top, sname, base))
    for d, keep in ((repo, sname), (skill, base)):
        for n in os.listdir(d):
            if n != keep:
                os.symlink(os.path.join(d, n), os.path.join(top, n) if d == repo else os.path.join(top, sname, n))
    for n in os.listdir(scripts):
        src, dst = os.path.join(scripts, n), os.path.join(top, sname, base, n)
        if re.fullmatch(r"(check_.*|motion_sweep)\.py", n):
            with open(dst, "w", encoding="utf-8") as f:
                f.write(SHIM.format(real=src, tool=os.path.abspath(__file__), name=n))
        else:
            os.symlink(src, dst)
    return os.path.join(top, sname, base)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "make":
        print(make(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 3 and sys.argv[1] == "blocks":
        for b in fail_blocks(open(sys.argv[2], encoding="utf-8").read()):
            print(f"{int('Hint:' in b)}\t{b!r}")
    else:
        sys.exit(__doc__)
