# 07 — Agent workflow

This is the "start-up instruction" for an agent beginning from scratch.

## 0. Environment check (5 min)

```bash
openscad --version                 # must be 2026.x
ls ~/Documents/OpenSCAD/libraries/BOSL2/std.scad
ls ~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh
python3 --version                  # ≥ 3.11
```

If anything is missing — **STOP**, report to the user with an `ENV_FAIL:` line. Do not start coding.

## 1. Start

1. Read `HANDOFF.md`, then `NEXT.md`, `docs/01`, `docs/03`, `docs/04`, `docs/05`.
2. Take **P0** (if not done) or the first unchecked item.
3. Mark it `⏳` in `NEXT.md`.

## 2. Work loop (one item = one loop)

```
plan → implement → test → AC check → report → NEXT.md [x]
```

1. **Plan** (5–10 min): list the files you will create/change and which ACs they touch. If the plan
   requires changing `docs/03`, change the document first, then the code.
2. **Implement** in small steps; after each module run `openscad -o /dev/null <file>`.
3. **Test**: a new module without a fixture and a mutant is not done.
4. **AC check**: run the command from `docs/04` and **paste the output**.
5. **Report** per §Report.
6. **NEXT.md**: tick `[x]` only when every AC of that item is met.

## 3. Commands

```bash
cd /Volumes/SSD_1TB/Docs/03_Asmeniniai_projektai/OpenSCAD_GenKit

# one module
openscad -o /tmp/m.stl kit/plate_with_holes.scad

# generator
python3 gen/emit_part.py tests/fixtures/bracket_l.json -o /tmp/b.scad

# gates (from the skill)
bash ~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh /tmp/b.scad

# all tests
bash tests/run_all.sh
```

## 4. Definition of done

- [ ] ACs met and command output pasted
- [ ] `bash tests/run_all.sh` → `0 failed`
- [ ] `NEXT.md` updated
- [ ] No changes outside this project folder (unless the item requires it)
- [ ] If the API changed, `docs/03` updated in the same loop

## 5. Report format

```
## P<N> — <title>

What I did: <2–4 lines>
Files: <list>
AC: <ID> — <command> — <one line of output>
Tests: <N passed, M failed>
Not done / deferred: <if any, why>
Risks: <if new ones appeared>
```

**Forbidden** in a report: "everything works" without output.

## 6. When something fails

| Situation | Action |
|---|---|
| `assert` fires on a good input | Check whether the limit is justified; if not, change `docs/03` (not a silent exception) |
| Module does not render | Read the `openscad` error; do not guess |
| Generator produces a wrong bbox | `check_dimensions.py` is the oracle; fix the Python formula, not the declaration |
| Unclear AC | Ask the user **one** question with a proposal |
| A module is missing for a real brief | Record it in `docs/08_p5_measurement.md`; add the module only after gate V3 |

## 7. Do not

- Rewrite `validate_scad.sh` / `check_*.py` (P4′ exception with its own AC).
- Put parameters into SQLite (ADR-002).
- Hand-write coordinates inside a module (AC-17).
- Make "while I'm here" fixes in other files.
- Use `custom()` in the generator.

## 8. First concrete step (if starting now)

1. `NEXT.md` → P0/P6.
2. `gen/schema.json` per `docs/03` §Schema.
3. `examples/bracket_80x50.json` + `tests/fixtures/bracket_l.json`.
4. `python3 gen/validate_schema.py tests/fixtures/*.json` → 8/8 OK.
5. Only then P1.
