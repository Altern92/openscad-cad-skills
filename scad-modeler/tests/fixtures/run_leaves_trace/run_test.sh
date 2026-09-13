#!/usr/bin/env bash
# A run must leave evidence it happened, and must name the next command.
#
# Two failures this guards against, both measured 2026-09-12.
#
# 1. A validated project and a never-validated one were indistinguishable by
#    looking at it. The only record was a central log in ~/.claude that nothing
#    in the project referenced, so a stale PASS and a fresh one read the same.
#
# 2. The next command lived 600 lines into SKILL.md. An agent skipped it: it ran
#    one checker by hand, called the work done, and shipped a part that
#    check_connectivity.py fails immediately. Documentation is remembered or not;
#    the last line of output is read.
#
# The state file also records a hash per source, so "this was validated" can be
# told apart from "this was validated before someone edited params.scad".
set -uo pipefail

proj=$(mktemp -d)
mkdir -p "$proj/parts"
printf '%s\n' '$fa = 2; $fs = 0.3;' > "$proj/params.scad"
printf 'cube([10, 10, 10]);\n' > "$proj/parts/box.scad"

out=$( cd "$proj" && bash "$SCAD_MODELER_SCRIPTS/validate_scad.sh" --all 2>&1 )
code=$?

# --- 1. the next command is named in the output -----------------------------
echo "$out" | grep -q "check_rules.py --project-dir" || {
    echo "the run does not name check_rules.py -- the next step is invisible:" >&2
    echo "$out" | tail -6 >&2
    rm -rf "$proj"; exit 1; }

# --- 2. the state file exists and is well-formed ----------------------------
state="$proj/build/.validation_state.json"
[ -f "$state" ] || {
    echo "no build/.validation_state.json -- the run left no trace:" >&2
    rm -rf "$proj"; exit 1; }

python3 - "$state" "$proj" "$code" <<'PY' || { rm -rf "$proj"; exit 1; }
import json, sys

state, proj, code = sys.argv[1], sys.argv[2], int(sys.argv[3])
d = json.load(open(state))
fails = []

for key in ("when", "mode", "verdict", "coverage", "sources"):
    if key not in d:
        fails.append("missing key: " + key)

if fails:
    print("state file is incomplete: " + ", ".join(fails), file=sys.stderr)
    sys.exit(1)

# The verdict must agree with the exit code -- a PASS recorded for a failing
# run would be worse than no record at all.
want = "PASS" if code == 0 else "FAIL"
if d["verdict"] != want:
    fails.append("verdict %s but exit code %d" % (d["verdict"], code))

# Sources must be hashed, not merely listed -- a path with no digest cannot
# answer "has this changed since?".
sources = d["sources"]
if not sources:
    fails.append("no sources recorded")
for path, digest in sources.items():
    if len(digest) != 64:
        fails.append("bad digest for %s" % path)

# The coverage counts must add up to something -- all zeros means the run
# reported nothing, which is the failure mode this whole skill exists to stop.
cov = d["coverage"]
if sum(cov.values()) == 0:
    fails.append("coverage is all zeros")

if fails:
    print("state file problems:", file=sys.stderr)
    for f in fails:
        print("  " + f, file=sys.stderr)
    sys.exit(1)
print("ok  trace written: %s, %d source(s) hashed" % (d["verdict"], len(sources)))
PY

rm -rf "$proj"
exit 0