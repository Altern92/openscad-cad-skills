#!/usr/bin/env python3
"""tests/geom_mutation.py -- periodic geometric mutation test (audit 2026-11-02 §5 #3).

The one critical failure class is "gates PASS, geometry wrong". `gm_br_orientation`
and `gm_bbox_tight` in run_all.sh pin two cases; this script measures the CLASS.

For every golden fixture:
  1. emit the part (declarations come from the TRUE parameters);
  2. for every parameter in the `kit_<kind>(...)` call, write mutants that change
     ONLY the geometry -- the `// EXPECTED_*` lines stay as they were:
       * numbers:   x0.6 (gross) and +0.2 mm (subtle)
       * hole size: the next size in the kit hole table (M5 -> M6, ...)
  3. render + run the scad-modeler gates on each mutant.

Outcome per mutant:
  killed_gate    gates exit != 0           (good: the gates saw it)
  killed_assert  the kit's assert() refused the parameters (good: never renders)
  survived       gates exit 0              (the gates are blind to this change)

Survivors are compared against `geom_mutation_baseline.tsv` (known, accepted blind
spots, each with a reason). A survivor that is NOT in the baseline is a regression:
exit 1. Run monthly (scripts/run_geom_mutation_monthly.sh) and after any gate change.

    python3 tests/geom_mutation.py                     # full run, ~5-10 min
    python3 tests/geom_mutation.py --only box,plate    # subset
    python3 tests/geom_mutation.py --update-baseline   # accept current survivors
    python3 tests/geom_mutation.py --tsv out.tsv       # also write every row

Exit: 0 no new survivors, 1 new survivor(s), 4 setup error.
Works in both layouts (GenKit repo; scad-modeler/tests/genkit/).
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TESTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TESTS)
if not os.path.isfile(os.path.join(ROOT, "gen", "emit_part.py")):
    ROOT = os.path.dirname(ROOT)
EMIT = os.path.join(ROOT, "gen", "emit_part.py")
BASELINE = os.path.join(TESTS, "geom_mutation_baseline.tsv")
GATE = os.environ.get("SCAD_GATE") or (
    os.path.join(ROOT, "scripts", "validate_scad.sh")
    if os.path.isfile(os.path.join(ROOT, "scripts", "validate_scad.sh"))
    else os.path.expanduser("~/Skills-plugins-etc/skills/scad-modeler/scripts/validate_scad.sh"))

CALL_RE = re.compile(r"^(kit_\w+)\((.*)\);\s*$", re.M)
ARG_RE = re.compile(r"(\w+)\s*=\s*(\"[^\"]*\"|[^,]+)")
HOLE_ORDER = ["M2", "M2.5", "M3", "M4", "M5", "M6", "M8", "M10", "M12"]


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def mutations(name, raw):
    """(label, new_raw) pairs for one parameter."""
    raw = raw.strip()
    if raw.startswith('"'):
        val = raw.strip('"')
        if val in HOLE_ORDER:
            i = HOLE_ORDER.index(val)
            j = i + 1 if i + 1 < len(HOLE_ORDER) else i - 1
            return [(f"{val}->{HOLE_ORDER[j]}", f'"{HOLE_ORDER[j]}"')]
        return []
    if raw in ("true", "false"):
        return [(f"{raw}->{'false' if raw == 'true' else 'true'}",
                 "false" if raw == "true" else "true")]
    try:
        v = float(raw)
    except ValueError:
        return []          # vectors/expressions: not mutated (no such params today)
    out = [("+0.2mm", fmt(v + 0.2))]
    if v != 0:
        out.insert(0, ("x0.6", fmt(v * 0.6)))
    return out


def gate_run(job):
    fixture, param, label, scad_text = job
    d = tempfile.mkdtemp(prefix="gm_")
    try:
        p = os.path.join(d, "part.scad")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(scad_text)
        r = subprocess.run(["openscad", "-o", os.path.join(d, "probe.stl"), p],
                           capture_output=True, text=True)
        if r.returncode != 0:
            log = r.stderr + r.stdout
            # Only a kit assert() counts as a kill; a parser/IO error is a harness bug.
            msg = next((l for l in log.splitlines() if "KLAIDA" in l), None)
            if msg is None or "assert" not in log.lower():
                first = next((l for l in log.splitlines() if "ERROR" in l), "render failed")
                return (fixture, param, label, "error", first.strip()[:120])
            return (fixture, param, label, "killed_assert", msg.strip()[:120])
        g = subprocess.run(["bash", GATE, "part.scad"], cwd=d,
                           capture_output=True, text=True)
        out = g.stdout + g.stderr
        if g.returncode == 0:
            return (fixture, param, label, "survived", "")
        fails = [l.split()[1] for l in out.splitlines()
                 if l.startswith("CHECK_RESULT") and ("=FAIL" in l or "=INCONCLUSIVE" in l)]
        return (fixture, param, label, "killed_gate", ",".join(fails) or f"exit {g.returncode}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def load_baseline():
    known = {}
    if os.path.isfile(BASELINE):
        for line in open(BASELINE, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            known[tuple(parts[:3])] = parts[3] if len(parts) > 3 else ""
    return known


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", help="comma-separated fixture names")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--tsv", help="write every row here")
    a = ap.parse_args()

    if not os.path.isfile(GATE):
        print(f"SKIP: scad-modeler gates not found ({GATE})", file=sys.stderr)
        return 4
    if shutil.which("openscad") is None:
        print("ERROR: openscad not on PATH", file=sys.stderr)
        return 4

    only = set(a.only.split(",")) if a.only else None
    fixtures = sorted(f for f in os.listdir(os.path.join(TESTS, "fixtures")) if f.endswith(".json"))
    jobs = []
    for f in fixtures:
        name = f[:-5]
        if only and name not in only:
            continue
        tmp_scad = os.path.join(tempfile.gettempdir(), f"gm_emit_{os.getpid()}_{name}.scad")
        r = subprocess.run([sys.executable, EMIT, os.path.join(TESTS, "fixtures", f), "-o", tmp_scad],
                           capture_output=True, text=True)
        text = open(tmp_scad, encoding="utf-8").read() if r.returncode == 0 else ""
        if os.path.exists(tmp_scad):
            os.remove(tmp_scad)
        m = CALL_RE.search(text)
        if r.returncode != 0 or not m:
            print(f"ERROR: cannot emit {f}: {r.stderr.strip()[:200]}", file=sys.stderr)
            return 4
        for am in ARG_RE.finditer(m.group(2)):
            pname, raw = am.group(1), am.group(2)
            for label, new in mutations(pname, raw):
                args = m.group(2)[:am.start(2)] + new + m.group(2)[am.end(2):]
                mutated = text[:m.start(2)] + args + text[m.end(2):]
                jobs.append((name, pname, label, mutated))

    print(f"GATE: {GATE}")
    print(f"{len(jobs)} mutants over {len({j[0] for j in jobs})} fixtures, {a.jobs} workers")
    with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        rows = sorted(ex.map(gate_run, jobs))

    known = load_baseline()
    new = [r for r in rows if r[3] == "survived" and r[:3] not in known]
    gone = [k for k in known if not any(r[:3] == k and r[3] == "survived" for r in rows)
            and (not only or k[0] in only)]

    for r in rows:
        tag = {"killed_gate": "KILL", "killed_assert": "ASRT", "survived": "SURV",
               "error": "ERR!"}[r[3]]
        mark = "  NEW" if r in new else ""
        print(f"{tag} {r[0]:18s} {r[1]:10s} {r[2]:10s} {r[4]}{mark}")

    k_g = sum(r[3] == "killed_gate" for r in rows)
    k_a = sum(r[3] == "killed_assert" for r in rows)
    s = sum(r[3] == "survived" for r in rows)
    errs = [r for r in rows if r[3] == "error"]
    print("----------------------------------------------------------------")
    print(f"{len(rows)} mutants: {k_g} killed by gates, {k_a} by kit asserts, "
          f"{s} survived ({len(new)} new, {s - len(new)} known), {len(errs)} harness errors")
    if gone:
        print(f"{len(gone)} baseline survivor(s) are now killed -- tighten the baseline "
              "with --update-baseline:")
        for k in gone:
            print("  " + " ".join(k))

    if a.tsv:
        with open(a.tsv, "w", encoding="utf-8") as fh:
            fh.write("fixture\tparam\tmutation\toutcome\tdetail\n")
            for r in rows:
                fh.write("\t".join(r) + "\n")

    if errs:
        print("HARNESS ERRORS -- mutants that did not render for a reason other than a kit "
              "assert; the run is not a measurement:")
        for r in errs:
            print(f"  {r[0]} {r[1]} {r[2]}: {r[4]}")
        return 4
    if a.update_baseline:
        with open(BASELINE, "w", encoding="utf-8") as fh:
            fh.write("# Known geometric blind spots: mutants that change geometry but pass the gates.\n"
                     "# fixture\tparam\tmutation\treason -- keep a reason on every line.\n")
            for r in rows:
                if r[3] == "survived":
                    fh.write("\t".join(r[:3]) + "\t" + known.get(r[:3], "TODO: reason") + "\n")
        print(f"baseline written: {BASELINE}")
        return 0

    if new:
        print("NEW SURVIVORS -- the gates now pass geometry they did not pass before "
              "(or a new parameter is uncovered):")
        for r in new:
            print(f"  {r[0]} {r[1]} {r[2]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
