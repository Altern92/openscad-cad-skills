<!-- RAG-passport: file=NEXT.md | skill=all | applies_to=[future-work, roadmap, known-gaps] | version=2026-09-11 | source=07_Pilna_skill_analize + PRES_PO eval -->
# NEXT — ką daryti toliau (2026-09-11 būklė)

Būsena šiandien: trys skill'ai, 23 pasai, 25 regresijos fixture'iai, 18 R-taisyklių,
`scad-modeler/SKILL.md` 750 eil. (buvo 971). Testai 25/25.

**Šis failas — vienintelis sąrašas to, kas žinoma ir nepadaryta.** Kiekvienas
punktas turi įrodymą, kodėl jis čia. Kai padaromas — ištrinti, ne pažymėti.

---

## 1. Golden set'as nematuoja — perrašyti (prioritetas: aukštas)

**Įrodymas:** `golden_scad/PRES_PO_2026-09-11.md`. Tie patys 10 klausimų prieš ir po
viso pakeitimų ciklo — **abi versijos 100%**. Metrikas, kuris turėjo parodyti
pagerėjimą, neparodė nieko.

**Ką daryti:**
1. Perrašyti atvejus taip, kad „prieš" versija **negalėtų** atsakyti teisingai be
   pasų. Pavyzdžiai, kurių dabar trūksta:
   - atvejis, reikalaujantis atskirti du panašius reference failus
     (`tolerances.md` vs `mechanics_and_motion_planning.md`);
   - atvejis, kur chunk'ą reikia rasti pagal `applies_to` žymą, ne pagal failo vardą;
   - atvejis su **spąstu** — bibliotekoje yra panašus, bet neteisingas atsakymas.
2. Išplėsti iki **≥30 atvejų** (dabar 10 — statistinės galios nėra).
3. Paleisti abi versijas; jei vėl 100/100 — atvejai vis dar per lengvi.

**Iki tol šio rinkinio negalima naudoti kaip kokybės įrodymo.** Jis gali pagauti
regresiją (jei kas nors sulaužoma, atsakymai kris), bet ne pagerėjimą.

**Pamoka iš pirmo paleidimo:** vienas atvejis (SCAD-05) buvo apskritai nevaldgas —
`openscad-organic` buvo untracked git'e, tad `worktree` „prieš" versija jo neturėjo.
Prieš paleidžiant eval — patikrinti, kad abi versijos turi tą patį failų rinkinį.

---

## 2. 230 treniravimo pavyzdžių — neprijungti prie nieko (prioritetas: sprendimas, ne darbas)

**Kur:** `04_Kita/openscad_skill_training_data*/ (6 katalogai)` — 236 pavyzdžiai
(5 senos kategorijos) + 22 nauji `openscad_skill_training_data_rack_v6`
(`validation_gate`, `user_correction`).

**Būklė:** surinkti, validūs, unikalūs — ir **nenaudojami**. Biblioteka jų nemato.

**Trys keliai, reikia pasirinkti:**

| Kelias | Ką reiškia | Kada prasminga |
|---|---|---|
| **RAG bazė** | prijungti prie bibliotekos kaip papildomas references sluoksnis | jei nori, kad modelis mokytųsi iš praeities sesijų |
| **LoRA pilotas** | fine-tune su 258 pavyzdžiais, griežtu eval | jei nori formato/elgesio, ne žinių; **rizika: 44% iš vieno projekto** |
| **Golden atvejai** | paversti sunkiais eval klausimais iš realių nesėkmių | jei nori matuoti (papildo #1) |

**Peržiūros išvados** (iš `04_Kita` analizės): 0 dublikatų, `failure_correction_chains`
aukščiausia kokybė (48/48 su `root_cause_summary`), bet projekto koncentracija 80%
top-3, kalba sumaišyta (58/236 su lietuviškais diakritikais), `related_tool_call_id`
52/54 tuščias.

---

## 3. Neįgyvendinti tyrimų verdiktai (prioritetas: vidutinis)

| Šaltinis | Verdiktas | Būklė |
|---|---|---|
| `06_RAG_taisykles` T5/T6 | hybrid retrieval + reranker | **netaikoma** — Claude Code skill'ai neturi retriever'io; RAG čia metafora failų organizavimui |
| `06_RAG_taisykles` T8 | struktūrinis tarpininkas | tyrimas padarytas (`research_2026_scad_llm/DESIGN_T8.md`): **verta, bet kitaip** — ne JSON→.scad kompiliatorius, o `--export-format=csg` patikra. `check_csg.py` **neparašytas** |
| `07_Pilna_skill_analize` | 5 rekomendacijos | 3 padarytos (§7 skaidymas, fixtures, pasai), liko attachment (padaryta šiandien) |

**T8 konkretus žingsnis, kai bus laiko:** `scripts/check_csg.py` — renderina
`--export-format=csg`, tikrina `difference` tvarką ir transformacijų hierarchiją
BE renderio. Pigus patikrinimas, bet nėra įrodymo, kad reikalingas — kol kas
`check_bore_reachability` ir `check_subfeature_overlap` jau dengia praktinius atvejus.

---

## 4. Techninės skolos likučiai (prioritetas: žemas)

1. **Exit kodų nenuoseklumas** — 6 checker'iai grąžina 1, 6 grąžina 3. Dokumentuota
   (`tests/README.md`, `references/validation.md`), **bet nesuvienodinta** ir
   neturėtų būti — `validate_scad.sh` ir vartotojų skriptai jau remiasi šiomis
   reikšmėmis. Jei kada bus lūžis — `check_*.py` v2 su vienodais kodais ir
   compatibility sluoksniu.
2. **PETG** — biblioteka neturi išmatuotų PETG duomenų (`tolerances.md` tai sako
   atvirai, su cituota literatūra). Užpildyti galima tik **išmatavus** ir įrašius
   pagal esamą formatą (printeris, medžiaga, sluoksnis, ėminys, measured vs reported).
   Nesugalvoti skaičių.
3. **Fixtures** — 25 iš ~21 skripto, bet ne visi dengiami. Trūksta:
   `check_intake`, `check_plan`, `check_rules`, `check_service_envelope`,
   `check_dependencies`, `doctor`, `scad_tessellation`. Pridėti pagal tą patį
   šabloną (fail + pass pora, su realaus incidento citata).
4. **`research/` katalogas** — 6 failai (~40 KB), `.gitignore`intas, bet guli.
   Turi istorinę vertę (kaip daryti skill tyrimus), bet jo turinys išdalintas į
   `references/`, tad dalis dubliuojasi.

---

## 5. Kaip tikrinti, kad šis sąrašas negyvas

```bash
# ar golden set'as vis dar nematuoja?
python3 golden_scad/run_2026-09-11/compare.py golden_scad/run_2026-09-11/pre golden_scad/run_2026-09-11

# ar testai žali?
bash scad-modeler/tests/run_all.sh

# ar pasai vietoje (turetų buti ≥23)?
grep -rl 'RAG-passport' --include='*.md' --include='*.scad' . | wc -l

# ar R-taisyklių skaičius (turetų buti 18)?
grep -c '  - id: R-' scad-modeler/rules_manifest.yaml
```
