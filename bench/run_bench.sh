#!/usr/bin/env bash
# Run bench tasks headless on the Claude subscription (no API key), one fresh dir per task, resumable.
# Usage: run_bench.sh [task_id ...]   (default: all not yet run). Model: $BENCH_MODEL (default opus).
# Tools are allow-listed (no permission bypass); a denied tool just fails inside the run.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; runs="$here/runs"; mkdir -p "$runs"
ids=("$@"); [ ${#ids[@]} -gt 0 ] || ids=($(python3 -c "import json;[print(t['id']) for t in json.load(open('$here/tasks.json'))['tasks']]"))
for id in "${ids[@]}"; do
  d="$runs/$id"; [ -s "$d/claude.json" ] && { echo "skip $id (done)"; continue; }
  mkdir -p "$d"
  prompt=$(python3 - "$here/tasks.json" "$id" <<'PY'
import json, sys
t = next(t for t in json.load(open(sys.argv[1]))["tasks"] if t["id"] == sys.argv[2])
keys = ", ".join(t["answer_keys"])
print(f"/{t['skill']} {t['prompt']}\n\nWork in the current directory. When done, write answer.json here: one JSON object "
      f"with exactly these numeric keys: {keys}. Units are in the key names. Do not ask questions; make reasonable assumptions.")
PY
)
  echo "$prompt" > "$d/prompt.txt"
  echo "run $id ($(date -u +%H:%MZ))"
  ( cd "$d" && perl -e 'alarm shift; exec @ARGV' 2700 env -u ANTHROPIC_API_KEY claude -p "$prompt" --model "${BENCH_MODEL:-opus}" --output-format json \
      --permission-mode acceptEdits \
      --allowedTools "Read" "Write" "Edit" "Glob" "Grep" "Skill" "Bash(openscad:*)" "Bash(bash:*)" "Bash(python3:*)" \
                     "Bash(ls:*)" "Bash(mkdir:*)" "Bash(cat:*)" "Bash(cp:*)" "Bash(uv:*)" \
                     "Bash($HOME/.local/share/scad-modeler/venv/bin/python:*)" "Bash(env:*)" "Bash(PATH=*)" \
      < /dev/null > claude.json.tmp 2> stderr.txt ) ; echo "rc=$?" >> "$d/stderr.txt"
  if [ -s "$d/claude.json.tmp" ]; then mv "$d/claude.json.tmp" "$d/claude.json"; else echo "  $id: empty output, see $d/stderr.txt"; fi
done
python3 "$here/score.py" "$runs"
