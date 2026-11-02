#!/usr/bin/env bash
# INCIDENTS.json stores structured incident entries queried via scripts/incidents.py.
# Verify:
#   1. INCIDENTS.json passes schema validation (check)
#   2. list / search / show / add work deterministically
#   3. check rejects a corrupted entry (negative test)
set -uo pipefail

INC="$SCAD_MODELER_SCRIPTS/../../INCIDENTS.json"
CLI="$SCAD_MODELER_SCRIPTS/incidents.py"

[ -f "$INC" ] || { echo "no INCIDENTS.json at $INC" >&2; exit 1; }
[ -f "$CLI" ] || { echo "no incidents.py at $CLI" >&2; exit 1; }

# --- 1. schema check passes on real INCIDENTS.json --------------------------
python3 "$CLI" check --file "$INC" || exit 1

# --- 2. list / search / show / add on a scratch copy ------------------------
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cp "$INC" "$scratch/inc.json"

python3 "$CLI" list --file "$scratch/inc.json" | grep -q "^INC-2026-11-02-01" || {
    echo "list did not return INC-2026-11-02-01" >&2; exit 1
}
python3 "$CLI" search "check_features.py" --file "$scratch/inc.json" | grep -q "INC-2026-11-02-01" || {
    echo "search did not find check_features.py incident" >&2; exit 1
}
python3 "$CLI" show "INC-2026-11-02-01" --file "$scratch/inc.json" | grep -q '"date": "2026-11-02"' || {
    echo "show did not return JSON for INC-2026-11-02-01" >&2; exit 1
}
python3 "$CLI" add \
    --file "$scratch/inc.json" \
    --date "2026-11-02" \
    --title "synthetic test incident" \
    --where "tests/fixtures/incidents_index_accurate" \
    --symptom "none" \
    --root-cause "test" \
    --fix "none" >/dev/null || { echo "add failed" >&2; exit 1; }
python3 "$CLI" check --file "$scratch/inc.json" >/dev/null || {
    echo "check failed after add" >&2; exit 1
}

# --- 3. corrupted entry must fail check -------------------------------------
python3 - "$scratch/inc.json" <<'PY'
import json, sys
p = sys.argv[1]
doc = json.load(open(p, encoding="utf-8"))
doc["entries"][0]["id"] = "BAD-ID"
json.dump(doc, open(p, "w", encoding="utf-8"))
PY
if python3 "$CLI" check --file "$scratch/inc.json" >/dev/null 2>&1; then
    echo "check passed on invalid incident ID" >&2
    exit 1
fi

echo "ok  INCIDENTS.json validated (check + list + search + show + add + negative check)"
exit 0
