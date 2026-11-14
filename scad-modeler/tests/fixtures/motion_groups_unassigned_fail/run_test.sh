#!/usr/bin/env bash
# P21 (INC-2026-11-13-05: a Z drive outside the bbox-defined moving group was silently treated
# as static and the sweep reported a false 1.2 mm). With a "static" list declared, an STL that
# no driver and no static entry names must FAIL before any sweep, naming the part.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
python3 "$here/../motion_groups/make_stls.py" "$t" out tray || exit 1
o=$(python3 "$SCAD_MODELER_SCRIPTS/motion_sweep.py" --joints "$here/../motion_groups/joints_ok.json" "$t"/*.stl 2>&1); r=$?
[ "$r" -eq 3 ] || { echo "expected exit 3, got $r"; echo "$o"; exit 1; }
echo "$o" | grep -q "unassigned.*cable_tray" || { echo "report does not name cable_tray as unassigned"; echo "$o"; exit 1; }
echo "$o" | grep -q "Sweeping" && { echo "sweep ran despite an unassigned part"; echo "$o"; exit 1; }
exit 0
