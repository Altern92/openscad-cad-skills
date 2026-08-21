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


def load_json_maybe(path):
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def find_requirement_usages(joints_data, bores_data, affected_basenames):
    """Which declared contacts/motion drivers/bores name a part whose file
    is in affected_basenames (case-insensitive substring, same convention
    check_collisions.py/check_bore_reachability.py use for STL matching).

    This is the "requirement influence" layer check_dependencies.py's plain
    parameter DAG doesn't have on its own: knowing that params.scad's
    `worm_wheel_teeth` change reaches `output_gear.scad` (a FILE-level fact)
    doesn't say WHICH declared checks now need re-verifying -- the declared
    gear_mesh contact between output_gear and jackshaft, or the motion sweep
    driver on output_gear, or a bore declared on it in bores.json. Confirmed
    directly as a real gap: the actual esp32_rc_modelis incident this was
    built for was exactly a parameter change (worm_wheel_teeth 20->40) whose
    downstream effect on a DECLARED CONTACT's validity went unnoticed for
    multiple validation rounds (INCIDENTS.md, 2026-08-19/21).
    """
    affected = {b.lower() for b in affected_basenames}

    def name_hits(name):
        n = str(name).lower()
        return any(n in b or b in n for b in affected)

    contacts, motion, bores = [], [], []
    if isinstance(joints_data, dict):
        for c in joints_data.get("contacts", []) or []:
            pair = c.get("pair", [])
            if len(pair) == 2 and any(name_hits(p) for p in pair):
                contacts.append(pair)
        for m in joints_data.get("motion", []) or []:
            for d in m.get("drivers", []) or []:
                if name_hits(d.get("part", "")):
                    motion.append(m.get("id", "?"))
                    break
    elif isinstance(joints_data, list):
        for c in joints_data:
            pair = c.get("pair", [])
            if len(pair) == 2 and any(name_hits(p) for p in pair):
                contacts.append(pair)
    if isinstance(bores_data, list):
        for b in bores_data:
            if name_hits(b.get("part", "")):
                bores.append(b.get("name", "?"))
    return contacts, motion, bores


EDIT_CLASSES = {
    "C1": ("no downstream part or declared requirement",
           "recalculate affected formulas/asserts only -- no render needed"),
    "C2": ("reaches a part file, but no declared cross-part contact, motion, or bore",
           "part-local geometry (connectivity/bbox/features) for the affected part(s)"),
    "C3": ("reaches a declared bore",
           "the affected part(s) plus check_bore_reachability.py for the affected bore(s)"),
    "C4": ("reaches a declared cross-part contact",
           "the affected part(s) plus check_collisions.py for the affected contact(s)"),
    "C5": ("reaches a declared motion driver",
           "full validate_scad.sh --all -- a motion/ratio change invalidates the static "
           "collision precondition AND the sweep, not just one local check"),
}


def classify_edit(affected_basenames, contacts, motion, bores):
    """Map a change to the cheapest class of re-validation it actually needs,
    from strongest to weakest downstream reach (C5 > C4 > C3 > C2 > C1) --
    derived from signals this script actually has (which parts/contacts/
    motion/bores a change reaches), not guessed. There is no C0 here: this
    tool tracks variable assignments, not comments/labels, so "no textual
    effect at all" isn't something it can observe -- C1 (reaches nothing
    tracked) is the weakest class it can actually distinguish.

    This is advisory classification, not an execution mode: it names what
    the MINIMUM validation should be, but per SKILL.md §7 and
    change_propagation.md's own fallback policy, the full chain remains the
    safe default whenever there's any doubt about whether the classification
    itself is complete (e.g. this tokenizer missed a construct).
    """
    if motion:
        return "C5"
    if contacts:
        return "C4"
    if bores:
        return "C3"
    if affected_basenames:
        return "C2"
    return "C1"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scad", required=True, help="source .scad file (e.g. params.scad)")
    ap.add_argument("--all", action="store_true", help="dump the full dependency graph as JSON")
    ap.add_argument("--change", metavar="VAR", help="print the affected chain for this variable")
    ap.add_argument("--parts-dir", metavar="DIR", help="directory of part .scad files to scan for usages")
    ap.add_argument("--joints", metavar="PATH", default="joints.json",
                     help="joints.json to cross-reference for affected declared contacts/motion "
                          "(default: joints.json in the current directory, skipped if absent)")
    ap.add_argument("--bores", metavar="PATH", default="bores.json",
                     help="bores.json to cross-reference for affected declared bores "
                          "(default: bores.json in the current directory, skipped if absent)")
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
    affected_basenames = [os.path.splitext(fn)[0] for fn in usages]

    joints_data = load_json_maybe(args.joints)
    bores_data = load_json_maybe(args.bores)
    contacts, motion, bores = find_requirement_usages(joints_data, bores_data, affected_basenames)

    downstream = ", ".join(v for v in ordered if v != args.change) or "(none)"
    parts_line = ", ".join(f"{fn} ({', '.join(v)})" for fn, v in usages.items()) or "(none)"
    edges_line = ", ".join(f"{e['from']}->{e['to']}" for e in direct_edges) or "none"
    contacts_line = ", ".join(f"{p[0]}<->{p[1]}" for p in contacts) or "(none)"
    motion_line = ", ".join(motion) or "(none)"
    bores_line = ", ".join(bores) or "(none)"

    edit_class = classify_edit(affected_basenames, contacts, motion, bores)
    class_desc, class_min_validation = EDIT_CLASSES[edit_class]

    print(f"Change: {args.change} (line {assignments[args.change][1]} in {args.scad})")
    print(f"  expr  - {downstream}")
    print(f"  parts - {parts_line}")
    print(f"  edges - {len(direct_edges)} dependency edge(s): {edges_line}")
    print(f"  edit class - {edit_class} ({class_desc})")
    print(f"    minimum validation - {class_min_validation}")
    if joints_data is not None or bores_data is not None:
        print(f"  requirement influence (from {args.joints}/{args.bores}, if present):")
        print(f"    contacts affected - {contacts_line}")
        print(f"    motion affected   - {motion_line}")
        print(f"    bores affected    - {bores_line}")
        if contacts or motion or bores:
            print("    -> re-run check_collisions.py / motion_sweep.py / "
                  "check_bore_reachability.py for these specifically, not just "
                  "the file-level parts above -- a part being 'affected' doesn't "
                  "by itself say a DECLARED requirement on it needs re-checking.")
    print("  NOTE  - per change_propagation.md: if any construct was unparsed,"
          " re-run validate_scad.sh --all instead of trusting this subset. This "
          "is advisory scoping, not an automated skip mechanism -- when in doubt,"
          " the full validate_scad.sh --all remains the safe default (SKILL.md §7).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
