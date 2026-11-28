#!/usr/bin/env python3
"""Score bench runs: runs/<id>/answer.json against tasks.json ranges; also report whether any .scad renders.
Usage: score.py [runs_dir]   Prints one line per task and a total; exit 0 always (it is a report)."""
import glob, json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
runs = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "runs")
tasks = json.load(open(os.path.join(here, "tasks.json")))["tasks"]


def score(t, d):
    try:
        a = json.load(open(os.path.join(d, "answer.json")))
    except (OSError, ValueError):
        return 0, len(t["answer_keys"]), ["no readable answer.json"]
    ok, notes = 0, []
    for k, (lo, hi) in t["answer_keys"].items():
        v = a.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi:
            ok += 1
        else:
            notes.append(f"{k}={v!r} not in [{lo}, {hi}]")
    return ok, len(t["answer_keys"]), notes


def renders(d):
    scads = sorted(glob.glob(os.path.join(d, "**", "*.scad"), recursive=True))
    if not scads:
        return None
    # the first top-level-looking file: assembly.scad, else any
    main = next((s for s in scads if os.path.basename(s) == "assembly.scad"), scads[0])
    r = subprocess.run(["openscad", "-o", os.devnull, "--export-format", "binstl", main], capture_output=True, timeout=600)
    return r.returncode == 0


if __name__ == "__main__":
    tot = got = 0
    for t in tasks:
        d = os.path.join(runs, t["id"])
        if not os.path.isdir(d):
            print(f"SKIP {t['id']}: not run"); continue
        ok, n, notes = score(t, d)
        got += ok; tot += n
        meta = {}
        try:
            meta = json.load(open(os.path.join(d, "claude.json")))
        except (OSError, ValueError):
            pass
        print(f"{'PASS' if ok == n else 'PART' if ok else 'FAIL'} {t['id']}: {ok}/{n} answers, renders={renders(d)}, "
              f"{meta.get('duration_ms', 0) / 60000:.1f} min, cost_equiv ${meta.get('total_cost_usd', 0):.2f}"
              + "".join(f"\n     {x}" for x in notes))
    print(f"total {got}/{tot} answer values in range")
