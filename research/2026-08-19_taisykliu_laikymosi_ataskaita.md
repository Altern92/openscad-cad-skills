# Ataskaita: SCAD skill taisyklių laikymasis ir verifikacinis medis v2

> Data: 2026-08-19 · Parašyta: **Alibaba Cloud Qwen (qwen-plus-character) subagentai**,
> orkestruota: deepseek-v4-flash (struktūra, paskirstymas, surinkimas, patikra).
> Kontekstas: skill repo `claude_skills/` (scad-modeler + openscad-cad), žr.
> `2026-08-19_taisykliu_laikymosi_tyrimas.md` dėl metodikos ir modelių patikros.

## Šaltinių žurnalas

| ID | Teiginys | Šaltinis (URL) | Tipas | Data | Būsena |
|---|---|---|---|---|---|
| A-001 | Verifikacijos kilpos mažina LLM haliucinacijas (CoVe, structured verification loops) | https://arxiv-org.ezproxy.obspm.fr/html/2606.21724v1 ; https://aclanthology.org/2025.bionlp-share.34/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-002 | Agentų patikimumas: veiksmų apribojimas, struktūruoti rezultatai, savęs gydymo kilpos | https://befailproof.ai/guides/how-to-make-ai-agents-reliable/ ; https://blog.n8n.io/make-ai-agents-more-reliable-and-restrict-the-actions-they-can-take/ ; https://dev.to/system_rationale/part-3-making-gemma-4-agents-production-ready-guardrails-structured-outputs-and-self-healing-575n | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-003 | Gamybiniams agentams neužtenka promptų — būsenos mašinos ir vartai | https://www.mygreatlearning.com/blog/production-ai-agents/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-004 | Formaliai verifikuotas kodo generavimas per savęs tobulinimą (AlphaVerus) | https://mlanthology.org/icml/2025/aggarwal2025icml-alphaverus/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-005 | CAD generavimo verifikacijos kilpa gerina rezultatą (CADCode-Verify) | https://proceedings.iclr.cc/paper_files/paper/2025/hash/81a934cd364e18ea6fdeaf57a93c17d4-Abstract-Conference.html ; https://huggingface.co/papers/2410.05340 | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-006 | CAD priklausomybių valdymas; FreeCAD recompute (topologinė eilė, tik nešvarūs mazgai) | https://ar5iv.labs.arxiv.org/html/2508.05940 ; http://opendeep.wiki/FreeCAD/FreeCAD/core-application-architecture.recompute-dependency-ordering-and-transactions ; https://dfam.designsociety.org/download-publication/37750/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-007 | FDM tarpų klasės ir poslinkiai (shrinkage, elephant foot, layer lines); judančios spausdintos dalys | https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/ ; https://tools.creative3dp.com/tools/press-fit-calculator/ ; https://www.ftcwiki.org/manufacturing-and-assembly/machining/tolerances ; https://thevirtualfoundry.com/3d-print-moving-parts/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-008 | NopSCADlib vitaminų filosofija: standartinės detalės realiais matmenimis, BOM | https://github.com/nophead/NopSCADlib ; https://deepwiki.com/nophead/NopSCADlib/4-component-library-(vitamins) | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-009 | OpenSCAD statinė analizė: tree-sitter-openscad (npm v0.5.1); openscad-language-server = LSP, ne ekstraktorius | https://www.npmjs.com/package/tree-sitter-openscad ; https://github.com/dzhu/openscad-language-server | pirminis | 2026-08-19 | ✅ su šaltiniu |
| A-010 | Perplexity MCP šioje sesijoje išjungtas (krisdavo dsh); paieškos per integruotą web_search | ~/.dsh/profiles/web/cordis.patch.yml | pirminis (vietinis) | 2026-08-19 | ✅ patvirtinta |

---

## 1. Problema: kodėl skill'as vis klysta

**Konkretūs gedimų pavyzdžiai iš INCIDENTS.md:**

1. **2026-08-19 – Belt-and-pulley sistema praleido visus patikrinimus, bet fiziškai neįmanoma įtempti.** Dvi pulkelės su fiksuotais centrais, be tensioner'io ar idler'io; `check_features.py` ir `check_collisions.py` praėjo švariai, nes tikrina galutinę surinkimo padėtį — niekas netikrino *surinkimo proceso*. Rezultatas: dizainas negaminamas.

2. **2026-08-19 – Gearbox_frame.stl atvaizdavimas kaip du nesusiję kūnai.** Apatinis diskas (~1043mm³) „plaukiojo ore", su viršutine bokšteliu susietas tik vizualiai. Po to, kai suportų spindulys buvo padidintas nuo 7mm iki 15mm (kad vengtumėt worm gear dantų konflikto), niekas nepatikrino, ar naujas spindulys vis dar liečiasi su disku — liko 3mm tarpo. `check_dimensions.py` ir `check_collisions.py` praėjo; bug aptiktas tik rankiniu būdu per render vaizdą.

**LLM taisyklių drift'o priežastys (iš `rules_enforcement.md`):**

1. **Konteksto perkrova** — ilgoje SKILL.md taisyklės „nuskęsta" tarp detalių; modelis seka paskutinį matytą pavyzdį, o ne taisyklę.
2. **Nėra pasekmių** — jei žingsnis praleidžiamas, niekas nesustoja; modelis gauna teigiamą grįžtamąjį ryšį už „greitą" atsakymą net ir be patikros.
3. **Taisyklė nėra patikrinama** — „privaloma atlikti X" be jokio mechanizmo patvirtinti, kad X tikrai įvyko (ir įvyko teisingai).

**Kodėl tik proza nepakanka šiam skill'ui:** prozinės instrukcijos be deterministinių vartų veikia tik kol kontekstas trumpas arba apkrova maža. Realus projektas greitai generuoja daug failų (`params.scad`, `part_*.scad`, `assembly.scad`) ir ilgą pokalbį — taisyklės pradedamos praleisti. Be skriptų, kurie **įrodo**, kad žingsnis įvykdytas (`check_connectivity.py`, `validate_scad.sh --all`), LLM linkęs tęsti darbą toliau vietoj to, kad grįžtų ir patikrintų ankstesnius sprendimus (kaip rodo abu incidentai). Proza primena; skriptas verčia.

---

## 2. Sprendimo idėja: verifikacinis medis v2

Pradinė vartotojo idėja buvo paprasta: sukurti **verifikacinį medį** — struktūruotą naršymo pagalbą, kuri atsako į klausimą *„kuris tikrinimas taikomas mano situacijai dabar?"*. Skill'e yra ~12 skirtingų skriptų su skirtingais triggeriais (mandatory, opt-in pagal failo/komentaro buvimą, manual-only), be to — du nauji proceso etapai (intake/analysis). Rašytinis aprašymas tampa per sunkiai naviguojamas; todėl gimė idėja — **Mermaid diagrama kaip navigacija**, papildyta deterministiniais script gate'ais, kurie užtikrina, kad modelis nepraleis privalomų patikrinimų.

### v2 pipeline — etapais eilės tvarka

1. **Stage 0 — Intake.** Vartotojo brief'as + informacija iš kitų AI → modelio generuojamas `requirements.json` / `design_manifest.json`. Prieš modeliavimą bėga `check_intake.py` gate — patikrina, ar specifikacijos failas egzistuoja ir atitinka JSON schemą.
2. **Stage 0.5 — Analysis.** Kiekvienas komponentas klasifikuojamas: **PRINTED vs PURCHASED**. Tada retrievinami 2–3 panašūs ankstesni variantai (embeddings + templates) adaptavimui.
3. **Planning.** Jei 3+ dalys arba architektūra neaiški — rašomas `plan.md`, valdomas `check_plan.py`. Jeigu ne — tiesiai į skaičiavimo lentelę.
4. **Geometry.** Prieš kuriant/redaguojant geometriją — jei feature sąveikauja su bearing/shaft/fastener/purchased part arba dalijasi `union()` su kita feature — privaloma Section 0.6 narrative (4 atsakymai: insertion path, neighbors, retention, purchased-part fit).
5. **Validation.** Po BET KOKIO pakeitimo bėga `validate_scad.sh --all`: automatiškai `check_connectivity.py` ant kiekvienos dalies, opt-in patikros (`check_assumptions.py`, `check_service_envelope.py`, `check_dimensions.py`, `check_features.py`, `check_bore_reachability.py`) — tik jei atitinkamas failas/komentaras egzistuoja.
6. **Mechanics.** Jei `design_manifest.json` turi `motion` bloką (kas nors juda) — pirmiausia static collision check, tada `motion_sweep.py`. Static patikra yra motion sweep'o precondition.
7. **Change-propagation (Choice Tree).** `check_dependencies.py` fiksuoja param→part dependency DAG. Redagavus kintamąjį — dirty-root nuo pasikeitusio parametro, perskaičiuojama tik paveikta grandinė topologine tvarka. Fallback — pilnas `--all` re-run.
8. **Rules Gate.** `check_rules.py` — paskutinis vartas prieš final report. Modelis PRIVALO paleisti rules manifest ir cituoti jo output'ą ataskaitoje. Tai enforcement loop, darantis taisyklių laikymąsi nepriklausomą nuo modelio atminties.
9. **Final Report (Section 8).** Tik po to — rezultatų santrauka su confidence tier ir tuo, kas vis dar estimated.

### Kodėl navigacinė diagrama + deterministiniai vartai, o ne proza?

Proza (SKILL.md) yra autoritetingas šaltinis, bet kaip **runtime navigacija** agentui per 12+ skriptų ekosistemą ji per ilga ir lengvai praleidžiama. Mermaid diagrama pateikia aiškią if/then sintaksę vizualiai — kiekvienas sprendimo mazgas matomas vienu žvilgsniu. Svarbiau — **script gates yra deterministiniai**: `check_intake.py`, `check_rules.py`, `validate_scad.sh --all` veikia nepriklausomai nuo to, ar LLM „prisimena" taisykles. Proza gali būti ignoruojama; shell komanda, kuri grįžta non-zero exit code — negali.

### Ką paveldėjome iš v1

V1 branduolys, kuris jau veikia ir yra validuotas, **liko nepakitęs**: environment check (`doctor.py` / `selftest.py`), planavimo etapas, narrative reikalavimas, `validate_scad.sh --all` vykdymas po bet kokio pakeitimo ir check ordering. v2 yra sluoksnis *virš* — struktūra aplink branduolį, ne jo perrašymas.

---

## 3. Intake ir analizė: iš aprašymo į planą (vartotojo vizija)

Skill'intake fazė paverčia vartotojo (dažnai neformalią) užklausą struktūruotu, mašina tikrinamu `design_manifest.json` (arba statiniams dizainams — `requirements.json`). Šis failas tampa **vieninteliu tiesos šaltiniu** visam tolesniam procesui: planavimui (§0.5), parametrų valdymui (`params.scad`, §2) ir galutiniams tikrinimams (§7).

### Schema

- **`goal`** — pagrindinis funkcinis tikslas vienu sakiniu.
- **`envelope`** — maksimalus apvalkalas `[x, y, z]` mm + `is_strict` žymeklis (ar ribų negalima viršyti).
- **`parameters`** — vardinti kintamieji; kiekvienas turi `status`: `"confirmed"` | `"estimated"` | `"unknown"`.
- **`interfaces`** — jungčių tipai (`bore`, `boss`, `slot`, `fastener_clearance`, `thread_insert`) su `mating_part` ir `clearance_mm`.
- **`motion`** — kinematika: `has_kinematics`, `dof_type` (`none`, `rotational`, `linear`, `planar`, `gear_mesh`).
- **`dependencies`** — DAG žemėlapis: parameter → sąrašas priklausančių modulių/perskaičiavimų.

### Statusų disciplina: niekada nekurti skaičių

Tai **didžiausios klaidų šaltinio kontrolė**. Kiekvienas skaičius iš vartotojo ar kito AI privalo būti paženklintas:

- **`confirmed`** — matuota arba gamintojo specifikacija.
- **`estimated`** — skaičius, žymimas `@estimated`; pateikiamas į `params.scad` kaip vardinis kintamasis ir į §8 ataskaitą kaip „vis dar vertinamas".
- **`unknown`** — privaloma paklausti atgal arba pamatuoti. **Niekada nesugalvoti.**

Skill'as netyliai **niekada** nepakelia `estimated` į `confirmed` modeliavimo metu.

### Klausimai, kuriuos visada klauskite atgal

1. Tikslas vienu sakiniu + ko tai **NEGALI** daryti.
2. Kurie matmenys yra kieti (privalo tilpti į esamą dalį/erdvę), o kurie minkšti.
3. Ar kas nors juda? Kaip (variklis, ranka, spyruoklė)? Sūkiai/apkrova, jei žinoma.
4. Kurios dalys jau egzistuoja / yra perkamos (guoliai, velenai, varžtai...)?
5. Spausdinimo apribojimai: printerio dydis, medžiaga, orientacijos pageidavimas.

### Panašių variantų paieška: skill „pats suvokia, ką reikės brėžti"

Norint **niekada nepradėti nuo nulio**, kai egzistuoja ankstesnis dizainas arba parametrinis šablonas, dengiantis pusę problemos, naudojami du mechanizmai:

**A. Embedding indeksas** (`scad_variants_index`): naudojant DashScope `qwen3.7-text-embedding` modelį (1024 dimensijos, kosinusinė metrika) indeksuojami visi ankstesni projektai — jų `README.md` + `.scad` įėjimo taško kintamųjų blokas. Dokumentas koduojamas pagal šabloną:

```
{category} | {title} | {description} | Motion: {kinematics_type} | Vitamins: {vitamins_list} | KeyParams: {key_dimensions}
```

Paieškos užklausa — suglaudinta intake JSON santrauka (`'{goal} {motion.dof_type} {vitamins}'`). Grąžinama **top-3**, persirikiuota pagal (a) vitaminų Jaccard persidengimą, (b) judesio DOF suderinamumą, (c) apvalkalo tilpimą.

**B. Parametriniai šablonai**: Gridfinity lentelės (`openscad-cad/references/gridfinity-params.md`) ir kartotiniai pattern'ai (`openscad-cad/references/patterns.scad`) patys yra variantų šaltinis. Kai užklausa atitinka žinomą pattern'ą (bin, bracket, sleeve, pocket), šablonas **YRA tas panašus variantas** — skill adaptuoja jo parametrus, o ne rašo geometriją iš naujo.

**Rezultatas:** skill siūlo **2–3 variantus** adaptavimui vietoj dizaino nuo pagrindo. Tik kai užklausa aiškiai reikalauja **naujo mechanizmo** arba neištirtos geometrijos — paieška praleidžiama ir apie tai pranešama plane (§0.5).

---

## 4. Spausdinama vs pirkta (guoliai, metalinės detalės)

Dizaino proceso metu kiekviena surinkimo dalis klasifikuojama kaip **spausdinta** (parametrinis `.scad` modulis) arba **pirkta / vitaminas** (NopSCADlib komponentas su realiais katalogo matmenimis). Šis sprendimas nėra estetinis — jis lemia surinkimo patikimumą ir saugumą.

### Sprendimo kriterijai

| Kriterijus | Spausdinti (`.scad`) | Pirkti / vitaminas (NopSCADlib) | Sprendimo riba |
|---|---|---|---|
| **Apkrova** (Load) | Statiniai korpusai, žemo sukimo momento laikikliai | Ašys, velenai, konstrukcinės tvirtinimo detalės | Jei šlytis/tempimas rizikuoja sluoksnių atsisluoksniavimu → plienas |
| **Tikslumas** (Precision) | ISO ≥ IT11 (tarpas ≥ 0.2mm) | Guolių kakliukai, velenai (ISO h6/h7/g6) | Tolerancija < 0.1mm → vitaminas + spausdinta kišenė |
| **Trintis / greitis** (Friction/Speed) | Žemi sūkiai (<60 rpm), slankikliai | Rutuliniai guoliai (608, 625), žalvario įvorės | Nuolatinis sukimasis arba μ < 0.15 → rutulinis guolis |
| **Kaina** (Cost) | Individuali geometrija, vienetiniai | M3/M4 varžtai, šiluminiai įdėklai, GT2 skriemuliai/diržai | Standartinė detalė < ~1€ → pirkti |
| **Įgyvendinamumas** (Print Feasibility) | Savaiminės atramos ≤45°, tiltai <15mm | Lygūs strypai, sraigtai, spyruoklės | Vidiniai spiraliniai keliai / nespaudinami iškyšos → pirkta |

### NopSCADlib „vitaminų" filosofija

„Vitaminas" — tai **standartinė rinkos detalė**, kuri visada modeliuojama tiksliais gamintojo katalogo matmenimis (`ball_bearings.scad`, `shafts.scad` ir kt.), bet **niekada nėra spausdinama**. Vieta surinkime rezervuojama pagal realius išorinius matmenis (OD, ID, plotį), o BOM sąrašas generuojamas su tiksliu pavadinimu ir kiekiu. Tai užtikrina, kad:

- Spausdintose dalyse bus teisingos kišenės (housing pockets) ir tarpai;
- Surinkimo metu nereikės improvizuoti ar gręžti/virinti;
- Galutinis prototipas bus surinktas iš realių komponentų, ne plastiko imitacijų.

### `purchased_components` masyvas dizaino manifeste

Kiekviena pirkta detalė fiksuojama `design_manifest.json` kaip objektas su `name`, `qty` ir raktais matmenimis (`bore_mm`, `od_mm`, `width_mm`). Pavyzdys:

```json
{ "name": "608ZZ bearing", "qty": 4, "bore_mm": 8, "od_mm": 22, "width_mm": 7 }
```

Šie matmenys pažymimi `@purchased` žyma parametrų medyje — kai keičiasi pirkto komponento matmuo, automatiškai paleidžiami tikslumo patikrinimai (fit checks), o ne geometrijos perskaičiavimai.

### Kodėl tai svarbu vartotojo vizijai?

Guoliai ir metalinės detalės yra **palaikomosios** (supporting), ne funkcinės — jos užtikrina mechaninį ryšį ir patikimumą ten, kur plastikas praranda stiprumą dėl anizotropijos ar trinties. Vartotojo vizijoje tai reiškia, kad galutinis produktas yra **surinktas iš realių detalių**: ašys sukasi be deformacijos, guoliai laiko apkrovas, o spausdintos dalys atlieka savo vaidmenį — geometrinę fiksaciją ir adaptaciją prie individualių matmenų. Toks hibridinis požiūris sumažina iteracijų skaičių, nes standartiniai komponentai jau yra patikrinti gamyboje.

---

## 5. Mechanika ir judančios dalys

Šis skyrius apibrėžia mechaninių sistemų dizaino principus, skirtus **3D spausdinimui (FDM)** — kai tikslumas ribotas, o klaidos kaupiasi greičiau nei tradicinėje gamyboje.

### Judesių taksonomija

Sistemoje atpažįstami keturi pagrindiniai judesio tipai:

| Tipas | Pavyzdžiai | Planavimo prioritetas |
|-------|-----------|----------------------|
| **Rotation** | Gear pair, lever pivot, hinge, knob/dial | Axis, teeth count, module, backlash, center distance |
| **Translation** | Slider-on-track, rack-and-pinion, lead screw | Track axis, travel distance, guide geometry, end stops |
| **Constrained rolling/sliding** | Bearing on shaft, pin-in-slot, worm gear | Bore/shaft fit, shoulder, axial retention, concentricity |
| **Flexure** | Living hinge, cantilever beam | Thickness, bend radius, cycle life, fatigue limit |

Kompleksiniai mechanizmai (pvz., svirtis, varantis slider per pin-in-slot) skaidomi į atskirus jungčių įrašus `design_manifest.json` `motion` masyve; priklausomybių grafikas (`drives` array) užtikrina, kad pakeitus vieną parametrą perskaičiuojamos visos žemyn esančios jungtys.

### `design_manifest.json` — auto-triggered checks

Kai manifeste yra **ne tuščias** `motion` masyvas, `validate_scad.sh --all` automatiškai paleidžia:

1. `check_collisions.py` (static pose)
2. `motion_sweep.py` (dynamic sweep)

`motion_sweep.py` naudoja **periodicity collapse**: jei visi driver'ai revolute su dantų skaičiumi, turinčiu bendrą periodą, sweep sumažinamas iki vieno danties pitch (pvz., 18° 20-dantų gear'ui), taupant ~20× laiko. Nustatęs glaudžiausią poziciją, atlieka **adaptive refinement** ±5° intervale su padalintu žingsniu.

### Patikrinimų pipeline eilė

Eilė kritinė ir fiksuota:

1. **Static collision detection** (`check_collisions.py`) — **PIRMAS**, prieš bet kokį motion sweep. Rezultatai: pass / degraded / fail.
2. **Dynamic sweep** (`motion_sweep.py`) — **ANTRAS**. Sweep'ina kiekvieną driver per declared range. Darbas priklauso nuo švarios statinės patikros — sweep per jau susikertančią geometriją yra beprasmis.
3. **Bearing & shaft alignment** — tikrina bore-to-shaft, outer race-to-housing, shoulder, axial retention, co-linearity.

Bet kuris upstream check fail'as sukelia **short-circuit**: fix at source → re-run `validate_scad.sh --all` nuo pat viršaus.

### FDM fit skaičiai (CAD gaps)

Tarpai matuojami **CAD modeliuose**; realūs spausdinti tarpai skiriasi dėl FDM klaidų (žr. žemiau).

| Fit tipas | CAD tarpas (mm) | Paskirtis |
|-----------|-----------------|-----------|
| **Press fit** | −0.10 … −0.25 (interference) | Axial retention, snap fits |
| **Transition fit** | 0.00 … +0.05 | Bearing outer race in housing |
| **Slip fit (light)** | +0.15 … +0.25 | Minimalus slankiojimo tarpas (PLA, 0.2mm layer height) |
| **Slip fit (loose)** | +0.30 … +0.50 | Pin'as slote, greitai judantys slankikliai |
| **Running clearance** | +0.50 … +1.00 | Velenas besisukantis spausdintoje įvorėje |

Be kalibracijos profilių naudojama konservatyvi default vertė ir pažymima `PATIKRINTI`.

### Trys pagrindinės FDM kompensacijos

| Klaida | Efektas | Kompensacija |
|--------|---------|--------------|
| **Shrinkage** (aušinimas) | Matmenys mažesni nei CAD ~0.2–0.5% | Kritinius bore diametrus didinti pagal measured bias; kalibruoti su test cube |
| **Elephant foot** (pirmojo sluoksnio squeeze) | Pirmojo sluoksnio OD didesnis ~0.1–0.3mm | Mažinti first-layer height; spausdintų cilindrų press fit'ams mažinti CAD OD elephant-foot dydžiu |
| **Layer lines** (stair-stepping) | Bore diameter osciliuoja ±0.1 × layer_height | Apvalius bores spausdinti horizontaliai (XY plane); jei vertikalus bore būtinas — CAD diameter didinti +0.1mm per 0.2mm layer height |

Papildoma: **nozzle diameter tolerance** (±0.025mm) gali pastumti visus features link smaller internal / larger external — kalibruoti nozzle actual vs nominal ir adjust global clearance `params.scad` faile.

Visos kompensacijos pritaikomos **pirma** `params.scad` lygmenyje; po to paleidžiamas pilnas validation pipeline.

---

## 6. Pokyčių / perskaičiavimo medis („pasirinkimų medis")

**Reikalavimas:** „Jeigu kažkur kažką pakeitė, žinotų, kokios detalės susijusios ir ką reikia perskaičiuoti."

Kad vartotojas visada matytų, kurio parametro pokytis veikia kokį geometrijos elementą, kurią detalę ir ar pažeidžiamas kuris nors patikrinimas, diegiama **dependency DAG** (directed acyclic graph) sistema — modeliuota pagal FreeCAD recompute mechanizmą: perskaičiavimas vyksta topologine tvarka, tik „nešvarūs" (dirty) mazgai peržiūrimi.

### Dependency DAG lygmenys

```
params → derived params → modules (feature builders) → parts (.stl failai) → assembly
```

Kiekvienas mazgas turi `kind` (param, module, part); kiekviena briauna neša `kind` (`expression`, `module`, `part`), kad runner'is atskirtų kintamojo priklausomybę nuo topologinės/part sąsajos.

### Algoritmas: pokytis X → ką perskaičiuoti?

1. **Dirty-roots:** redaguojant kintamąjį `X`, pažymima `dirty = {X}`; jei pasikeitė failo `mtime`, įtraukiami visi jo deklaruoti parametrai.
2. **Forward closure:** iš kiekvieno dirty mazgo briaunomis ieškoma visų žemyn esančių mazgų (parametrai, moduliai, detalės, surinkimas). Kiekvienas mazgas klasifikuojamas pagal veiksmą:
   - Param/derived-param → perskaičiuoti išraišką, paleisti `assert` tikrinimus (*Calculations*, `validate_scad.sh` praleidžiamas).
   - Module → **Geometry** tam modulio feature + jo detalės failui.
   - Part → **`validate_scad.sh --all`** tai detalei (bbox/connectivity/hole — dimensionless, paleidžiami tik jei keitėsi parametrai, kurie tieka tą geometriją).
   - Assembly / judantis gear mesh → **Situational**: sub-feature overlap → static collision → motion sweep.
3. **Topological order:** tikrinimai vykdomi briaunų nurodyta tvarka. Tik parametro pokytis yra pigesnis (render nereikalingas).
4. **Fallback rule:** jei parseris nesupranta struktūros (pvz., nežinomas token'as, `include` neparsinto failo), pakeliama į `validate_scad.sh --all` ir fiksuojama — „wrong subgraph beats a missed one".

### Parserio pasirinkimas

Naudojamas lengvas Python tokenizer'is (regex-based), o ne tree-sitter-openscad. Argumentas: OpenSCAD gramatika per tree-sitter duoda `variable_definition` ir `call_expression` mazgus, bet Python repo'je tai vilktų wasm/FFI runtime. Tokenizer'is išgauna viršutinio lygio `name = <expr>;` priskyrimus ir `use/include` deklaracijas, tada iš RHS renka minimus identifikatorius. Tikslus aritmetika nereikalinga — tik **name→names dependency edge**. PoC: `scripts/check_dependencies.py` (`--change` ir `--all` režimai, testuotas).

### Vartotojo matomas rezultatas

Pakeitus parametrą, spausdinamas paveiktų mazgų medis:

```
┌ Change: P1_teeth 12→14 (params.scad:22)
│  expr  ─ ratio_1, CD1 → assert(ratio_1≈6.0) [FAIL: 4.0]  ← check
│  module─ P1_gearhousing, P2_gearhousing
│  part  ─ P1_gear.stl [dirty]  ├─ connectivity ├─ EXPECTED_BBOX
│  fit   ─ P1_bore ⊃ P1_pinion (press 0.05mm) @purchased  ├─ check_features
│  assembly─ rear_axle (static geom)  →  situational: collisions
└ Unaffected: S1, jackshaft, diff_ring  (skipped)
```

`[FAIL]` ant assert'ų trumpina žemyn esančius render'ius ir nukreipia į `calculations.md`. Lapai po „Unaffected" rodo, kad lazy scope veikia — tik meshing/printed-mate grandinė perkraunama.

---

## 7. Taisyklių laikymosi variklis (kaip užtikrinti, kad skill KASKART laikytųsi taisyklių)

Problemą apibūdina trys patvirtintos priežastys, kodėl agentai nukrypsta nuo taisyklių: **konteksto perkrova** — taisyklės „nuskęsta" ilgoje SKILL.md; **nėra pasekmių** — praleidus žingsnį niekas nesustoja; ir **taisyklė nėra patikrinama mašinai** — „privaloma atlikti X" be mechanizmo įrodyti, kad X tikrai įvyko. Vienas „būk atsargus" promptas šioms problemoms nepadeda — modelis gali pasirodyti sekąs, bet be deterministinio patikrinimo tai tik imitacija. Literatūra tai patvirtina: verifikacijos kilpos mažina haliucinacijas ([CoVe, arxiv 2606.21724](https://arxiv-org.ezproxy.obspm.fr/html/2606.21724v1)), struktūruoti rezultatai ir veiksmų apribojimai būtini patikimiems agentams ([BeFailProof](https://befailproof.ai/guides/how-to-make-ai-agents-reliable/), [Gemma 4 guardrails](https://dev.to/system_rationale/part-3-making-gemma-4-agents-production-ready-guardrails-structured-outputs-and-self-healing-575n)), o gamybiniams agentams neužtenka promptų — reikia būsenos mašinos ir vartų ([Production AI agents](https://www.mygreatlearning.com/blog/production-ai-agents/)).

Todėl numatytas **keturių sluoksnių vykdymo modelis**:

**L1 — Prompt lygmuo (primena).** SKILL.md pradžioje — trumpa eilutė, nukreipianti į `rules_enforcement.md` ir `validation_decision_tree.md`. Kiekviena taisyklė — vienoje vietoje, be dublikatų (dublikatai skiriasi — modelis pasirenka paskutinį).

**L2 — Deterministiniai vartai (įrodo).** Kiekvienas privalomas žingsnis gauna skriptą, kuris *įrodo*, kad žingsnis įvyko. Pavyzdys — jau veikiantis `check_plan.py`:

| Privalomas žingsnis | Vartas |
|---|---|
| Intake | `check_intake.py` (naujas) — validuoja `requirements.json`/`design_manifest.json` |
| Planavimas (§0.5) | `check_plan.py` (yra ✅) |
| Geometrija | `validate_scad.sh --all` (yra ✅) |
| Judančios dalys | `motion_sweep.py` (yra ✅, trigger per `design_manifest.json.motion`) |
| Pokyčių plitimas | `check_dependencies.py` (yra ✅) |

**L3 — Savęs patikros kilpa.** Prieš galutinį pranešimą modelis privalo paleisti taisyklių manifestą (L4) ir pats įvertinti kiekvieną eilutę: *padaryta / praleista / netaikoma*. Praleista → grįžti, padaryti, paleisti iš naujo. Tai **ne pasirenkamas žingsnis**, o privalomas vartas prieš atsakymą vartotojui.

**L4 — Mašiniškai tikrinamas taisyklių manifestas.** Failas `rules_manifest.yaml` (šalia SKILL.md) — vieningas visų privalomų taisyklių sąrašas su ID, taisykle, patikrinimo komanda, varto skriptu ir taikymo sąlyga. Naujas skriptas `check_rules.py` paleidžia jį prieš §8. Modelis privalo **cituoti jo išvestį** galutinėje ataskaitoje.

**Kodėl tai stipresnė už „pasakyk modeliui būti atsargesniam"?** Nes taisyklės laikymasis **nebepriklauso nuo modelio atminties**: jį įrodo skriptai, o modelio darbas — tik juos paleisti ir rezultatus cituoti. Gedimo tvarkymas aiškus: stabdyk → taisyk šaltinyje → paleisk iš naujo nuo viršaus → užfiksuok incidentą. Šis principas atitinka formaliai verifikuotą kodo generavimą per savęs tobulinimą ([AlphaVerus, ICML 2025](https://mlanthology.org/icml/2025/aggarwal2025icml-alphaverus/)) ir CAD generavimo verifikacijos kilpą ([CADCode-Verify, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/81a934cd364e18ea6fdeaf57a93c17d4-Abstract-Conference.html)).

---

## 8. Rekomendacijos ir tolimesni žingsniai

Dabartinė būsena: pagrindiniai geometrijos tikrinimo skriptai (`check_*.py`, `validate_scad.sh`) veikia, planavimo vartas (`check_plan.py`) parašytas, `validation_decision_tree.md` v2 suformuluota. Trūksta procesinių vartų ir integracijos tarp etapų.

**Eiliškumas įgyvendinant:**

1. **`check_intake.py`** — sukurti JSON schemos `requirements.json`/`design_manifest.json` validavimą. Be šio varto Stage 0 lieka nepatikrinta.
2. **`rules_manifest.yaml` + `check_rules.py`** — surašyti visas privalomas taisykles (ID, rule, check, gate, applies) ir paleisti prieš §8. Tai paskutinis trūkstamas elementas, dėl kurio taisyklių laikymasis tampa nepriklausomas nuo modelio atminties.
3. **Embedding variantų indeksas** — panaudoti DashScope `qwen3.7-text-embedding` (kreditai jau yra) pagal `intake_and_analysis.md` template. Tai leidžia gauti 2–3 panašių ankstesnių variantų šablonus vietoj nulio.
4. **`motion_sweep` auto-trigger** — užbaigti sujungimą: `design_manifest.json.motion` blokas automatiškai paleidžia statinį `check_collisions.py` (prerequisite) → `motion_sweep.py`.

**Top-3 praktikos, kurias skill turėtų pradėti taikyti nedelsiant:**

1. **Status disciplina: confirmed / estimated / unknown.** Kiekviena skaitinė parametro vertė galutinėje ataskaitoje turi statusą. „Estimated" reikalauja paaiškinimo, kodėl įvertinta, o ne matuota; „unknown" — kodėl negalima nustatyti dabar.
2. **Taisyk šaltinyje ir paleisk iš naujo nuo viršaus.** Kai vartas nepraleidžia — netaisoma „išvestyje", o taisomi parametrai/geometrija/skriptas ir paleidžiama `validate_scad.sh --all` nuo pradžios. Kaskadinis efektas: apačia praeina tik tada, kai viršūnė švari.
3. **Cituok `check_rules.py` išvestį galutinėje ataskaitoje (§8).** Galutiniame pranešime pateikti taisyklių manifesto patikrinimo rezultatą — vienintelis būdas įrodyti, kad L3–L4 įvyko, o ne tik buvo pretenduojama juos įvykdyti.

---

## Metodika (kas ką rašė)

| Sekcija | Autorius (modelis) |
|---|---|
| §1, §2 | Alibaba Cloud Qwen `qwen-plus-character` |
| §3, §4 | Alibaba Cloud Qwen `qwen-plus-character` |
| §5 | Alibaba Cloud Qwen `qwen-plus-character` (pirma versija Mistral `ministral-3b` — atmesta dėl kokybės) |
| §6 | Alibaba Cloud Qwen `qwen-plus-character` |
| §7, §8 | Alibaba Cloud Qwen `qwen-plus-character` |
| Struktūra, paskirstymas, surinkimas, šaltinių žurnalas, patikra | deepseek-v4-flash (orkestratorius) |

Pastaba: NVIDIA `deepseek-v4-flash-0731` ir Google `gemini-3.7-flash` šioje sesijoje workflow'e buvo nestabilūs (2× nuliai, nors tiesiogiai per API veikia — žr. `2026-08-19_taisykliu_laikymosi_tyrimas.md`); jų kampus perėmė Qwen subagentai.
