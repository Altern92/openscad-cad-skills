# Rules-enforcement engine (kaip užtikrinti, kad skill KASKART laikytųsi taisyklių)

> Tikslas: nulis „pamiršau taisyklę" atvejų. Principas — **taisyklė turi būti
> patikrinama mašinai, ne tik įsimenama modelio**. Promptas primena; skriptas
> įrodo. Jei skriptas negali įrodyti, kad žingsnis įvyko — darbas sustoja.

## 1. Kodėl agentai nukrypsta nuo taisyklių (3 pagrindinės priežastys)

1. **Konteksto perkrova** — ilgoje SKILL.md taisyklės „nuskęsta" tarp detalių;
   modelis seka paskutinį matytą pavyzdį, o ne taisyklę.
2. **Nėra pasekmių** — jei žingsnis praleidžiamas, niekas nesustoja; modelis
   gauna teigiamą grįžtamąjį ryšį už „greitą" atsakymą net ir be patikros.
3. **Taisyklė nėra patikrinama** — „privaloma atlikti X" be jokio mechanizmo
   patvirtinti, kad X tikrai įvyko (ir įvyko teisingai).

Patvirtinti kontrargumentai iš literatūros: verifikacijos kilpos (CoVe,
structured verification loops — [arxiv 2606.21724](https://arxiv-org.ezproxy.obspm.fr/html/2606.21724v1)),
„agentas pats patikrina savo darbą prieš atsakymą" ([BeFailProof](https://befailproof.ai/guides/how-to-make-ai-agents-reliable/)),
veiksmų apribojimas ir struktūruoti rezultatai ([n8n](https://blog.n8n.io/make-ai-agents-more-reliable-and-restrict-the-actions-they-can-take/),
[Gemma 4 guardrails](https://dev.to/system_rationale/part-3-making-gemma-4-agents-production-ready-guardrails-structured-outputs-and-self-healing-575n)),
o gamybiniams agentams neužtenka vien promptų — reikia būsenos mašinos ir
deterministinių vartų ([Production AI agents](https://www.mygreatlearning.com/blog/production-ai-agents/)).

## 2. Sluoksniuotas vykdymo modelis (4 sluoksniai)

### L1 — Prompt lygmuo (primena)
- SKILL.md pradžioje — **trumpa „prieš ką nors darydamas" eilutė**, nukreipianti
  į šį dokumentą ir į `validation_decision_tree.md` (ne kartoti visas taisykles
  — jos yra žemiau; tik „kur žiūrėti").
- Kiekvienas privalomas žingsnis turi **vieną** nurodymą vienoje vietoje
  (dublikatai skiriasi — modelis pasirenka paskutinį).

### L2 — Deterministiniai vartai (įrodo)
Egzistuojantis pavyzdys: `check_plan.py` — įrodo, kad §0.5 planavimas įvyko
(ne tik prozoje). Kiekvienas privalomas žingsnis gauna tokį vartą:

| Privalomas žingsnis | Vartas (skriptas įrodo) |
|---|---|
| Intake atliktas | `requirements.json`/`design_manifest.json` egzistuoja ir atitinka schemą (naujas `check_intake.py`) |
| Planavimas (§0.5) | `check_plan.py` (yra) |
| Paskyrimų lentelė (§1) | `calculations.md` su decisions-log (yra per `check_assumptions.py`) |
| Fizinė naratyva (§0.6) | 4 atsakymai failo pavidalu (naujas lengvas vartas) |
| Geometrija | `validate_scad.sh --all` (yra) |
| Judančios dalys | `design_manifest.json.motion` → `motion_sweep.py` (yra, trigger naujas) |
| Pokyčių perskaičiavimas | `check_dependencies.py` (naujas — žr. `change_propagation.md`) |

### L3 — Savęs patikros kilpa (modelis tikrina save)
Prieš §8 galutinį pranešimą modelis paleidžia **taisyklių manifestą** (L4) ir
pats įvertina kiekvieną eilutę: `padaryta / praleista / netaikoma`. Praleista
→ grįžti, padaryti, paleisti iš naujo. Šis žingsnis — ne pasirenkamas „jei
turiu laiko", o privalomas vartas prieš atsakymą vartotojui.

### L4 — Taisyklių manifestas (mašiniškai tikrinamas sąrašas)
Failas `rules_manifest.yaml` (šalia SKILL.md): **vienintelis** sąrašas visų
privalomų taisyklių. Naujas skriptas `check_rules.py` paleidžia jį prieš §8:

```yaml
rules:
  - id: R-01
    rule: "Intake: requirements.json egzistuoja ir validus"
    check: "file exists requirements.json && schema valid"
    gate: check_intake.py
    applies: new_design
  - id: R-02
    rule: "Planavimas: plan.md egzistuoja 3+ dalių surinkimui"
    check: "check_plan.py passes"
    gate: check_plan.py
    applies: assembly_3plus
  - id: R-03
    rule: "validate_scad.sh --all po KIEKVIENO pakeitimo"
    check: "last run green + mtimes newer than last .scad edit"
    gate: validate_scad.sh
    applies: any_change
  # ... visas sąrašas
```

Modelis privalo paleisti `check_rules.py` ir **cituoti jo išvestį** §8
ataskaitoje. Jei skripto nėra tam žingsniui — taisyklė laikoma neįgyvendinta.

## 3. Gedimo tvarkymas (kas atsitinka, kai vartas nepraleidžia)

1. **Stabdyk** — nesitaisyk „šalia", neperrašyk rezultato.
2. **Taisyk šaltinyje** (parametras, skriptas, geometrija) — ne išvestyje.
3. **Paleisk iš naujo nuo viršaus** — ne tik to vieno varto, kuris nepraėjo
   (kaskadinis efektas: apačioje praeina tik tada, kai viršuje švaru).
4. **Užfiksuok** — jei vartas praleido klaidą (false pass), įrašyk incidentą į
   `INCIDENTS.md` (jau yra tokia praktika).

## 4. Kodėl tai veiks šiam skill'ui

Skill'as jau turi tinkamiausią pagrindą: skriptų rinkinį, kuris tikrina
geometriją **nepriklausomai nuo modelio** (`check_*.py`). Šis variklis tą patį
principą išplečia į **proceso** žingsnius (intake, planavimas, naratyva,
pokyčių medis) ir prideda paskutinį trūkstamą elementą — **privalomą savęs
patikrą prieš atsakymą** (L3+L4). Tada taisyklės laikymasis nebepriklauso nuo
modelio atminties: jį įrodo skriptai, o modelio darbas — tik juos paleisti ir
jų rezultatus cituoti.

## Šaltinių žurnalas

| ID | Teiginys | Šaltinis (URL) | Tipas | Data | Būsena |
|---|---|---|---|---|---|
| E-001 | Verifikacijos kilpos mažina haliucinacijas (CoVe; structured verification loops) | https://arxiv-org.ezproxy.obspm.fr/html/2606.21724v1 ; https://aclanthology.org/2025.bionlp-share.34/ | pirminis | 2026-08-19 | su šaltiniu |
| E-002 | Agentų patikimumas: apriboti veiksmus, struktūruoti rezultatai, savęs gydymas | https://befailproof.ai/guides/how-to-make-ai-agents-reliable/ ; https://blog.n8n.io/make-ai-agents-more-reliable-and-restrict-the-actions-they-can-take/ ; https://dev.to/system_rationale/part-3-making-gemma-4-agents-production-ready-guardrails-structured-outputs-and-self-healing-575n | pirminis | 2026-08-19 | su šaltiniu |
| E-003 | Gamybiniams agentams neužtenka promptų — reikia būsenos mašinos ir vartų | https://www.mygreatlearning.com/blog/production-ai-agents/ | pirminis | 2026-08-19 | su šaltiniu |
| E-004 | Formaliai verifikuotas kodo generavimas per savęs tobulinimą (AlphaVerus) | https://mlanthology.org/icml/2025/aggarwal2025icml-alphaverus/ | pirminis | 2026-08-19 | su šaltiniu |
| E-005 | CAD generavimo verifikacijos kilpa gerina rezultatą (CADCode-Verify) | https://proceedings.iclr.cc/paper_files/paper/2025/hash/81a934cd364e18ea6fdeaf57a93c17d4-Abstract-Conference.html | pirminis | 2026-08-19 | su šaltiniu |
