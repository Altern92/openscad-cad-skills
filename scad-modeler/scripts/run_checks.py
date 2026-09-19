#!/usr/bin/env python3
"""run_checks.py — vieno proceso scad-modeler check'ų paleidiklis (PROTOTIPAS).

⚠  TAI NĖRA validate_scad.sh PAKAITALAS. Dengia 9 iš 18 check'ų:
   connectivity, dimensions, features, collisions, mechanics,
   margin_provenance, param_context, assumptions, plan.
   Nepaleidžia: openscad renderių, intake, dependencies, printability,
   bore_reachability, attachment, subfeature_overlap — jiems reikia
   validate_scad.sh STL paruošimo logikos.
   Naudoti TIK kaip opt-in pagreitintuvą iteruojant prie vienos dalies;
   pilnai validacijai visada: bash scripts/validate_scad.sh --all

Matuota 2026-09-19 (examples/gear_reduction): baseline 19,34 s; šio dispečerio
dengiama dalis ~9,7 s -> ~2,0 s (warm). Visas 19,34 s -> ~11,6 s, jei būtų integruota.
Sąmoningai NEintegruota: antras orkestratorius reikštų du tiesos šaltinius.

Tikslas: trimesh/shapely/scipy/networkx importuojami VIENĄ kartą, o ne po kartą
kiekviename check'o procese (matuota: ~0,65-1,9 s importas vienam procesui).

Semantika atkartota iš validate_scad.sh:
  - connectivity: TIK parts/*.scad (niekada assembly), --stl --scad
  - dimensions:   tik jei .scad turi '// EXPECTED_BBOX'
  - features:     tik jei .scad turi '// EXPECTED_HOLE'
  - collisions:   [--expected-contacts joints.json] + positioned STL keliai
  - mechanics:    motion_sweep --joints joints.json + positioned STL keliai (jei joints.json turi motion)
  - margin_provenance / param_context / assumptions / plan: fiksuoti argumentai

Nepaleidžia: openscad renderių, intake, dependencies, printability, bore/attachment/subfeature.
Naudojimas: python3 run_checks.py [--project-dir .] [--quiet]
"""
import argparse, glob, importlib.util, io, json, os, pathlib, re, sys, time

HERE = pathlib.Path(__file__).resolve().parent
CACHE = {}


def load(name):
    if name not in CACHE:
        spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        CACHE[name] = mod
    return CACHE[name]


def run(name, argv):
    mod = load(name)
    old_argv, old_cwd = sys.argv, os.getcwd()
    buf, real_out, real_err = io.StringIO(), sys.stdout, sys.stderr
    sys.argv = [name + ".py"] + argv
    t0, rc = time.time(), 0
    try:
        sys.stdout = sys.stderr = buf
        mod.main()
    except SystemExit as e:
        rc = int(e.code or 0)
    except Exception as e:
        rc = 99
        buf.write("EXCEPTION %s: %s\n" % (type(e).__name__, e))
    finally:
        sys.stdout, sys.stderr, sys.argv = real_out, real_err, old_argv
        os.chdir(old_cwd)
    return rc, time.time() - t0, buf.getvalue()


def has_marker(scad, marker):
    return re.search(r"^[ \t]*//[ \t]*" + marker, pathlib.Path(scad).read_text(), re.M) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default=".")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    os.chdir(pathlib.Path(a.project_dir).resolve())

    t0 = time.time()
    load("check_connectivity")
    t_import = time.time() - t0

    results, timings = [], []

    def record(check, name, rc, dt):
        results.append((check, rc))
        timings.append((name, rc, dt))

    for scad in sorted(glob.glob("parts/*.scad")):
        stl = "build/" + pathlib.Path(scad).stem + ".stl"
        if not pathlib.Path(stl).exists():
            continue
        rc, dt, _ = run("check_connectivity", ["--stl", stl, "--scad", scad])
        record("connectivity", "connectivity:" + pathlib.Path(stl).name, rc, dt)
        if has_marker(scad, "EXPECTED_BBOX"):
            rc, dt, _ = run("check_dimensions", ["--stl", stl, "--scad", scad])
            record("dimensions", "dimensions:" + pathlib.Path(stl).name, rc, dt)
        if has_marker(scad, "EXPECTED_HOLE"):
            rc, dt, _ = run("check_features", ["--stl", stl, "--scad", scad])
            record("features", "features:" + pathlib.Path(stl).name, rc, dt)

    positioned = sorted(glob.glob("build/positioned/*.stl"))
    joints = pathlib.Path("joints.json")
    if len(positioned) >= 2:
        argv = (["--expected-contacts", "joints.json"] if joints.exists() else []) + positioned
        rc, dt, _ = run("check_collisions", argv)
        record("collisions", "collisions", rc, dt)
        if joints.exists() and "motion" in joints.read_text():
            rc, dt, _ = run("motion_sweep", ["--joints", "joints.json"] + positioned)
            record("mechanics", "mechanics", rc, dt)

    for mod_name, check, argv in (
            ("check_margin_provenance", "margin_provenance", ["--scad", "params.scad", "--parts-dir", "parts"]),
            ("check_param_context", "param_context", ["--project-dir", "."]),
            ("check_assumptions", "assumptions", ["--calc", "calculations.md"]),
            ("check_plan", "plan", ["--plan", "plan.md"])):
        rc, dt, _ = run(mod_name, argv)
        record(check, check, rc, dt)

    ALL = ("connectivity", "dimensions", "features", "collisions", "mechanics",
           "margin_provenance", "param_context", "assumptions", "plan")
    seen = {}
    for check, rc in results:
        if seen.get(check) == "FAIL":
            continue                      # vienas FAIL nusveria velesnius
        if rc == 0:
            seen[check] = "PASS"
        elif rc in (1, 3, 99):
            seen[check] = "FAIL"
        else:
            seen[check] = "SKIP"
    # SKIP eilutes spausdiname ir tada, kai check'as nebuvo paleistas —
    # kaip daro validate_scad.sh, kad isvestis sutaptu 1:1
    for check in ALL:
        print("CHECK_RESULT %s=%s" % (check, seen.get(check, "SKIP")))
    if not a.quiet:
        print("IMPORT_ONCE=%.2fs TOTAL=%.2fs" % (t_import, time.time() - t0))
        for name, rc, dt in sorted(timings, key=lambda r: -r[2])[:8]:
            print("  %-32s rc=%d %.2fs" % (name, rc, dt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
