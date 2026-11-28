# Small textbook bench

Seven tasks with known answers taken from worked examples in Bethune, *Engineering Design and Graphics with
SolidWorks 2016* (Pearson). Only dimensions and answer numbers are reused; section and page are in `tasks.json`.
Each task runs headless (`claude -p "/<skill> ..."`) in a fresh directory and must write `answer.json`; `score.py`
checks every value against a [min, max] range and that the produced `.scad` renders.

```bash
bash bench/run_bench.sh            # all tasks not yet run (resumable); BENCH_MODEL=opus by default
python3 bench/score.py             # score bench/runs/
```

## Result 2026-11-28 (Opus 5.5, Claude Code 2.1.325, skills at 4271c78, one run each)

| Task | Skill | Values in range | Renders | Time | Cost (API-equivalent) |
|---|---|---|---|---|---|
| t1 M10×1.25 tapped joint (§6-13) | scad-modeler | 2/2 | yes | 2.7 min | $1.12 |
| t2 positional tolerance, floating/fixed (§8-48) | openscad-cad | 2/2 | yes | 0.9 min | $0.56 |
| t3 spur pair m1 16/48 (proj. 10-7) | scad-modeler | 3/3 | yes | 3.8 min | $1.50 |
| t4 gear plate m2.5 20/50 (10-14/10-17) | scad-modeler | 1/1 | yes | 7.6 min | $2.19 |
| t5 ISO H11/c11 @10, H8/f7 @16 | openscad-cad | 6/6 | yes | 1.4 min | $0.71 |
| t6 bolt length, 3-block stack (§6-11, inch) | openscad-cad | 1/2 | yes | 1.2 min | $0.63 |
| t7 U-bracket bearings H7/p6, H9/d9 | scad-modeler | 6/6 | yes | 5.5 min | $1.79 |
| **Total** | | **21/22** | 7/7 | 23 min | $10.50 |

Miss: t6 reported the minimum length as the bare stack (1.857 in) instead of stack + 2 pitches (1.982 in, the book's
full-engagement rule), but still chose the right 2.00 in bolt.

Limits (read before quoting this): 7 tasks written by the maintainer, one run each, no run without the skills to
compare against, and t5/t7 overlap the ISO table that `check_fits.py` carries. The cost column is the CLI's
`total_cost_usd` (what the same tokens would cost on the API); the runs used a Max subscription. This is a smoke test
of correctness on textbook numbers, not a public benchmark (P37 still lists MUSE / Parametric CAD Bench).
