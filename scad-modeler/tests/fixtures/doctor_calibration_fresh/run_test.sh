#!/usr/bin/env bash
# A calibration profile counts only on the day its coupon was measured, in the material it names:
# filament changes with spool and moisture, so the coupon is printed and measured before each print
# (maintainer, 2026-11-28). Today's profile = ok (tier not capped by calibration); yesterday's = stale,
# missing material / holes = invalid; both cap the tier at 2 like no profile at all.
set -uo pipefail
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT; cd "$t"
today=$(python3 -c "import datetime; print(datetime.date.today())")
old=$(python3 -c "import datetime; print(datetime.date.today() - datetime.timedelta(days=1))")
prof() { printf '{"material": "PETG", "printer": "fixture", "measured": "%s", "holes": [{"nominal": 8.0, "measured": %s}]}\n' "$1" "$2" > printer_profile.json; }
st() { python3 "$SCAD_MODELER_SCRIPTS/doctor.py" --json 2>/dev/null | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['calibration_status'], r['max_tier'], r['max_tier_reason'])"; }
fail=0
prof "$today" 7.82; o=$(st); grep -q "^ok " <<< "$o" || { echo "today's profile not ok: $o"; fail=1; }
grep -q "calibration" <<< "$o" && { echo "today's profile still caps the tier: $o"; fail=1; }
prof "$old" 7.82; o=$(st); grep -q "^stale 2 .*measured $old" <<< "$o" || { echo "yesterday's profile not stale/tier 2: $o"; fail=1; }
echo '{"measured": "'"$today"'", "holes": [{"nominal": 8.0, "measured": 7.8}]}' > printer_profile.json
o=$(st); grep -q "^invalid 2 .*material" <<< "$o" || { echo "profile without material accepted: $o"; fail=1; }
prof "$today" '"x"'; o=$(st); grep -q "^invalid 2 .*holes" <<< "$o" || { echo "non-numeric hole accepted: $o"; fail=1; }
rm printer_profile.json; o=$(st); grep -q "^none 2" <<< "$o" || { echo "no profile not reported: $o"; fail=1; }
exit $fail
