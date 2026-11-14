#!/usr/bin/env bash
# P1-P5 (2026-11-14): the repo installs as a Claude Code plugin from its own marketplace, and an installed
# plugin never writes incidents into its cache (each update installs into a new directory). Uses a throwaway
# git repo of the CURRENT working tree as the marketplace and a temp CLAUDE_CONFIG_DIR, so nothing of the
# user's own Claude config is touched. Needs the `claude` CLI; without it (CI) it prints SKIP and exits 0.
set -uo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v claude >/dev/null || { echo "test_plugin: SKIP (no claude CLI)"; exit 0; }
t=$(mktemp -d); trap 'rm -rf "$t"' EXIT
fail() { echo "test_plugin: $*" >&2; exit 1; }
N="openscad-cad-skills"

claude plugin validate "$SRC" >"$t/validate.log" 2>&1 || { cat "$t/validate.log" >&2; fail "P1 validate failed"; }
python3 - "$SRC" <<'EOF' || fail "P1 manifest fields"
import json, sys, os
r = sys.argv[1]
p = json.load(open(os.path.join(r, '.claude-plugin/plugin.json')))
m = json.load(open(os.path.join(r, '.claude-plugin/marketplace.json')))
assert 'version' not in p, 'plugin.json must not pin a version (commit sha is the version)'
assert p['name'] == 'openscad-cad-skills' and p.get('description') and p.get('author'), p
assert sorted(p['skills']) == ['./openscad-cad', './openscad-organic', './scad-modeler'], p['skills']
assert m.get('description') and m.get('owner') and [x['source'] for x in m['plugins']] == ['./'], m
EOF

rsync -a --exclude .git --exclude __pycache__ --exclude build "$SRC/" "$t/mkt/"
( cd "$t/mkt" && git init -q -b main && git add -A && git -c user.name=t -c user.email=t@t commit -qm init ) || fail "setup"
export CLAUDE_CONFIG_DIR="$t/cfg"
claude plugin marketplace add "$t/mkt" >/dev/null 2>&1 || fail "P2 marketplace add"
claude plugin install "$N@$N" >/dev/null 2>&1 || fail "P2 install"
claude plugin details "$N" 2>&1 | grep -q 'Skills (3)  openscad-cad, openscad-organic, scad-modeler' || fail "P2 skills not listed"
C=$(ls -d "$CLAUDE_CONFIG_DIR/plugins/cache/$N/$N"/*/ | head -1)
[ -f "$C/scad-modeler/scripts/incidents.py" ] || fail "P2 no cache dir"

export SCAD_INCIDENTS_LOCAL="$t/local/INCIDENTS.local.json"
want=$(python3 -c "import json;print(len(json.load(open('$SRC/INCIDENTS.json'))['entries']))")
inc() { (cd "$C/scad-modeler" && python3 scripts/incidents.py "$@"); }
inc list | grep -q "^Total: $want incident" || fail "P3 list count != $want"
before=$(shasum "$C/INCIDENTS.json")
d=$(python3 -c "import json;print(json.load(open('$SRC/INCIDENTS.json'))['entries'][0]['date'])")
inc add --date "$d" --title t --where w --symptom s --root-cause r --fix f >/dev/null || fail "P4 add failed"
[ "$(shasum "$C/INCIDENTS.json")" = "$before" ] || fail "P4 cache INCIDENTS.json was modified"
[ -f "$SCAD_INCIDENTS_LOCAL" ] || fail "P4 local file not written"
inc list | grep -q "^Total: $((want + 1)) incident" || fail "P4 merged count != $((want + 1))"
python3 - "$C/INCIDENTS.json" "$SCAD_INCIDENTS_LOCAL" <<'EOF' || fail "P4 id collision"
import json, sys
a = [e['id'] for e in json.load(open(sys.argv[1]))['entries']]
b = [e['id'] for e in json.load(open(sys.argv[2]))['entries']]
assert not set(a) & set(b), set(a) & set(b)
EOF

inc check | grep -q "local incidents validated" || fail "P4 check skipped the local file"
echo '{broken' > "$SCAD_INCIDENTS_LOCAL"
o=$(inc add --title t --where w --symptom s --root-cause r --fix f 2>&1) && fail "P5 add accepted a broken local file"
echo "$o" | grep -q "$SCAD_INCIDENTS_LOCAL" || fail "P5 error does not name the local file: $o"
[ "$(cat "$SCAD_INCIDENTS_LOCAL")" = '{broken' ] || fail "P5 broken local file was overwritten"
[ "$(shasum "$C/INCIDENTS.json")" = "$before" ] || fail "P5 cache modified"
echo "test_plugin: 5/5 OK"
