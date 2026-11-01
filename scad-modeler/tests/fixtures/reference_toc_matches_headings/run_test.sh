#!/usr/bin/env bash
# Anthropic skill best practices: a reference file over 100 lines needs a table of contents,
# because an agent may preview it with head and never see the rest. Each workflow_details.md
# must list every '## ' heading in its '## Contents' block, in order, and the check must fail
# on a heading the contents omit.
set -uo pipefail
R="$(cd "$SCAD_MODELER_SCRIPTS/../.." && pwd)"
check() { python3 - "$1" <<'PY'
import re, sys
t = open(sys.argv[1]).read()
heads = [h for h in re.findall(r'^## (.+)$', t, re.M) if h != 'Contents']
m = re.search(r'^## Contents\n(.*?)(?=^## )', t, re.M | re.S)
if not m: sys.exit(f"{sys.argv[1]}: no '## Contents' block before the first section")
listed = re.findall(r'^- (.+)$', m.group(1), re.M)
if listed != heads:
    sys.exit(f"{sys.argv[1]}: contents {len(listed)} entries != {len(heads)} headings; first mismatch: "
             + next((f"{a!r} vs {b!r}" for a, b in zip(listed + [''] * 99, heads + [''] * 99) if a != b), '?'))
PY
}
n=0
for f in "$R"/scad-modeler/references/workflow_details.md "$R"/openscad-cad/references/workflow_details.md; do
    [ -f "$f" ] || { echo "missing $f" >&2; exit 1; }
    check "$f" || exit 1; n=$((n + 1))
done
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp "$R/scad-modeler/references/workflow_details.md" "$tmp/w.md"; printf '\n## Unlisted section\nx\n' >> "$tmp/w.md"
check "$tmp/w.md" 2>/dev/null && { echo "an unlisted heading was not caught" >&2; exit 1; }
exit 0
