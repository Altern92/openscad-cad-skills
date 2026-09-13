#!/usr/bin/env python3
"""mutation_test.py -- does the grader actually REJECT wrong answers?

Usage: mutation_test.py <grader.py> <answers_dir> [answer_glob]

Mutation testing asks whether a test suite can tell a correct result from a
nearly-correct one. Here the "mutant" is a real answer that passes, with one
FORBIDDEN phrase appended; the grader must reject it. If it still passes, the
mutant survived -- and that case is not measuring what it claims to measure.

Because a grader's forbidden-phrase list lives in its own source, this script
extracts RUBRIC from the grader file rather than duplicating it. That keeps the
two in sync: edit the rubric, the mutation test follows.

CAVEAT, and it matters: the mutants are weak. "Forbidden phrases" are things a
model rarely says, so a high score here proves the grader catches OBVIOUS wrong
answers -- not subtle ones. A stronger test mutates with plausible errors. Treat
the score as a floor, never as evidence the grader is good.

Measured 2026-09-12 against golden_scad/run_2026-09-11/grader.py: 9/9 = 100%.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile


def load_rubric(grader_path):
    src = open(grader_path, encoding="utf-8").read()
    m = re.search(r"RUBRIC = (\{.*?\n\})", src, re.S)
    if not m:
        raise SystemExit("could not find RUBRIC = {...} in " + grader_path)
    return eval(m.group(1))                              # noqa: S307 -- local rubric file


def main():
    if len(sys.argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    grader_path = os.path.abspath(sys.argv[1])
    answers_dir = sys.argv[2]
    pattern = sys.argv[3] if len(sys.argv) > 3 else "*.md"

    rubric = load_rubric(grader_path)
    answers = {}
    for path in sorted(glob.glob(os.path.join(answers_dir, pattern))):
        cid = re.search(r"(SCAD-\d+)", os.path.basename(path))
        if cid and cid.group(1) not in answers:
            answers[cid.group(1)] = open(path, encoding="utf-8").read()

    print("answers found: %d" % len(answers))
    print()
    print("%-10s %-10s %-10s %s" % ("case", "mutants", "killed", "verdict"))
    killed = total = 0
    survived = []
    for cid in sorted(rubric):
        if cid not in answers:
            print("%-10s %s" % (cid, "-- no answer to mutate"))
            continue
        groups = rubric[cid].get("forbidden", [])
        n_kill = 0
        for group in groups:
            mutant = answers[cid] + "\n\nBe to, " + group[0] + ".\n"
            with tempfile.TemporaryDirectory() as td:
                shutil.copy(grader_path, os.path.join(td, "grader.py"))
                with open(os.path.join(td, cid + ".md"), "w", encoding="utf-8") as fh:
                    fh.write(mutant)
                proc = subprocess.run([sys.executable, os.path.join(td, "grader.py")],
                                      capture_output=True, text=True, cwd=td)
            total += 1
            if re.search(r"^%s\s.*FAIL" % cid, proc.stdout, re.M):
                killed += 1
                n_kill += 1
            else:
                survived.append((cid, group[0]))
        print("%-10s %-10d %-10d %s"
              % (cid, len(groups), n_kill,
                 "all killed" if n_kill == len(groups) else "*** SURVIVED ***"))

    print()
    print("MUTATION SCORE: %d/%d = %.0f%%"
          % (killed, total, 100.0 * killed / total if total else 0))
    if survived:
        print()
        print("surviving mutants (the grader does not see these):")
        for cid, phrase in survived:
            print("  %-10s %s" % (cid, phrase[:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
