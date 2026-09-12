#!/usr/bin/env bash
# Proves check_connectivity.py (a) FAILS a shattered mesh, and (b) reports a
# count that MATCHES what it prints.
#
# Regression guard for the 2026-09-12 bug: the checker counted with
# mesh.body_count but printed mesh.split(only_watertight=False). On the CADAM
# knurled knob those disagreed -- header said "2 disconnected bodies", the
# listing had 3122 lines, and the suggested EXPECTED_BODIES: 2 was wrong. The
# fixture asserts the arithmetic closes: shown + "and N more" == reported.
set -uo pipefail
OPENSCAD=${OPENSCAD:-openscad}
EXPECTED_EXIT=1
"$OPENSCAD" --backend=Manifold --render -o part.stl part.scad >/dev/null 2>&1
out=$(python3 "$SCAD_MODELER_SCRIPTS/check_connectivity.py" --stl part.stl --scad part.scad 2>&1)
actual=$?
rm -f part.stl

if [ "$actual" -ne "$EXPECTED_EXIT" ]; then
    echo "expected exit $EXPECTED_EXIT, got $actual" >&2
    echo "$out" >&2
    exit 1
fi
if ! echo "$out" | grep -q "disconnected"; then
    echo "expected 'disconnected' in output, got:" >&2
    echo "$out" >&2
    exit 1
fi

reported=$(echo "$out" | head -1 | sed -n 's/.*has \([0-9][0-9]*\) disconnected.*/\1/p')
shown=$(echo "$out" | grep -c '^  - body')
more=$(echo "$out" | sed -n 's/^  - \.\.\. and \([0-9][0-9]*\) more.*/\1/p')
more=${more:-0}

if [ -z "$reported" ]; then
    echo "could not parse the reported body count from:" >&2
    echo "$out" | head -1 >&2
    exit 1
fi
if [ "$((shown + more))" -ne "$reported" ]; then
    echo "REPORTED COUNT DOES NOT MATCH THE LISTING: reported=$reported shown=$shown more=$more" >&2
    echo "$out" | head -3 >&2
    exit 1
fi
if [ "$reported" -lt 100 ]; then
    echo "expected a shattered mesh (>=100 islands), got $reported -- fixture no longer reproduces" >&2
    exit 1
fi
if ! echo "$out" | grep -q "EXPECTED_BODIES: ${reported}"; then
    echo "the suggested EXPECTED_BODIES does not match the reported count ($reported)" >&2
    echo "$out" | tail -1 >&2
    exit 1
fi
if ! echo "$out" | grep -q "\.\.\. and .* more components"; then
    echo "expected the capped listing to say how many were hidden, got:" >&2
    echo "$out" | tail -3 >&2
    exit 1
fi
exit 0
