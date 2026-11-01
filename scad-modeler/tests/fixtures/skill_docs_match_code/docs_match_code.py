#!/usr/bin/env python3
"""P11 (2026-11-01): every script a skill doc names must exist, and every --flag
given after a `scripts/X` reference must appear in X's source. Uber's MCP registry
measured 9.93% of tool descriptions out of step with their code; this is that
check for our SKILL.md + references. Usage: docs_match_code.py REPO_ROOT"""
import glob, os, re, sys

root = sys.argv[1]
docs = glob.glob(os.path.join(root, "*", "SKILL.md")) + glob.glob(os.path.join(root, "*", "references", "*.md"))
code = {}
for p in glob.glob(os.path.join(root, "**", "*.py"), recursive=True) + glob.glob(os.path.join(root, "**", "*.sh"), recursive=True):
    if "/.git/" not in p:
        code.setdefault(os.path.basename(p), p)
for p in glob.glob(os.path.join(root, "scad-modeler", "scripts", "*")):  # the canonical copy wins
    code[os.path.basename(p)] = p

bad = []
for d in docs:
    rel = os.path.relpath(d, root)
    for n, line in enumerate(open(d, encoding="utf-8"), 1):
        line = line.replace("\\n", " ")  # mermaid labels carry a literal \n
        for s in re.findall(r"(?<![\w/.-])([A-Za-z0-9_]+\.(?:py|sh))\b", line):
            if s not in code:
                bad.append(f"{rel}:{n}: names {s}, which is not in the repo")
        for m in re.finditer(r"scripts/([A-Za-z0-9_]+\.(?:py|sh))", line):
            if m.group(1) not in code:
                bad.append(f"{rel}:{n}: names scripts/{m.group(1)}, which is not in the repo")
                continue
            tail = re.split(r"[`|#;)]|&&|scripts/", line[m.end():])[0]  # up to the next command
            src = open(code[m.group(1)], encoding="utf-8").read()
            for f in re.findall(r"(?<![\w-])(--[a-z][a-z0-9-]*)", tail):
                if f not in src:
                    bad.append(f"{rel}:{n}: {m.group(1)} {f} -- flag not in {os.path.relpath(code[m.group(1)], root)}")
print("\n".join(bad) if bad else f"OK: {len(docs)} docs match the code")
sys.exit(1 if bad else 0)
