# 10 — Measured knowledge from the audit (2026-11-01)

Everything here is **measured**, not read. Every claim has a command that reproduces it.

## 1. Time breakdown (canonical model, 8k triangles)

`validate_scad.sh --all` = **5.77 s**.

| Component | Time | How measured |
|---|---|---|
| OpenSCAD subprocesses (7 calls) | 1.69 s | a shim wrapping every `openscad` invocation |
| `render` gate | ~2.0 s | `validation_log` timestamps |
| `collisions` (positioned render + FCL) | ~2.0 s | same |
| ~19 Python process startups | 1.2–1.5 s | 19 × 60–80 ms |
| One checker on an already-built STL | 0.02–0.03 s | `/usr/bin/time -p` |

**Conclusion:** the 4.8 s line is **not** Python's fault. Rust would save ~30 % (startup), not 10×.

```bash
mkdir -p /tmp/shim && cat > /tmp/shim/openscad <<'EOF'
#!/bin/bash
s=$(perl -MTime::HiRes=time -e 'printf "%.3f", time')
$HOME/.local/bin/openscad "$@"; rc=$?
e=$(perl -MTime::HiRes=time -e 'printf "%.3f", time')
echo "$s $e $*" >> /tmp/openscad_calls.log
exit $rc
EOF
chmod +x /tmp/shim/openscad
PATH=/tmp/shim:$PATH bash <skill>/scripts/validate_scad.sh --all
awk '{sum+=$2-$1} END {printf "openscad: %.2f s\n", sum}' /tmp/openscad_calls.log
```

## 2. Gate inventory (~21 checks after the 2026-11-01 rewrite)

| Gate | When it runs | What it catches | Note |
|---|---|---|---|
| `env` | always | missing Python module / library | exit 5 = ENV_FAIL |
| `analytic_bounds` | always | `assert()` in `params.scad` | cheapest |
| `margin_provenance` | always | assert without a clearance term | |
| `param_context` | always | `use_param()` contexts | opt-in via `use_param()` |
| `scad_lint` | always | numeric defaults, rounded standards | |
| `assumptions` | if `calculations.md` | unresolved `Critical` rows | missing file → SKIP |
| `service_envelope` | if `service_envelope.md` | blank fields | **missing → SKIP** (was PASS) |
| `plan` | if `plan.md` | 2+ architectures, confirmed decision | **missing → SKIP** (was PASS) |
| `declarations` | always | parts without `EXPECTED_BBOX` | **new**; forces declarations |
| `render` | always | empty STL | |
| `connectivity` | always | multiple bodies | |
| `bore_reachability` | if `bores.json` | enclosed cavity | |
| `attachment` | if `attachments.json` | nothing to fasten to | |
| `subfeature_overlap` | if `// SUBFEATURES` | hidden overlap | |
| `collisions` | if 2+ positioned parts | interference / clearance | |
| `mechanics` | if `motion` | motion sweep | |
| `dimensions` | **if `// EXPECTED_BBOX`** | wrong size | opt-in until the generator writes it |
| `features` | **if `// EXPECTED_HOLE`** | undersized bore, wrong plane | |
| `topology` | **if `// EXPECTED_THROUGH_HOLES`** | blind bore | |
| `printability` | always | overhang / thin walls | ADVISORY (non-gating) |
| `intake` | if `design_manifest.json` | schema-valid manifest | was hard-coded SKIP |
| `dependencies` | `--change` | change propagation | on demand |

## 3. Defects to know (with reproduction)

### 3.1 `SKIP` + "All validations passed"

```bash
cd /tmp/scad-audit/base          # canonical example, no EXPECTED_BBOX
bash <skill>/scripts/validate_scad.sh --all | tail -1
# (before 2026-11-01) All validations passed.
```

### 3.2 A gear 62 % too thin passes

```bash
sed -i '' 's/gear_thickness = 8;/gear_thickness = 3;/' params.scad
bash <skill>/scripts/validate_scad.sh --all | tail -1   # All validations passed.
python3 <skill>/scripts/check_rules.py --project-dir .  # exit 0
```

### 3.3 `intake` never fired

```bash
grep -n "intake=SKIP" <skill>/scripts/validate_scad.sh   # was hard-coded (~line 884)
```

### 3.4 `INCONCLUSIVE` → exit 0

```bash
# a project with joints.json "motion" but no assembly.scad
bash <skill>/scripts/validate_scad.sh --all | grep -E "mechanics|All validations"
# CHECK_RESULT mechanics=INCONCLUSIVE ; All validations passed.   (before the fix)
```

### 3.5 FCL coplanar 40 mm

```bash
# two parts with exactly coincident faces (boolean intersection = 0)
bash <skill>/scripts/validate_scad.sh --all | grep INTERFERENCE
# DECLARED INTERFERENCE OUT OF RANGE ... penetration depth is 40.000 mm
# check: trimesh intersection volume == 0.0
```

### 3.6 Interpreter drift

```bash
python3 <skill>/scripts/check_rules.py --project-dir . ; echo $?   # 3 (false FAIL, pre-fix)
PATH="$HOME/.local/share/scad-modeler/venv/bin:$PATH" python3 <skill>/scripts/check_rules.py --project-dir . ; echo $?  # 0
```

### 3.7 Template module name

```bash
grep -n "module part_geometry" <skill>/templates/part_template.scad
# §6 dispatch expects a module named after the part
```

### 3.8 Coordinate contradiction

```bash
grep -n "assembly coordinates" <skill>/templates/bores.json
grep -n "local" <skill>/scripts/check_attachment.py
```

## 4. Dead-gate statistics (8 685 runs)

```python
# ~/.claude/scad_modeler/validation_log/validation_log.jsonl
plan:              436 PASS, 0 FAIL
service_envelope:  436 PASS, 0 FAIL
intake:            323 SKIP, 0 PASS, 0 FAIL
```

**Lesson:** a gate that never moves is decoration, not protection. In your own `run_all.sh`, check
**specific** `CHECK_RESULT` lines, not the overall exit code.

## 5. Quick self-checks

```bash
openscad -o /dev/null kit/<module>.scad && echo OK            # does it render at all
python3 <skill>/scripts/stl_extent.py /tmp/x.stl              # real bbox (not the declaration)
python3 <skill>/scripts/check_topology.py --stl /tmp/x.stl --scad kit/<module>.scad
bash <skill>/scripts/validate_scad.sh /tmp/x.scad             # one file through all gates
```

## 6. Numbers worth remembering

| Number | Meaning |
|---|---|
| ~21 | gates in `--all` after the rewrite |
| 82 | skill tests (`run_all.sh`) |
| 53 | GenKit tests |
| 4.8–5.8 s | one full cycle |
| 1.69 s | the OpenSCAD share |
| 0 | how often `plan`/`service_envelope` failed in 436 runs (before the fix) |
| 3 | the most expensive gates that were opt-in |
| 40 mm | FCL phantom penetration on coplanar faces |
