"""Per-run token stats from subagent transcripts: final context, sum of context over
turns (what is actually re-sent), tool calls, and whether script source was read."""
import json, glob, re, sys, os, statistics as st
D = os.environ.get('EVAL_TX_DIR') or os.path.expanduser('~/.claude/projects/-Users-gytismiliauskas-Desktop-Obsidian/8123fd4d-910e-42a3-8ec0-72043588841e/subagents')
pat = sys.argv[1]  # EVAL_TX_DIR = a session subagents/ dir; e.g. "agent_runs/p19_" or "agent_runs/slim"
rows = []
for f in glob.glob(D + '/*.jsonl'):
    first = open(f).readline()
    m = re.search(re.escape(pat) + r'(\d)/(\w+)', first)
    if not m: continue
    seen, ctxs, tools, src = set(), [], 0, []
    for l in open(f):
        o = json.loads(l)
        if o.get('type') != 'assistant': continue
        msg = o['message']; mid = msg.get('id')
        u = msg.get('usage', {})
        if mid not in seen:
            seen.add(mid)
            ctxs.append(u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0) + u.get('output_tokens', 0))
        for c in msg.get('content', []):
            if c.get('type') == 'tool_use':
                tools += 1
                s = json.dumps(c.get('input'))
                if re.search(r'scripts/\w+\.py', s) and re.search(r'(cat|sed|grep|head|Read|file_path)', s) and 'validate_scad' not in s:
                    src += re.findall(r'scripts/(\w+\.py)', s)
    rows.append((m.group(2), m.group(1), ctxs[-1] if ctxs else 0, sum(ctxs), tools, sorted(set(src))))
rows.sort()
for r in rows: print(*r[:5], r[5])
by = {}
for t, n, fin, tot, tl, s in rows: by.setdefault(t, []).append((fin, tot))
print('task n mean_final mean_sum')
for t, v in by.items(): print(t, len(v), round(st.mean(x[0] for x in v)), round(st.mean(x[1] for x in v)))
if rows: print('ALL', len(rows), round(st.mean(r[2] for r in rows)), round(st.mean(r[3] for r in rows)), 'tools', round(st.mean(r[4] for r in rows), 1))
