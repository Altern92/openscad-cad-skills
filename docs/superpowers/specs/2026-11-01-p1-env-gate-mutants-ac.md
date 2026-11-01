# P1 aplinkos vartai + P1b checker'ių mutantai — Acceptance Criteria

Data: 2026-11-01. Tier: feature (keičia `validate_scad.sh` sąsają, kuria remiasi SKILL.md).
Tyrimas: Obsidian `Research/Runs/2026/2026-11-01-openscad-skills.md` (31/95 incidentų = klaidingas PASS / tylus SKIP).

## Bazinė būsena (išmatuota 2026-11-01, mini)

- `python3` = `/usr/bin/python3`, be trimesh, shapely, scipy, networkx, manifold3d, rtree, jsonschema (`doctor.py`).
- `validate_scad.sh --all` ant `examples/gear_reduction` be `.venv`: rc=1, bet priežastys klaidinančios —
  `connectivity=FAIL`, `mechanics=FAIL`, `collisions=INCONCLUSIVE` (tikroji priežastis: trūksta modulių).
- BOSL2 neįdiegta (`no OpenSCAD library directory found`) → `render=FAIL` su „Can't find include file".
  Agentas tai gali palaikyti geometrijos klaida.
- `doctor.py` diagnozuoja teisingai, bet `validate_scad.sh` jo nekviečia.
- 16 `check_*.py`; visi turi ≥1 fiktūrą, bet ar kiekvienas turi fiktūrą, kuri tikisi FAIL, nežinoma (regex euristika rodo 8 be jos ◇).

## Architektūra (trumpai)

```
validate_scad.sh / tests/run_all.sh
  └─ scripts/resolve_python.sh  →  SCAD_PYTHON  >  ~/.local/share/scad-modeler/venv/bin/python  >  python3
  └─ env gate (prieš bet kokią patikrą): doctor.py --json su tuo interpretatoriumi
        trūksta modulio / openscad / įtrauktos bibliotekos → CHECK_RESULT env=FAIL + taisymo komanda, exit 5
scripts/setup_env.sh  →  uv venv ~/.local/share/scad-modeler/venv + requirements.txt (idempotentiška)
```
Visi `python3 "$SCRIPT_DIR/check_*.py"` kvietimai keičiami į `"$PY" ...`. Venv ne repo viduje, kad veiktų ir įdiegtam skill'ui (`~/.claude/skills` → `~/Skills-plugins-etc/skills`) ir MBP.

## P1: aplinkos vartai

- **AC-1.** Given `SCAD_PYTHON` nenustatytas, o `~/.local/share/scad-modeler/venv/bin/python` turi visus modulius, when `validate_scad.sh --all` paleidžiamas apvalkale, kurio `python3` neturi trimesh, then visos Python patikros vykdomos venv interpretatoriumi ir išvestyje nėra „not installed" klaidų.
- **AC-2.** Given `SCAD_PYTHON=/kelias/python`, when validacija paleidžiama, then naudojamas būtent tas interpretatorius (pirmenybė prieš venv ir `python3`); išvestyje yra eilutė `ENV python=<kelias>`.
- **AC-3 (klaidos kelias).** Given parinktam interpretatoriui trūksta bent vieno iš trimesh, shapely, scipy, networkx, manifold3d, rtree, yaml, jsonschema, when validacija paleidžiama, then spausdinama `CHECK_RESULT env=FAIL`, trūkstamų modulių sąrašas ir komanda `bash <scripts>/setup_env.sh`; jokių kitų `CHECK_RESULT` eilučių; exit 5.
- **AC-4 (klaidos kelias).** Given `openscad` nerastas (`OPENSCAD` ar PATH), when validacija paleidžiama, then `CHECK_RESULT env=FAIL` su įdiegimo instrukcija, exit 5 (dabar: exit 1 su ERROR).
- **AC-5 (klaidos kelias, ◇ provizoriškas).** Given projekto `.scad` turi `include <BOSL2/...>` (ar kitą `doctor.py` LIBRARIES biblioteką), o `doctor.py` ją rodo kaip trūkstamą, when validacija paleidžiama, then `CHECK_RESULT env=FAIL` nurodo biblioteką ir failą, kuris ją įtraukia; exit 5. Biblioteka, kurios projektas neįtraukia, vartų nestabdo.
- **AC-6.** Given kompiuteryje yra `uv`, when `bash scripts/setup_env.sh`, then sukuriamas venv iš `requirements.txt`, o `doctor.py` tuo interpretatoriumi rodo visus Python paketus `ok`; antras paleidimas exit 0 ir nieko neperdiegia.
- **AC-7.** Given trūksta modulių, when `bash tests/run_all.sh`, then jis spausdina tą pačią vartų žinutę ir exit ≠0 prieš paleidžiant fiktūras (ne „16/48 FAIL").
- **AC-8.** Given `scad-modeler/SKILL.md` ir `openscad-cad/SKILL.md`, when ieškoma `env=FAIL`, then kiekvienas turi taisyklę: sustoti, parodyti vartotojui taisymo komandą, nepranešti jokių patikrų rezultatų. Patikra: doc-fiktūra su `grep`.
- **AC-9 (regresija).** Given visos priklausomybės ir BOSL2 yra, when `tests/run_all.sh`, then visos esamos fiktūros PASS (48/48 + naujos), o `examples/gear_reduction` `CHECK_RESULT` rinkinys sutampa su dabartiniu, išskyrus naują `env=PASS` eilutę.

## P1b: checker'ių mutantai

- **AC-10.** Given `tests/mutants.tsv` (stulpeliai: checker, fiktūra), when meta-fiktūra `mutant_coverage` paleidžiama, then ji FAIL, jei kuris nors `scripts/check_*.py` nėra lentelėje arba nurodytos fiktūros nėra.
- **AC-11 (mutantų patikra).** Given kiekviena `mutants.tsv` fiktūra, when ji paleidžiama su `SCAD_MODELER_SCRIPTS`, nukreiptu į kopiją, kur tas checker'is pakeistas stubu `exit 0`, then fiktūra FAIL. Tai įrodo, kad fiktūra tikrai priklauso nuo to, ar checker'is pagauna defektą, o ne praeina bet kaip.
- **AC-12.** Given checker'iai, kurie dabar neturi AC-11 tenkinančios fiktūros, when įgyvendinimas baigtas, then kiekvienam pridėta po vieną sąmoningai sugadinto įvesties fiktūrą (sąrašas paaiškės per AC-11 matavimą; ◇ euristika rodo iki 8).

## Ne apimtis
- BOSL2 diegimas mini (siūloma atskirai; AC-5 tik praneša).
- `run_checks.py` prototipas (ne pagrindinis kelias) – tik pakeičiamas `python3` į resolverį, jei paprasta.
- P2–P7.
