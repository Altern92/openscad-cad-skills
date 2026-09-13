# tools/ — the measurement scripts this skill's claims rest on

These are not part of the validation pipeline. They are the **instruments** used to
decide whether the pipeline got better, kept here because the numbers in
`README.md`, `NEXT.md` and `_wiki/scad/` are worthless without the commands that
produced them.

| Script | Answers |
|---|---|
| `ab_tooling.sh` | Does one version of the checks report more than another, on real projects? |
| `ab_analyze.py` | Where exactly do the two versions differ? |
| `check_req.py` | Does a built part satisfy the stated requirements? |
| `mutation_test.py` | Does the golden-set grader actually reject wrong answers? |

## The one that matters most

`ab_tooling.sh` is the only measurement that produced a **deterministic** result.
Agent-based tests are unfalsifiable below roughly **120 tasks per arm** (see
`_wiki/scad/05_agentu_testai.md`), so they cannot answer "did this help" — but two
check versions run against the same projects, with the agent removed, can. Measured
2026-09-12 on 11 projects: **89 → 198** `CHECK_RESULT` lines, `COVERAGE` **0/11 → 11/11**,
and **10 of 18 checks were silent in the old version on every single project**.

## Running them

```bash
# 1. record what the CURRENT checks report, in a git-ignored scratch dir
bash tests/tools/ab_tooling.sh ~/path/to/projects /tmp/ab

# 2. compare against an older revision of this repo
git -C . worktree add /tmp/old-skill <OLD_SHA>     # or: rsync + git checkout, see below
POST=<this repo> PRE=/tmp/old-skill/tests/tools bash tests/tools/ab_tooling.sh \
     ~/path/to/projects /tmp/ab

# 3. read the diff
python3 tests/tools/ab_analyze.py /tmp/ab
```

## A trap worth knowing before you start

`git worktree` **does not carry untracked files**, so an "old version" built that way
can be missing whole skills — this already invalidated one run (SCAD-05 in
`golden_scad/PRES_PO_2026-09-11.md`). Use `rsync` then `git checkout` instead:

```bash
rsync -a --exclude '.git' <repo>/ /tmp/old-skill/
cd /tmp/old-skill && cp -R <repo>/.git . && git checkout -q <OLD_SHA> -- . && rm -rf .git
# verify: both trees should have the same file count
find /tmp/old-skill -type f | wc -l
```

## What these do NOT measure

Whether a **model** writes better OpenSCAD with the newer checks. Nothing here can
answer that, and at the sample sizes available nothing else can either. Every number
below is a property of the tooling, not of the agent.