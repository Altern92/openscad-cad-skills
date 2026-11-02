#!/usr/bin/env python3
"""tests/p5/run_p5.py — P5 bėgimas pagal docs/08 protokolą.

Kiekvienam prašymui: requirements.json (jau paruoštas ranka, BE iteracijų) →
generatorius → vartai. Fiksuoja: ar 1-as ratas PASS, ar atsisakyta sąžiningai.

Naudojimas:
    python3 tests/p5/run_p5.py            # bėgimas + markdown lentelė
    python3 tests/p5/run_p5.py --json     # tik JSON suvestinė

Pastaba: briefs.json čia yra SINTETINIAI prašymai (žr. docs/08 §Sintetinis
bėgimas). Tikra P5 reikalauja vartotojo sakinių ir pildoma atskirai.
"""
import json
import os
import subprocess
import sys

TESTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Two layouts: GenKit repo (tests/ next to gen/) and scad-modeler/tests/genkit/.
ROOT = os.path.dirname(TESTS)
if not os.path.isfile(os.path.join(ROOT, "gen", "emit_part.py")):
    ROOT = os.path.dirname(ROOT)
TMP = "/tmp/genkit_p5"
# Inside the skill, use the gates of the same tree; otherwise the canon.
GATE = os.environ.get("SCAD_GATE") or (
    os.path.join(ROOT, "scripts", "validate_scad.sh")
    if os.path.isfile(os.path.join(ROOT, "scripts", "validate_scad.sh"))
    else os.path.expanduser("~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh"))


def run(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def main():
    path = os.path.join(TESTS, "p5", "briefs.json")
    for i, a in enumerate(sys.argv):
        if a == "--briefs" and i + 1 < len(sys.argv):
            path = sys.argv[i + 1]
            if not os.path.isabs(path) and not os.path.exists(path):
                # "tests/p5/x.json" (GenKit-relative) works in both layouts.
                rel = path[len("tests/"):] if path.startswith("tests/") else path
                path = os.path.join(TESTS, rel)
    briefs = json.load(open(path, encoding="utf-8"))
    os.makedirs(TMP, exist_ok=True)
    rows = []

    for b in briefs:
        doc = {
            "version": 1,
            "kind": b["kind"],
            "params": b["params"],
            "assumptions": [b["note"]],
            "source": {"brief": b["brief"], "date": "2026-11-01"},
        }
        jpath = os.path.join(TMP, f"p5_{b['id']}.json")
        with open(jpath, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)

        row = {"id": b["id"], "brief": b["brief"], "kind": b["kind"],
               "first_pass": False, "refused": False, "detail": b["note"]}

        if b["kind"] == "custom":
            r = run([sys.executable, os.path.join(ROOT, "gen/emit_part.py"), jpath,
                     "-o", os.path.join(TMP, f"p5_{b['id']}.scad")])
            row["refused"] = r.returncode == 4
            row["detail"] = "atsisakyta (unsupported_kind) — teisinga elgsena"
            rows.append(row)
            continue

        bdir = os.path.join(TMP, f"b_{b['id']}")
        os.makedirs(bdir, exist_ok=True)
        scad = os.path.join(bdir, "assembly.scad" if b["kind"] == "box_with_lid" else f"p5_{b['id']}.scad")
        r = run([sys.executable, os.path.join(ROOT, "gen/emit_part.py"), jpath, "-o", scad])
        if r.returncode != 0:
            row["detail"] = f"emit exit {r.returncode}: {r.stderr.strip().splitlines()[:2]}"
            rows.append(row)
            continue

        if os.path.exists(GATE):
            gate_arg = "--all" if os.path.isdir(os.path.join(bdir, "parts")) else scad
            g = run(["bash", GATE, gate_arg], cwd=bdir)
            out = g.stdout + g.stderr
            ok = g.returncode == 0 and " 0 failed," in out and " 0 inconclusive," in out
            row["first_pass"] = ok
            if not ok:
                fails = [l for l in out.splitlines() if l.startswith("CHECK_RESULT") and "FAIL" in l]
                row["detail"] = "; ".join(fails[:3]) or "vartai nepaleido"
        rows.append(row)

    ok = sum(1 for r in rows if r["first_pass"])
    refused = sum(1 for r in rows if r["refused"])
    if "--json" in sys.argv:
        print(json.dumps({"rows": rows, "first_pass": ok, "refused": refused}, ensure_ascii=False, indent=2))
        return 0

    print(f"BRIEFS: {os.path.relpath(path, ROOT)}")
    print("| # | Prašymas | Modulis | 1-as ratas PASS? | Atsisakė? | Pastabos |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        mark = "✓" if r["first_pass"] else ("—" if r["refused"] else "✗")
        ref = "✓" if r["refused"] else "—"
        print(f"| {r['id']} | {r['brief']} | {r['kind']} | {mark} | {ref} | {r['detail']} |")
    print()
    print(f"Vieno karto sėkmė: {ok}/{len(rows)}; sąžiningai atsisakyta: {refused}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
