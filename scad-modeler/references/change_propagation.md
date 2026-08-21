# Change-propagation choice tree

**Status note (2026-08-21):** most of this file describes the aspirational
full design (the JSON schema in §2, the boxed tree output in §4) -- what's
actually built and tested is simpler: `scripts/check_dependencies.py`'s
regex-based `name→names` parameter DAG (§1's recommended approach, real),
plus, as of 2026-08-21, a **requirement-influence cross-reference**: given
`--change VAR` and (optionally) `--joints joints.json`/`--bores bores.json`,
it reports which *declared* contacts, motion drivers, and bores are affected
-- not just which part *files* are (a file being affected doesn't say
whether a declared requirement on it needs re-checking, which is exactly
the gap that let a real `worm_wheel_teeth` parameter change go unnoticed
across multiple validation rounds, INCIDENTS.md 2026-08-19/21). This is
advisory scoping the model reads and acts on -- there is no automated
"skip everything else" execution mode, and the fallback-to-full-`--all`
policy in §3.4 below is still the load-bearing safety net, not this file's
JSON schema or boxed-tree output format, neither of which is implemented.

When a variable in `params.scad` (or a module/include) changes, this is the
"what must I recompute, and in what order?" contract. It converts the current
"re-run `validate_scad.sh --all` always" blanket approach (`validation_decision_tree.md`) into a lazy, dependency-ordered re-run — without losing the safety net
of the blanket re-run as the fallback. Model: FreeCAD's recompute engine — a recompute
traverses the dependency DAG in topological order and only marks dependents dirty
([opendeep.wiki FreeCAD recompute/transactions](http://opendeep.wiki/FreeCAD/FreeCAD/core-application-architecture.recompute-dependency-ordering-and-transactions)). We mirror that: compute a static DAG once, then on each edit find the affected root set and walk forward.

## 1. Building the DAG: which parser

- **tree-sitter-openscad** (npm: [`tree-sitter-openscad`](https://www.npmjs.com/package/tree-sitter-openscad) v0.5.1; taip pat `@holistic-stack/tree-sitter-openscad` v0.1.0; GitHub [`nymann/tree-sitter-openscad`](https://github.com/nymann/tree-sitter-openscad)) — real grammar giving `variable_definition`, `identifier`, and `call_expression` nodes, so extractor code never hand-parses and survives syntax edits. But in a Python skill repo it drags in a wasm/FFI runtime.
- **openscad-language-server** ([dzhu](https://lib.rs/crates/openscad-language-server)) is a full LSP — too heavy for a passive dependency extractor; its value is IDE hover/autocomplete, not a static graph.
- **Lightweight Python regex/tokenizer** matches the skill's existing pure-Python scripts.

**Recommendation:** the lightweight Python tokenizer, but only as the *skeleton* — paired with a **ground-truth check** that re-derives a few derived values via OpenSCAD `-D`/`echo` and asserts they match the tokenizer's computation. The tokenizer gives you top-level `name = <expr>` assignments and `use/include` statements (both are single-line-first in this skill's convention: `%l` vs `%w`); a one-pass shunting-yard over the RHS collects referenced identifiers. Exact arithmetic isn't needed — only the **name→names dependency edge**. Keep `validate_scad.sh --all` as the not trusted, always-run safety net so a tokenizer miss is contained. Chose this over tree-sitter (runtime cost with zero extra correctness) and over the LSP (out of scope).

## 2. JSON schema (ordered edges, as-built DAG)

```json
{
  "sources": {"params.scad": {"mtime": "2026-08-19T18:00Z", "sha256": ""}},
  "nodes": [
    {"id": "P1_teeth", "kind": "param", "type": "number", "derived": false,
     "declared_by": ["params.scad:22"]},
    {"id": "CD1", "kind": "param", "type": "number", "derived": true,
     "expression": "gear_dist(teeth1=P1_teeth, teeth2=S1_teeth, mod=stage1_module)",
     "uses": ["P1_teeth", "S1_teeth", "stage1_module"]}
  ],
  "edges": [
    {"from": "P1_teeth", "to": "CD1", "kind": "expression"},
    {"from": "CD1", "to": "P1_gearhousing", "kind": "module"},
    {"from": "P1_gearhousing", "to": "rear_axle.stl", "kind": "part"}
  ],
  "constraints": [{"id": "ratio_1<=>6.0", "expr": "assert(abs(ratio_1-6.0)<0.1)",
                   "uses": ["ratio_1"]}],
  "assembly": {"root": "assembly.scad", "parts": ["rear_axle", "..."]}
}
```

Nodes: params → derived params → modules (feature builders) → parts (files/`.stl`) → assembly. Edges carry `kind` so the runner can tell a *variable edge* from a *topology/part* edge. Constraints (asserts) attach to variables so a change that moves a ratio past tolerance is reported as a check, not a silent geometry change.

## 3. Algorithm: change in X → recompute set, in order

1. **Dirty-roots:** on edit of `X`, emit `dirty = {X}`; if a file `mtime` changed, add all its directly-listed params.
2. **Forward closure:** walk `edges` from each dirty node to collect downstream params, modules, parts, assembly. Mark each node's *check* dependencies:
   - param/derived-param change → recompute expression, re-run `assert`s → **Calculations** (skip `validate_scad.sh`).
   - module change → **Geometry** for that feature + its part file.
   - part change → **`validate_scad.sh --all`** for that part (connectivity/bbox/hole are dimensionless — only re-run if the changed param feeds the relevant geometry).
   - bought-part/bearing dimension (marked `@purchased`) → **opt-in fits**: press/clearance fit vs printed mate using [fit classes](https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/) → **Features/bores**.
   - assembly change or any moving gear mesh → **Situational**: sub-feature overlap → static collision → motion sweep (same order as `validation_decision_tree.md`).
3. **Topological order** by `edges`; run each check group in dependency order. A param-only change is *cheap* (no render).
4. **Fallback:** if any parse is uncertain (unknown token, `include` of an unparsed file), escalate to `validate_scad.sh --all` and log it — a wrong subgraph beats a missed one.

## 4. User-facing output

Path printed under the change, one line per affected node, grouped by layer (params → modules → parts → assembly), with rendered `.stl`/check names prefixed `[dirty]`:

```
┌ Change: P1_teeth 12→14 (params.scad:22)
│  expr  ─ ratio_1, CD1 → assert(ratio_1≈6.0) [FAIL: 4.0]  ← check
│  module─ P1_gearhousing, P2_gearhousing
│  part  ─ P1_gear.stl [dirty]  ├─ connectivity ├─ EXPECTED_BBOX
│  fit   ─ P1_bore ⊃ P1_pinion (press 0.05mm) @purchased  ├─ check_features
│  assembly─ rear_axle (static geom)  →  situational: collisions
└ Unaffected: S1, jackshaft, diff_ring  (skipped)
```

`[FAIL]` on an assert short-circuits downstream render steps and points at `calculations.md`. Leaf nodes under "Unaffected" prove the lazy scope — the user sees at a glance that only the meshing/printed-mate chain re-runs.

## Šaltinių žurnalas

| ID | Teiginys | Šaltinis | Tipas | Būsena |
|---|---|---|---|---|
| P-001 | Topo order + only-dirty recompute (FreeCAD recompute engine) | opendeep.wiki FreeCAD core | pirminis | su šaltiniu |
| P-002 | tree-sitter-openscad — npm pkg v0.5.1 (taip pat @holistic-stack v0.1.0; GitHub nymann/tree-sitter-openscad) | npmjs.com/package/tree-sitter-openscad, github.com/nymann/tree-sitter-openscad | pirminis | su šaltiniu |
| P-003 | openscad-language-server is an LSP, not a static extractor | lib.rs/crates/openscad-language-server | pirminis | su šaltiniu |
| P-004 | Printed-assembly fit classes (clearance/press/interference) | aon3d.com/engineering-fits | pirminis | su šaltiniu |