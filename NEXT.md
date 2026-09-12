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

## 3b. Po 2026-09-12 darbo liko (prioritetas: vidutinis)

1. **Deklaracijos neparašytos nė viename projekte.** Šablonai dabar yra
   (`templates/bores.json`, `attachments.json`), bet `attachment` SKIP 11/11,
   `bore_reachability` SKIP 10/11. Tai **darbo proceso** klausimas, ne kodas — deklaraciją
   turi parašyti tas, kas žino, kur varžtas. Svarstyti generatorių: iš `layouts`/
   `EXPECTED_HOLE` duomenų sugeneruoti juodraštį, žmogui patvirtinti.
2. **`assembly.scad` MODE sutartis** — 4-5 projektuose `MODE = 1;` vietoj
   apsaugoto. Šablonas `templates/assembly.scad` dabar yra. Kol nesutvarkyta,
   `collisions` ten nepasileidžia (teisingai — tripwire pagauna).
3. **bbox tolerancija** — `minkowski` narys pridėtas, bet sprendžiami tik
   paprasti spindulio reiškiniai. Sudėtingesni praleidžiami (tyčia, ne spėjama).
4. **Kaina nepermatuota po nuotėkio fix'o.** Prieš matavimą: +89,5%. Nuotėkis
   (`INCIDENTS.md` runtime kataloge) pašalintas, bet **naujo evalo nebuvo**. Be to,
   skill'as dabar **sąmoningai daro daugiau** (collisions visur, tripwire, coverage),
   tad kaina tikriausiai kilo — matuoti reikia kartu su padengimu, ne atskirai.

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
3. ~~**Fixtures** — trūksta 8 checker'ių.~~ **BAIGTA 2026-09-12:** visi 8 padengti
   (`assumptions_critical_open_fail`, `dependencies_change_class`, `intake_no_manifest`,
   `plan_no_decision_fail`, `rules_gate_fails_unchecked_project`, `service_envelope_blank_fail`,
   `doctor_machine_report`, `tessellation_minkowski_sphere`). 27 → **35** fixture'ų.
   Radinys kelyje: `R-04` turėjo `applies: always` + `(PASS|SKIP)` → tuščias projektas
   gaudavo **vakuuminį PASS**; pridėtas `glob_exists:` detektorius.
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

---

## 6. KAINOS KILIMAS — ką tik rasta, reikia išspręsti (prioritetas: AUKŠČIAUSIAS)

**Įrodymas:** `golden_scad/KOSTAI_2026-09-12.md`. Tie patys atvejai, 3 paleidimai
rankai, tokenai iš DSH sesijų `usage` įrašų:

| Matas | PRIEŠ | PO | Delta |
|---|---:|---:|---:|
| Tokenai (6 švarios poros) | — | — | **+70%** |
| Žingsniai (40 sesijų) | 2,5 | 4,2 | **+67%** |
| Įrankių kvietimai | 2,4 | 4,0 | **+67%** |

Kaina kilo **visais komponentais**: fresh input +17%, cache read +68%, output +299%.

**Tai sutampa su literatūra** (arXiv 2602.11988: konteksto failai +20% kaštų be
teisingumo prieaugio). Taigi stebėjimas patikimas, bet **priežastis neįrodyta**.

**Kandidatai „kaltininkams" (reikia abliacijos po vieną):**
1. `references/validation.md` (397 eil., rodyklėje iš SKILL.md)
2. `NEXT.md` (šis failas — agentai gali skaityti be reikalo)
3. `templates/README.md`
4. 12 naujų INCIDENTS įrašų (INCIDENTS.md 1173 eil.)
5. 22 pasai (papildoma eilutė kiekviename atidarytame faile)

**Testas:** PO versija be vieno iš šių, 6 poros × 2 rankos = 12 paleidimų, ~40 min.
Kol to nepadaryta — žinoma, kad kaina kilo, bet ne kodėl, tad negalima jos sumažinti.

**Taip pat:** ankstesnis „−52% failų" teiginys atšauktas (žr. PRES_PO korekciją).
