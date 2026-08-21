#!/usr/bin/env python3
"""Shared append-only validation-run logger.

Why this exists: reconstructing a real project's validation history after
the fact (from calculations.md prose + INCIDENTS.md, no live logging)
lost almost every exact command, exit code, and timestamp -- confirmed
directly against the steering_reduction_gearbox project's ~26-round
history when asked to reconstruct it, 2026-08-21: 24 of 26 entries had
"nezinoma" (unknown) exit code, and only one had a fully-recorded command
line. This writes one JSON line per check run, at the moment it runs, so
a later pattern-review pass -- INCIDENTS.md's own stated purpose, "raw
data for a later pattern-review pass, not something to analyze now" --
has real data instead of a lossy reconstruction.

What this does NOT do: it does not make any tool "learn" by itself --
there is no training loop reading this file automatically. It is raw
material for a human (or an agent, later, explicitly) to review, exactly
like INCIDENTS.md itself, just at finer grain and captured live instead
of written up after the fact.

Where it writes: $SCAD_MODELER_LOG_DIR/validation_log.jsonl if that env
var is set, else ~/.claude/scad_modeler/validation_log/validation_log.jsonl.
Deliberately NOT a hardcoded personal path (this script ships in a public
repo) and deliberately NOT project-local -- checks are commonly run
standalone, outside any one project directory's git history, and the
point is seeing patterns across a project's full history and across
projects, not just within one validate_scad.sh --all invocation.

Logging here is best-effort and must never affect a validation run's own
exit code: any failure to write (missing permissions, disk full, whatever)
is silently swallowed.

Usage (from bash, e.g. validate_scad.sh):
    python3 validation_log.py --checker connectivity --exit 0 \\
        --command "validate_scad.sh --all" --summary "PASS"

Usage (from Python, e.g. check_collisions.py):
    from validation_log import log_run
    log_run("collisions", exit_code, "check_collisions.py " + " ".join(sys.argv[1:]), summary)
"""
import argparse
import datetime
import json
import os
import sys

DEFAULT_LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "scad_modeler", "validation_log")

# The exit-code convention shared by check_collisions.py, motion_sweep.py,
# check_bore_reachability.py, check_subfeature_overlap.py, check_rules.py:
# 0=OK, 2=DEGRADED (checked but not trustworthy, e.g. non-watertight mesh),
# 3=FAIL, 4=USAGE_ERROR (bad arguments, not a verdict on the geometry).
EXIT_LABELS = {0: "OK", 2: "DEGRADED", 3: "FAIL", 4: "USAGE_ERROR"}


def label_for_exit(code):
    return EXIT_LABELS.get(code, f"exit={code}")


def log_dir():
    return os.environ.get("SCAD_MODELER_LOG_DIR") or DEFAULT_LOG_DIR


def log_run(checker, exit_code, command, summary, project=None):
    try:
        d = log_dir()
        os.makedirs(d, exist_ok=True)
        record = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "project": project or os.getcwd(),
            "checker": checker,
            "exit_code": int(exit_code),
            "command": command,
            "summary": summary,
        }
        with open(os.path.join(d, "validation_log.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checker", required=True)
    ap.add_argument("--exit", required=True, type=int, dest="exit_code")
    ap.add_argument("--command", required=True)
    ap.add_argument("--summary", default="")
    ap.add_argument("--project", default=None)
    args = ap.parse_args()
    log_run(args.checker, args.exit_code, args.command, args.summary, args.project)
    return 0


if __name__ == "__main__":
    sys.exit(main())
