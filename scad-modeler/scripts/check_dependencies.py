#!/usr/bin/env python3
"""Change-propagation "choice tree" engine: what must be recomputed, and in
what order, when a variable in params.scad (or any .scad) changes.

Why this exists
----------------
The user's core requirement: "visada būna pasirinkimų medis — jei kazkur
kazka pakeite, zinotu, kokios detales susijusios ir ka reikia perskaiciuoti."
The blanket rule ("re-run validate_scad.sh --all after ANY change") is safe
but blind: a one-parameter edit re-renders and re-checks everything, and the
model cannot say *what* the edit affected. This script makes the dependency
structure explicit and machine-readable, so the model (and the user) see the
exact affected chain — mirroring how FreeCAD's recompute engine walks the
dependency DAG in topological order and marks only dependents dirty
(see references/change_propagation.md).

How it works (deliberately lightweight)
---------------------------------------
- Extracts top-level `name = <expr>;` assignments from a .scad file with a
  regex, then finds which *other declared variables* each expression
  references (identifier token match). No arithmetic — only name->name edges,
  exactly the information the choice tree needs.
- Builds a DAG (params -> derived params -> modules -> part files -> assembly
  is approximated as variables -> usages in other .scad files).
- `--change NAME` prints the forward closure: everything downstream of the
  edited variable, grouped by layer, plus which part files use it.
- `--all` dumps the full graph as JSON for other tools.

Limitations (stated honestly): this is a tokenizer, not a parser — it does not
understand control flow, `for` loops over variables, or function calls that
redefine names. Unknown constructs do not fail the run; they escalate to the
blanket re-run, exactly as references/change_propagation.md prescribes: "a
wrong subgraph beats a missed one" — any parse uncertainty means fall back to
`validate_scad.sh --all`. Consider tree-sitter-openscad
(npm `tree-sitter-openscad`) if a full AST is ever needed.

Usage:
    python3 check_dependencies.py --scad params.scad --all            # dump DAG
    python3 check_dependencies.py --scad params.scad --change P1_teeth  # affected chain
    python3 check_dependencies.py --scad params.scad --change P1_teeth --parts-dir parts/

Exit codes:
    0  pass
    2  changed variable not found in the file
    4  usage error
"""
import argparse
import json
import os
import re
import sys

ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*;\s*(?://.*)?$", re.M)
IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")


def parse_assignments(path):
    """Return {name: (expression, line_no)} for top-level assignments."""
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(4)
    out = {}
    for m in ASSIGN_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        out[m.group(1)] = (m.group(2), line)
    return out


def build_graph(assignments):
    """Return (nodes, edges): edges are (from_var, to_var) meaning to_var's
    expression references from_var."""
    names = set(assignments)
    nodes = []
    edges = []
    for name, (expr, line) in assignments.items():
        nodes.append({"name": name, "line": line, "expression": expr})
        for tok in IDENT_RE.findall(expr):
            if tok in names and tok != name:
                edges.append({"from": tok, "to": name})
    return nodes, edges


def forward_closure(edges, roots):
    """All variables reachable from roots by walking edges (dirty set)."""
    adj = {}
    for e in edges:
        adj.setdefault(e["from"], []).append(e["to"])
    dirty = set(roots)
    stack = list(roots)
    while stack:
        cur = stack.pop()
        for nxt in adj.get(cur, []):
            if nxt not in dirty:
                dirty.add(nxt)
                stack.append(nxt)
    return dirty


def find_part_usages(parts_dir, var_names):
    """Which part .scad files reference any of var_names."""
    hits = {}
    if not parts_dir or not os.path.isdir(parts_dir):
        return hits
    pat = re.compile(r"\b(" + "|".join(re.escape(v) for v in var_names) + r")\b")
    for fn in sorted(os.listdir(parts_dir)):
        if not fn.endswith(".scad"):
            continue
        p = os.path.join(parts_dir, fn)
        try:
            txt = open(p, encoding="utf-8").read()
        except OSError:
            continue
        found = sorted(set(pat.findall(txt)))
        if found:
            hits[fn] = found
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scad", required=True, help="source .scad file (e.g. params.scad)")
    ap.add_argument("--all", action="store_true", help="dump the full dependency graph as JSON")
    ap.add_argument("--change", metavar="VAR", help="print the affected chain for this variable")
    ap.add_argument("--parts-dir", metavar="DIR", help="directory of part .scad files to scan for usages")
    args = ap.parse_args()

    assignments = parse_assignments(args.scad)
    if not assignments:
        print("note: no top-level assignments found; nothing to graph.", file=sys.stderr)
    nodes, edges = build_graph(assignments)

    if args.all:
        print(json.dumps({"nodes": nodes, "edges": edges}, indent=2))
        return 0

    if not args.change:
        ap.error("provide --all or --change")
    if args.change not in assignments:
        print(f"error: variable '{args.change}' not found in {args.scad}", file=sys.stderr)
        return 2

    dirty = forward_closure(edges, [args.change])
    ordered = sorted(dirty, key=lambda v: (v in {args.change}, v))
    direct_edges = [e for e in edges if e["to"] in dirty]
    usages = find_part_usages(args.parts_dir, dirty)

    downstream = ", ".join(v for v in ordered if v != args.change) or "(none)"
    parts_line = ", ".join(f"{fn} ({', '.join(v)})" for fn, v in usages.items()) or "(none)"
    edges_line = ", ".join(f"{e['from']}->{e['to']}" for e in direct_edges) or "none"

    print(f"Change: {args.change} (line {assignments[args.change][1]} in {args.scad})")
    print(f"  expr  - {downstream}")
    print(f"  parts - {parts_line}")
    print(f"  edges - {len(direct_edges)} dependency edge(s): {edges_line}")
    print("  NOTE  - per change_propagation.md: if any construct was unparsed,"
          " re-run validate_scad.sh --all instead of trusting this subset.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
