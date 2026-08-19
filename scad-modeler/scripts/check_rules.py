#!/usr/bin/env python3
"""L4 rules-enforcement gate (references/rules_enforcement.md): the last
thing that runs before §8's final report.

Why this exists
----------------
Three confirmed reasons agents drift from stated rules: context overload (a
rule stated once, early in a long SKILL.md, gets buried under later detail),
no consequence (skipping a step doesn't stop anything, so a fast answer
without verification gets positive feedback), and rules that aren't
machine-checkable ("must do X" with no way to prove X actually happened).
Prose reminds; a script that returns non-zero cannot be quietly ignored.

What this does
--------------
Reads rules_manifest.yaml (the single list of every rule in this skill) and,
for each one:
  - Decides whether it applies to this project right now (a file-existence
    or JSON-field detector -- see the manifest's own header comment).
  - If it applies and has an automated gate script, RUNS that gate and
    records PASS/FAIL from its exit code -- this is real verification, not
    a checklist the model fills in from memory.
  - If it applies and has no automated gate (a few rules -- like whether the
    §0.6 narrative was actually written, or whether a collision check was
    actually run -- are about content quality or a manual step this script
    cannot see from the project directory alone), it is printed as MANUAL
    and the model is required to self-assess and state its verdict for that
    specific rule ID in the §8 report. This script does not silently pass
    a manual rule just because it can't check it -- it makes sure the rule
    stays visible instead of disappearing.

The exit code reflects only the AUTOMATED rules (a manual rule cannot be
force-failed by a script that has no way to verify it) -- but every manual
rule that applies is printed regardless, and the whole point of this gate is
that its FULL output (not a paraphrase) gets cited in the §8 report. Citing
a summary instead of the actual output is exactly the kind of soft
compliance this script exists to prevent.

Usage:
    python3 check_rules.py --project-dir .
    python3 check_rules.py --project-dir . --manifest rules_manifest.yaml

Exit codes:
    0  pass -- every applicable automated rule passed (manual rules may
       still be pending explicit self-assessment; check the output).
    3  fail -- at least one applicable automated rule failed.
    4  usage/runtime error (missing pyyaml, malformed manifest).
"""
import argparse
import json
import os
import re
import subprocess
import sys

EXIT_OK = 0
EXIT_FAIL = 3
EXIT_USAGE = 4

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(EXIT_USAGE)


def load_manifest(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        print(f"ERROR: cannot read/parse {path}: {e}", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    rules = data.get("rules") if isinstance(data, dict) else None
    if not isinstance(rules, list):
        print(f"ERROR: {path} must contain a top-level 'rules' list.", file=sys.stderr)
        sys.exit(EXIT_USAGE)
    for r in rules:
        missing = [k for k in ("id", "rule", "applies", "kind") if k not in r]
        if missing:
            print(f"ERROR: rule missing {missing}: {r}", file=sys.stderr)
            sys.exit(EXIT_USAGE)
    return rules


def evaluate_applies(expr, project_dir):
    """Return True/False for a detector expression, or None if unrecognized
    (treated as applying, so an unknown detector fails open toward MORE
    checking rather than silently skipping a rule)."""
    if expr == "always":
        return True
    if expr.startswith("file_exists:"):
        candidates = expr[len("file_exists:"):].split(",")
        return any(os.path.isfile(os.path.join(project_dir, c.strip())) for c in candidates)
    if expr.startswith("json_true:"):
        rest = expr[len("json_true:"):]
        if "#" not in rest:
            return None
        rel_path, dotted = rest.split("#", 1)
        full_path = os.path.join(project_dir, rel_path)
        if not os.path.isfile(full_path):
            return False
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return False
        cur = data
        for key in dotted.split("."):
            if not isinstance(cur, dict) or key not in cur:
                return False
            cur = cur[key]
        return bool(cur)
    return None


def run_gate(cmd_template, project_dir, skill_dir):
    """Run a gate command once, returning (exit_code, full_output, tail).

    Multiple rules can share the exact same gate command (R-04 and R-09 both
    run the whole `validate_scad.sh --all`, since it's a single render pass
    that produces results for several independent checks at once -- see
    `success_pattern` below for how a specific rule's verdict is pulled out
    of that shared output without re-running the render). Caching by the
    literal command string avoids paying for that render twice.
    """
    cmd = cmd_template.format(project_dir=project_dir, skill_dir=skill_dir)
    if cmd in run_gate._cache:
        return run_gate._cache[cmd]
    try:
        # cwd=project_dir matters: validate_scad.sh (and the relative-path
        # globs inside it) assume the project directory is the working
        # directory, not an argument -- confirmed by hitting this directly
        # (a first version of this function ran gates from wherever
        # check_rules.py itself was invoked, silently checking the wrong
        # directory's parts/*.scad).
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                               timeout=600, cwd=project_dir)
        code, output = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        code, output = 124, "(gate timed out after 600s)"
    tail = "\n".join(output.strip().splitlines()[-8:])
    result = (code, output, tail)
    run_gate._cache[cmd] = result
    return result


run_gate._cache = {}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-dir", default=".", help="project directory to check (default: .)")
    parser.add_argument("--manifest", default=None,
                         help="path to rules_manifest.yaml (default: next to this script's parent skill dir)")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    manifest_path = args.manifest or os.path.join(skill_dir, "rules_manifest.yaml")
    project_dir = os.path.abspath(args.project_dir)

    rules = load_manifest(manifest_path)

    results = []
    any_auto_fail = False

    for r in rules:
        applies = evaluate_applies(r["applies"], project_dir)
        if applies is None:
            print(f"ERROR: rule {r['id']} has an unrecognized 'applies' detector: {r['applies']}",
                  file=sys.stderr)
            return EXIT_USAGE
        if not applies:
            results.append((r["id"], "N/A", r["rule"], None))
            continue
        if r["kind"] == "manual":
            results.append((r["id"], "MANUAL", r["rule"], None))
            continue
        if not r.get("gate"):
            print(f"ERROR: rule {r['id']} is kind=auto but has no gate command.", file=sys.stderr)
            return EXIT_USAGE
        code, output, tail = run_gate(r["gate"], project_dir, skill_dir)
        success_pattern = r.get("success_pattern")
        if success_pattern:
            # This rule's gate may be a multi-purpose script (validate_scad.sh
            # --all runs several independent checks in one render pass) whose
            # OVERALL exit code can be non-zero because of a completely
            # unrelated check failing. Determining THIS rule's verdict from
            # that shared exit code would conflate "this specific check
            # failed" with "some other check failed and this one never even
            # ran" -- confirmed as a real, reported ambiguity (INCIDENTS.md,
            # 2026-08-19). Search the gate's own output for this rule's
            # specific marker instead, ignoring the process exit code
            # entirely for the verdict.
            passed = re.search(success_pattern, output) is not None
        else:
            passed = code == 0
        if passed:
            results.append((r["id"], "PASS", r["rule"], tail))
        else:
            results.append((r["id"], "FAIL", r["rule"], tail))
            any_auto_fail = True

    print(f"Rules manifest: {manifest_path}")
    print(f"Project: {project_dir}")
    print("-" * 70)
    manual_ids = []
    for rid, status, rule_text, tail in results:
        print(f"[{status:6}] {rid}: {rule_text}")
        if status == "FAIL" and tail:
            for line in tail.splitlines():
                print(f"           {line}")
        if status == "MANUAL":
            manual_ids.append(rid)
    print("-" * 70)

    if manual_ids:
        print(f"MANUAL rules requiring explicit self-assessment in the §8 report "
              f"(done / skipped / not applicable, with a one-line reason each): "
              f"{', '.join(manual_ids)}")
        print("This is not optional -- a manual rule left unaddressed in the "
              "report is indistinguishable from one nobody checked.")

    if any_auto_fail:
        print("FAIL: at least one automated rule did not pass. Fix at the "
              "source and re-run validate_scad.sh --all from the top, then "
              "re-run check_rules.py -- do not hand-edit around a failing gate.")
        return EXIT_FAIL

    print("OK: every applicable automated rule passed. Cite this FULL output "
          "(not a paraphrase) in the §8 report, including the manual-rule "
          "self-assessment above.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
