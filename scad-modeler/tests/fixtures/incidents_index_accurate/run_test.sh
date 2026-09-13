#!/usr/bin/env bash
# INCIDENTS.md ships an index so a reader can find the three relevant entries
# without paying for all 1 500 lines. An index whose line numbers drift is WORSE
# than no index: it looks authoritative and sends the reader to the wrong entry.
#
# Two properties, both mechanical:
#   1. every entry heading has an index line, and every index line points at an
#      entry heading
#   2. rebuilding is idempotent -- a rebuild that grows the file silently
#      accumulates stale blocks
#
# The idempotency check exists because the first version failed exactly that way:
# it stripped only the lines that LOOKED like index rows and left the date
# headings behind, so each rebuild added ~28 lines. `check` passed the whole time,
# because the numbers it verified were still correct.
set -uo pipefail

INC="$SCAD_MODELER_SCRIPTS/../../INCIDENTS.md"
GEN="$SCAD_MODELER_SCRIPTS/../tests/tools/incidents_index.py"

[ -f "$INC" ] || { echo "no INCIDENTS.md at $INC" >&2; exit 1; }
[ -f "$GEN" ] || { echo "no incidents_index.py at $GEN" >&2; exit 1; }

# --- 1. every link points at an entry heading -------------------------------
if ! python3 "$GEN" check "$INC"; then
    echo "the index does not match the file -- run:" >&2
    echo "  python3 $GEN rebuild $INC" >&2
    exit 1
fi

# --- 2. rebuild is idempotent -----------------------------------------------
scratch=$(mktemp -d)
cp "$INC" "$scratch/inc.md"
before=$(wc -l < "$scratch/inc.md" | tr -d " ")
python3 "$GEN" rebuild "$scratch/inc.md" > /dev/null
once=$(wc -l < "$scratch/inc.md" | tr -d " ")
python3 "$GEN" rebuild "$scratch/inc.md" > /dev/null
twice=$(wc -l < "$scratch/inc.md" | tr -d " ")
rm -rf "$scratch"

if [ "$before" != "$once" ] || [ "$once" != "$twice" ]; then
    echo "rebuild is not idempotent: $before -> $once -> $twice lines" >&2
    echo "  a rebuild that grows the file is accumulating stale blocks" >&2
    exit 1
fi

entries=$(grep -c "^### 20" "$INC")
echo "ok  index covers all $entries entries and rebuild is idempotent"
exit 0