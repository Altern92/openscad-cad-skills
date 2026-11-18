#!/usr/bin/env python3
"""Semantic mutants (P25 / AC-8, 2026-11-18): apply each plausible logic error from a TSV to a copy of
scripts/ and run the named fixture. Verdicts (Stryker / PIT taxonomy):
  KILLED          the fixture failed and no checker crashed: an assertion saw the wrong behaviour
  CRASH           the fixture failed only because something raised (Traceback) -- not credited
  SURVIVED        the fixture still passes: it does not test this logic
  NOT_APPLICABLE  the `find` text is not in the checker exactly once: the catalogue is stale
  BASELINE_RED    the fixture fails WITHOUT the mutant (environment, missing module): nothing is proven
Usage: semantic_mutants.py <scripts_dir> <fixtures_dir> <mutants.tsv>   exit 0 only if all KILLED.
Run it where the suite runs (tests/run_all.sh puts the mesh venv first on PATH)."""
import os
import shutil
import subprocess
import sys
import tempfile


def run_fixture(scripts, fixtures, name):
    env = dict(os.environ, SCAD_MODELER_SCRIPTS=scripts, SCAD_MUTANT_INNER="1")
    r = subprocess.run(["bash", "run_test.sh"], cwd=os.path.join(fixtures, name), env=env,
                       capture_output=True, text=True, timeout=900)
    return r.returncode, r.stdout + r.stderr


def main(scripts, fixtures, tsv):
    rows = [l.rstrip("\n").split("\t") for l in open(tsv, encoding="utf-8") if l.strip() and not l.startswith("#")]
    green, bad = {}, 0
    for mid, checker, find, repl, fx in rows:
        if fx not in green:
            green[fx] = run_fixture(scripts, fixtures, fx)[0] == 0
        p = os.path.join(scripts, checker + ".py")
        src = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
        if src.count(find) != 1:
            verdict = "NOT_APPLICABLE"
        elif not green[fx]:
            verdict = "BASELINE_RED"
        else:
            with tempfile.TemporaryDirectory() as t:
                # the whole skill, not scripts/ alone: checkers read ../references (a scripts-only copy
                # crashed every check_strength mutant -- a CRASH, correctly not credited)
                shutil.copytree(os.path.dirname(os.path.abspath(scripts)), os.path.join(t, "k"),
                                ignore=shutil.ignore_patterns("tests", "build", "__pycache__", ".git"))
                s = os.path.join(t, "k", os.path.basename(os.path.abspath(scripts)))
                with open(os.path.join(s, checker + ".py"), "w", encoding="utf-8") as f:
                    f.write(src.replace(find, repl.strip(), 1))   # blank replace = delete the fragment
                rc, out = run_fixture(s, fixtures, fx)
            verdict = "SURVIVED" if rc == 0 else "CRASH" if "Traceback (most recent call last)" in out else "KILLED"
        print(f"{verdict:15s} {mid}  ({checker} -> {fx})")
        bad += verdict != "KILLED"
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
