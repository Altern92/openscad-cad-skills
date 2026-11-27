<!-- RAG-passport: file=NEXT.md | skill=all | applies_to=[future-work, roadmap, known-gaps] | version=2026-09-12 | source=07_Pilna_skill_analize + PRES_PO eval + AB_IRANKIAI -->
# NEXT — ką daryti toliau (2026-09-12 būklė; §0 eilė atnaujinta 2026-11-14)

> **2026-11-14:** aktuali yra §0 eilė. §1 (golden set) ir §6 (kainos kilimas) iš esmės uždengė P7 (`bench/PIPELINE_BENCH_2026-11-01.md`, `bench/AGENT_EVAL_2026-11-01.md`), P18 ir P19 (SKILL.md 56,7→12,8 KB ir 25→8,4 KB); jie palikti istorijai. Atviri lieka §3b, §4 ir §0 „Toliau“. Skaičiai žemiau (45 fixture'ai ir pan.) pasenę: 2026-11-14 suite 95/95.

Būsena šiandien: trys skill'ai, 23 pasai, **45** regresijos fixture'iai, 18 R-taisyklių,
`scad-modeler/SKILL.md` **853** eil. Testai **45/45**. Įrankių A/B (11 projektų × 2 versijos):
`CHECK_RESULT` eilučių **89 → 198**, `COVERAGE` **0/11 → 11/11**.

**Tyrimo medžiaga:** `_wiki/scad/` (8 failai su Mermaid) — 5 standartai, matavimo
metodai, ir **6 klaidingos išvados su pataisymais**. Skaityti prieš didelį pakeitimą.

**Šis failas — vienintelis sąrašas to, kas žinoma ir nepadaryta.** Kiekvienas
punktas turi įrodymą, kodėl jis čia. Kai padaromas — ištrinti, ne pažymėti.

---

## 0. DARBŲ EILĖ nuo 2026-11-01 (vystymas Mac mini, `~/Github/Claude_Code_SCAD_Skill`)

Tyrimas: Obsidian `Research/Runs/2026/2026-11-01-openscad-skill-tobulinimas-pagal-incidentus.md`.
Kiekvienas punktas per `feature-loop`: AC → vartotojo patvirtinimas → TDD → `tests/run_all.sh` visi žali (73/73 2026-11-01), ir dev repo, ir per `~/.claude/skills`.
Baigus punktą: pažymėti `[x]` su commit'u, ne trinti (ši eilė istorijai).

- [x] **P1 Aplinkos vartai.** ✅ 2026-11-01 (bc43025, f110a8f, cf562ea, 524c649: `env_gate.py`, `resolve_python.sh`, `setup_env.sh`, venv `~/.local/share/scad-modeler/venv`, exit 5). Skill'as randa `.venv` (`~/Github/Claude_Code_SCAD_Skill/.venv`) ir `openscad`; jei trūksta — STOP su instrukcija, ne tęsti be patikrų. Įrodymas: MBP 32/48 patikrų exit 4 (2026-11-01).
- [x] **P1b Checker'ių mutantai.** ✅ 2026-11-01 (338535b, c7d9960: `tests/mutants.tsv` 16/16 checker'ių, `mutant_coverage` fixture; naujų fixture nereikėjo). Kiekvienam `check_*.py` bent vienas sąmoningai sugadintas modelis `tests/mutants/`, kuris PRIVALO duoti FAIL; tylus SKIP = STOP. Pagrindas: 31/95 incidentų = klaidingas PASS/tylus SKIP; LLMorpheus (Tip ir kt., 2025). Tyrimas: Obsidian `Research/Runs/2026/2026-11-01-openscad-skills.md`.
- [x] **P2 Trys pigios taisyklės iš „not yet“ incidentų:** (a) jokių numatytųjų verčių apskaičiuojamiems matmenims (beam 211 vs 216.5), (b) standartų konstantos be apvalinimo (EIA 44.45), (c) failo magijos patikra prieš STL parserį (ASCII vs binary). ✅ 2026-11-01: `check_scad_lint.py` (a: vienas kvietimas apskaičiuoja, kitas praleidžia → FAIL; b: 1U/colis/19"/EIA žingsnis, 500 bibliotekų failų 0 klaidingų). (c) jau uždengta: visi skriptai skaito STL per `trimesh` arba `stl_extent.py` (abu formatai, fixture `stl_extent_both_formats`); liko tik nuoroda SKILL.md, kad ad-hoc matavimai eitų per `stl_extent.py`.
- [x] **P12 Kiaurymių skaičius iš topologijos** (EvoCAD 2510.11631: Eulerio charakteristika). `// EXPECTED_THROUGH_HOLES: N` → `check_topology.py` lygina su tinklo genus = (2·kūnai − χ)/2 (trimesh). Pagrindas: B klasė 16/95 incidentų (užaklintos/nepramuštos skylės); 2026-11-01 bandymas: 2 kiaurai χ=−2 g=2, 1 aklina χ=0 g=1, abi aklinos χ=2 g=0. Ribotumas: genus skaičiuoja „rankenas“ (kiaurai pjūvis, žiedas, susikertančios skylės irgi), todėl deklaruojamas topologinis skaičius. ✅ 2026-11-01: `check_topology.py`, `CHECK_RESULT topology`.
- [x] **P14 Bibliotekų versijų užrakinimas** (iš vartotojo Rust pasiūlymo „build_key su BOSL2 revizija“; **patvirtinta realiu radiniu 2026-11-01**). `esp32_rc_modelis/.../steering_reduction_gearbox/parts/output_gear.scad`: su BOSL2 2.0.750 (iCloud kopija) genus 3, bbox z −10,84..2,84, teisinga; su 2.0.782 (mini numatytasis `~/Documents/OpenSCAD/libraries`) `worm_gear(anchor=CENTER)` pasislenka, veleno angos nėra (genus 0), varžto skylė tampa uždara ertme (−366 mm³ = π·2,3²·22). `validate_scad.sh` sustoja ties `analytic_bounds` ("an assert() in params.scad failed"), bet nesako, KURIS assert ir kad kalta bibliotekos versija; tiesioginis `openscad` render'is grąžina sugadintą STL be klaidos. Darbas: projekto `libs.lock` (BOSL2/NopSCADlib `version.scad` + OpenSCAD versija) → `env_gate.py` FAIL, kai įdiegta versija kita; versijos į `build/.validation_state.json`; assert pranešimą rodyti išvestyje. ✅ 2026-11-01: `env_gate.py --write-lock`/`libs.lock`, `"libs"` būsenoje, WARNING įvardijamas kaip warning; mini viena bibliotekų vieta (BOSL2 92d697c = 2.0.750 + NopSCADlib); `libs.lock` 6 realiuose projektuose. Tikroji priežastis: 2.0.782 neturi `worm_gear_thickness()`.
- [x] **P15 Sąžiningas verdiktas** (išorinis auditas MBP 2026-11-01, kiekvienas teiginys permatuotas mini). ✅ 2026-11-01: `declarations` patikra (kiekviena spausdinama dalis: `EXPECTED_BBOX` + `EXPECTED_THROUGH_HOLES` arba `NO_BBOX:`/`NO_THROUGH_HOLES_CHECK:` su priežastimi), `plan=FAIL` 3+ dalims be plan.md (kitaip SKIP), `service_envelope=SKIP` be failo, INCONCLUSIVE → exit 2 + `NOT VERIFIED:`, paskutinė eilutė „All executed checks passed (… not-applicable …)“, `check_rules.py` gate'ai su `resolve_python.sh`, R-19, šablonų pataisos (part_geometry pervadinti, bores.json = vietinės koordinatės), pavyzdys deklaruoja abu. Audito M4 (62 % plonesnis krumpliaratis) dabar `dimensions=FAIL`. Spec: `docs/superpowers/specs/2026-11-01-p15-honest-verdict-ac.md`. Suite 67/67.
- [x] **P16 Coplanar kontakto klaidingas FAIL** ✅ 2026-11-01: atkurta mini (atvira dėžutė + dangtis su 4 skylėmis, gulintis ant briaunos → „40.000 mm“ = dėžutės plotis; dangtis be skylių praeidavo). `check_collisions.py` `bounded_depth()`: FCL gylis apribotas boolean sankirtos mažiausiu matmeniu, tuščia sankirta = 0. 1 mm įleistas dangtis dabar rodo 1.000 mm (anksčiau 2.000). Fixture `collisions_coplanar_contact`. (auditas E1, sąlyginis): korpuso ramstis + plonas dangtis, 0 tūrio sankirta → `DECLARED INTERFERENCE OUT OF RANGE … penetration depth 40.000 mm`; du paprasti kubai praeina. Pirma atkurti mini, tada fixture. Dažniausias atvejis („dėžutė + dangtis“).
- [x] **P17 Likę audito punktai** ✅ 2026-11-01: (a) `doctor.py` persileidžia per `resolve_python.sh` (fixture `doctor_uses_mesh_python`); (b) Stop hook mato `.scad`, rašytus per Bash (`> >> tee sed -i cp mv install`), skaitymo komandų neblokuoja; DSH plugin'o NErašiau: įdiegtame `@deepseek-ai/dsh` nėra `turn-stopping` (audito teiginys mini nepasitvirtino), Cordis/pnpm plugin'as — atskiras darbas, kai DSH bus naudojamas SCAD darbui; (c) `acceptance.py emit` (P5); (d) paliekama: INCONCLUSIVE dabar exit 2. Pradinis aprašas: (a) `doctor.py` paleistas sistemine python3 rodo tier 1 vietoj 2 (turi naudoti `resolve_python.sh`); (b) DSH neturi Stop-hook atitikmens (lifecycle `agent/turn-stopping`), hook nemato `.scad`, rašytų per Bash; (c) automatinės deklaracijos iš `requirements.json` → dalis P5; (d) collisions bbox euristika INCONCLUSIVE, kai dalies bbox = assembly bbox (F7) — dabar bent exit 2.
- [x] **P13 Kintamojo keitimo testas** ✅ 2026-11-01: `check_sensitivity.py` (`CHECK_RESULT sensitivity`), `// SENSITIVE_TO: param` → `-D param=×1,5`, nepakitęs bbox+tūris = FAIL; reikšmė skaitoma iš dalies/include. Pavyzdys deklaruoja `gear_thickness`. Fixture `sensitivity`. Pradinis aprašas: (Gemini ataskaita, šaltinis tinklaraštis): `// SENSITIVE_TO: param` → perrenderinti su `-D param=1.5×` ir reikalauti, kad bbox/skylės pasikeistų; gaudo įkaltas konstantas. Mažesnis prioritetas nei P12.
- [x] **P3 Skylių kandidatai iš CSG** ✅ 2026-11-01: `bore_candidates.py --scad parts/X.scad > bores.json` (CSG medis, kiekvienas atimtas cilindras, ašis vietinėmis koordinatėmis, galai įtraukti 0,05 mm; kūgiai praleidžiami). Realūs duomenys SSD: 241 detalė, 0 klaidų, 156 su kandidatais; reachability rado tikrą defektą `server_rack_modular_v4/v7/parts/board_shelf.scad` — M3 skylės uždengtos vientisais standoff'ais, pridėtais po `difference()` (varžtas nepraeis). Pirmas variantas davė klaidingus radinius `gearbox_frame` (taškas ant pjoviklio galo plokštumos) → įtraukimas. Fixture `bore_candidates`. Pradinis aprašas: (`check_csg.py`, T8): `--export-format=csg` → visi `difference()` cilindrai → `bores.candidates.json`; žmogus patvirtina į `bores.json`. Ne auto-deklaracija. Įrodymas: bore_reachability SKIP 10/11, B klasė 22 incidentai.
- [x] **P4 Jungčių grafas** ✅ 2026-11-01: `check_joint_graph.py` (`CHECK_RESULT joints`, R-21 su nauju `applies: glob_min:2:`), dalis be joints.json kontakto / attachments.json `part`/`to` / `// NO_JOINT: priežastis` = FAIL; grupių skaičius INFO. `attachments.json` šablonas: vietinės koordinatės (buvo „assembly“), naujas `to`. Fixture `joint_graph`. Pradinis aprašas: (MUSE stiliumi): kiekviena dalis turi ≥1 jungtį (varžtas/presas/klijai/magnetas) `attachments.json`; be jungties = FAIL. D klasė 13 incidentų.
- [x] **P5 Patvirtinti priėmimo skaičiai** ✅ 2026-11-01: `acceptance.json` (bbox + through_holes kiekvienai daliai) → `acceptance.py approve --quote "<vartotojo žodžiai>"` → `acceptance.lock` (sha256); `CHECK_RESULT acceptance` FAIL, kai nepatvirtinta / pakeista po patvirtinimo / dalis deklaruoja kitus skaičius; Stop hook blokuoja, jei citatos nėra vartotojo žinutėje; `emit` sugeneruoja deklaracijas; R-20. Spec `docs/superpowers/specs/2026-11-01-p5-acceptance-lock-ac.md`. Suite 70/70. Pradinis aprašas: **P5 Reikalavimų testai prieš geometriją** (CADTests + CIT-CAD + ProCAD): intake → `requirements_tests` → vartotojas patvirtina → geometrija. **Papildyta 2026-11-01 (vartotojo Rust pasiūlymo įvertinimas):** dabar `EXPECTED_*` deklaracijas rašo tas pats agentas tame pačiame `.scad`, todėl jis gali pataisyti deklaraciją, o ne detalę. P5 turi perkelti priėmimo reikalavimus į atskirą, vartotojo patvirtintą failą su sha256, kurį checker'iai skaito, o stop gate blokuoja jo keitimą be patvirtinimo. Rust/SQLite perrašymas atmestas: runner, doctor, sha256 būsena, JSONL istorija, PASS/FAIL/SKIP/INCONCLUSIVE ir mutantai jau yra Python'e (63 fixture'ai).
- [x] **P6 `openscad-organic` patikros:** (2026-11-01: check_proportions.py + check_silhouette.py, CHECK_RESULT proportions/silhouette, fixture organic_checks, suite 74/74) siluetų IoU su referencine nuotrauka, proporcijų lentelė iš šaltinio prieš modeliavimą.
- [x] **P7 Golden set v2:** (2026-11-01 agentų dalis: bench/agent_eval.py, Sonnet subagentai, full 5/5, lean 4/5 -> bench/AGENT_EVAL_2026-11-01.md) (2026-11-01 deterministinė dalis: bench/pipeline_bench.py, 30 defektų + 7 kontrolinių, recall 29/29, false alarms 0/7 -> bench/PIPELINE_BENCH_2026-11-01.md; agentų QA v2 su cost-of-pass laukia leidimo mokamiems paleidimams) ≥30 sunkių atvejų su spąstais + cost-of-pass (žr. §1, §6).
- [x] **P8 Sprendimas dėl 258 mokymo pavyzdžių** (2026-11-01 vartotojas: eval. Padaryta: 6 tikri defektai į pipeline_bench (35/35, 0/9) + 5 agentų užduotys agent_eval.py; LoRA/RAG atmesta) (§2) — vartotojo. Argumentas prieš LoRA: Text-to-CadQuery (2505.06507) fine-tuning'o prieaugis gautas su ~170 tūkst. porų; 258 yra ~0,15 % to kiekio.
- [x] **P9 Stop gate** (Uber MCP Gateway principas „deterministinis sprendimas kiekvienam kvietimui“; vault `Research/Runs/2026/2026-10-31-mcp-gateway-agentbus.md`). ✅ 2026-11-01 (0d8b5e5): `hooks/scad_stop_gate.py` – sesija, kurioje Edit/Write keitė `.scad`, nesibaigia, kol `build/.validation_state.json` neturi to failo dabartinio sha256. Įjungta mini `~/.claude/settings.json` (Stop). Ribotumas: `.scad`, sukurtas per Bash, nematomas.
- [x] **P10 Vienas validacijos kelias.** ✅ 2026-11-01 (6feff84): `validate_scad.sh part.scad` vienai detalei už `parts/` ribų; `openscad-cad` nebemoko leisti checker'ių rankomis.
- [x] **P11 Dokumentacija = kodas.** ✅ 2026-11-01 (431d749 + pataisa po incidento): `skill_docs_match_code` fixture – SKILL.md/references minimi skriptai ir flag'ai egzistuoja kode.

- [x] **P18 scad-modeler SKILL.md 56,7 KB (~14k tokenų) sumažinti** — ATLIKTA 2026-11-01: SKILL.md 12,8 KB, pilnas tekstas references/workflow_details.md; slim n=2×5: 10/10 PASS, vid. 73 712 tok. (−6,8 % vs full, triukšmo ribose). Buvęs aprašas: — 2026-11-01 abliacija (bench/AGENT_EVAL_2026-11-01.md): agentai skaito tik SKILL.md failus, validation.md/INCIDENTS/NEXT neatidaromi; be scad-modeler SKILL.md −12,8 % tokenų, bet viena užduotis (vyrio ašis) blogesnė. Kelias: perkelti retai reikalingus skyrius į references/, palikti vartus ir komandas; matuoti tuo pačiu agent_eval (n ≥ 3).
- [x] **P19 openscad-cad SKILL.md 25 KB → 8,4 KB + tylus validatoriaus log'as + motion formatas** — 2026-11-01 (agent-reach tyrimas: SkillsBench, SkillReducer, Anthropic best practices). Agent_eval n=3×5: 15/15 PASS, vid. galutinis kontekstas 69 050 (−6,2 % vs slim, −12,7 % vs full), suma per ėjimus −4,1 %. Rasti ir pataisyti 2 validatoriaus defektai (motion be drivers → traceback; dviejų plokštumų kontaktas → 10 mm netikras gylis).
- [x] **P20 Mazgai, sukurti ne per parts/*.scad, irgi tikrinami fasteners/collisions** ✅ 2026-11-14: `fasteners.json` `mounts` (dalis → host, `min`), `validate_scad.sh` leidžia `fasteners` be `assembly.scad` ant `build/positioned/*.stl`, fixture `fasteners_mount` + `fasteners_mount_unfastened_fail` (trimesh STL, ne OpenSCAD), mutantas. Host galvos po dalimi = esamas `head blocked` (host varžtus irgi deklaruoti). Ribotumas: nedeklaruotos host skylės nematomos. Spec `docs/superpowers/specs/2026-11-14-p20-p22-genkit-github-ac.md`. (INC-2026-11-13-02, pasikartojimas INC-2026-11-08-01). Big_CNC Z variklio laikiklis buvo trimesh dėžės `build_full.py` viduje, todėl R-22 jo nematė, o vartotojas rado, kad koja be skylių ir užspaudžia BK12 varžtų galvas. Siūlomi AC (laukia vartotojo patvirtinimo): (1) `check_fasteners.py` priima `build/positioned/*.stl` iš bet kokio skripto, ne tik iš `parts/*.scad`, ir projekto `fasteners.json` gali įvardyti tokias dalis; (2) nauja patikra `host_face`: detalei su `mounts_on: <host>` visos host'o skylės/galvos po jos kontaktiniu plotu turi turėti jos skylę ar reliefą, kitaip FAIL; (3) fixture: koja ant plokštės su 4 varžtų galvomis be reliefų = FAIL, su reliefais = PASS; (4) mutantas `tests/mutants.tsv`.
- [x] **P21 Judesio prasukimas su deklaruotomis grupėmis** ✅ 2026-11-14: `motion_sweep.py` driver `"parts": [...]` (viena transformacija, grupės viduje poros netikrinamos), viršutinis `"static": [...]` → nepriskirta dalis = FAIL prieš prasukimą; fixture `motion_groups`, `motion_groups_unassigned_fail`, mutantas. Be `static` lieka sena elgsena su NOTE. (INC-2026-11-13-04, -05). Siūlomi AC: (1) `motion_sweep.py` skaito `motion.json` su ašimis, eiga ir **vardiniais** dalių sąrašais (ne bbox); (2) dalis `build/positioned/`, nepriskirta jokiai grupei ir be `static: true`, = FAIL (gaudo naujai pridėtą, bet nepriskirtą detalę); (3) ataskaitoje minimalus tarpas ir porų vardai per visą eigą; (4) fixture: jutiklis judančios detalės kelyje = FAIL, naujai pridėta nepriskirta dalis = FAIL; (5) mutantas.
- [x] ~~**P22 Diegimas neatsuka naujesnių dev failų**~~ PAKEISTA 2026-11-14 (G1–G3, H1–H5): GenKit gyvena tik šiame repo (`docs/genkit/`, `scad-modeler/gen/examples/`, `scripts/run_geom_mutation_monthly.sh`), `deploy_genkit.sh` ištrintas, SSD nebėra šaltinis. Diegimas tik per `install.sh` iš GitHub `origin/main` (nešvarus/nepushintas medis = atsisakoma, `--dev` apeina su WARNING); `deploy_to_canon.sh` = `install.sh --manual-only` + DSH fork; `scripts/test_install.sh` 6/6. (INC-2026-11-13-09). `deploy_genkit.sh` kopijuoja SSD GenKit → dev be patikros; 2026-11-13 jis ištrynė INC-2026-11-07-01 pataisą. Siūlomi AC: (1) prieš rsync, jei dev failas skiriasi nuo git HEAD arba HEAD versija skiriasi nuo GenKit šaltinio, kurio nėra HEAD istorijoje → STOP su failų sąrašu, nieko nekopijuota; (2) `--force` tik sąmoningam perrašymui; (3) fixture: senesnis šaltinis + naujesnis HEAD = STOP, vienodi = OK.

- [x] **P23 Surinkimo elgsena: laikosi / juda / stovi** ✅ 2026-11-18: `check_behavior.py` + `behavior.json` (kūnai = detalės IR pirktos dalys, jungtys su `max_gap` ≤ 1 mm, pozų tinklelis, tarpai, žemė + masės centras), gate `behavior`, R-24 (privaloma, kai yra `joints.json`), `check_connectivity.py` uždara ertmė = FAIL be `// EXPECTED_CAVITIES: N`. Fixture `behavior_gates` (13 atvejų), `connectivity_cavity_declared`, 2 mutantai. Pritaikyta `esp32_rc_modelis` front/rear/vehicle; rado 2 tikrus defektus (INC-2026-11-18-03 kairio rato vairas, -04 galinio variklio padėtis). Spec `docs/superpowers/specs/2026-11-18-p23-assembly-behaviour-ac.md`. (INC-2026-11-18-01, -05). Ribos: ne fizika (jėgos, trintis), laisvės laipsnių neskaičiuoja (svirtis, kabanti ant vieno kaiščio, „laikoma“).
- [ ] **P24 Surinkimo fizika: DOF, šarnyrų kampai, įvorės, apkrovos** (2026-11-18, dalinai): `check_behavior.py` KINEMATICS (Jakobiano rangas, laisvas kūnas įvardijamas, `angle` per pozą iš OpenSCAD echo), naujas `check_strength.py` + gate `strength` + R-25 (įvorių skylė Ø/gylis/sienelė pagal CNC Kitchen lentelę, sijos σ su Z sluoksnių stiprumu, Bambu TDS), validate klaidingo PASS pataisa (INC-2026-11-18-08). Fixture `kinematics_gates`, `strength_gates`, 2 mutantai. RC: įvorių skylės pataisytos (Ø4.6 → 4.2, gylis 6.7; ir splice), 55 įvorės deklaruotos (front 15, rear 24, vehicle 16), visos PASS. Liko (AC-16): front_axle_v4 joint `type`/`dof`/`angle` (tikėtinas FAIL: viršutinis rutulys 22.8°), 3 g nusileidimo `loads.json` ant svirčių. Spec `docs/superpowers/specs/2026-11-18-p24-kinematics-strength-ac.md`.
- [x] **P25 Apsaugoti dėsniai** ✅ 2026-11-18: validacijos kvitas su deklaracijų sha256 ir skill versija, stop hook blokuoja po validacijos pakeistą `*.json`; `check_limits.py` + `limits.lock` + gate `limits` + R-26 (ribą galima sugriežtinti, ne sušvelninti; ◇ riba = OPEN QUESTION); mutantai: „atmeta viską“ stub'as (3 stulpelis), 7 semantiniai mutantai su KILLED/CRASH/BASELINE_RED/NOT_APPLICABLE/SURVIVED; metamorfiniai testai (standus judesys, skerspjūviai pagal formules) rado įvorės Ø priklausomybę nuo orientacijos (INC-2026-11-18-10) ir mutantų vykdytojo spragas (-11). Liko: RC projektų `limits.lock` (vartotojo citata), Hypothesis/CrossHair, TLA+, Sigstore kvitai, mutmut (trial later). Spec `docs/superpowers/specs/2026-11-18-p25-protected-laws-ac.md`.
- [x] **P26 Geometrija, ne deklaracija** ✅ 2026-11-19 (Fable auditas): gate `contact_geometry` (deklaruotos jungtys matuojamos tinkleliais, ≤ 1 mm, tikslūs vardai), `behavior.json` privalomas 2+ dalių surinkimui ir turi apimti visas dalis, tuščias render'is = FAIL be `LIBRARY_FILE`, vieno failo connectivity, neperskaitoma deklaracija = FAIL, varžtas turi sėdėti ant medžiagos, stiprumas pjauna vieną gabalą nuo šaknies, veidrodinės `LAYOUT` kopijos (pvz. `upper_arm_l`) dabar renderinamos ir tikrinamos (AC-21; anksčiau visa kairė ašies pusė nebuvo tikrinama), `seat_external` sąsajos varžtams, motion_sweep tikslūs vardai, kvitas išlaiko `--all`, ranka rašytas kvitas ir netikra citata blokuojami, užraktas mato daugiau laukų ir savo ištrynimą. P26c (2026-11-19): `fasteners.json` `purchased` -- pirktiniai kūnai (servo ausys) renderinami į `build/purchased/` ir laikomi medžiaga varžtų patikrai (AC-22). Liko: HMAC kvitai, hook'o įrašymas į settings iš `install.sh`. Spec `docs/superpowers/specs/2026-11-19-p26-geometry-not-declaration-ac.md`.
- [x] **P27 Skaičiavimų auditas** ✅ 2026-11-19 (Fable, 15 atkurtų klaidų, 12 klaidingų PASS): įstrižas lenkimas (pilnas inercijos tenzorius), įvorės gylis bisekcija, mažėjantis `range_deg`, deklaruoti kontaktai be `min_clearance_mm`, `teeth` tik simetriškai daliai, `instances` papildo positioned, `head_h 0` kryžiavimas, varžtas be `start` ir neuždaras tinklelis = bloga įvestis, sriegis nuo 0,44 d, uždengtos skylės pagal plotą, `limits.lock` numatytosios ribos + žingsnis/intervalas/`teeth`/jėgos kryptis, `import()` cache raktas, blogiausias echo, kaištis ne skylė, vienpusė bbox tolerancija. Mutantų runner'is skaičiavo IndentationError kaip KILLED (INC-2026-11-19-09) -- pataisyta su neigiamu atveju. Spec `docs/superpowers/specs/2026-11-19-p27-calculation-audit-ac.md`.
- [x] **P27b** ✅ 2026-11-19: Fable peržiūrėjo P27 -- 3 klaidingi PASS, 3 klaidingi FAIL, lėtumas; pataisyta (lock schema 2, kontakto savas `min_clearance_mm`, viršūnių simetrija, nelyginių briaunų nesandarumas, sriegis pagal žingsnį, `offset(delta)`, uždengtos skylės 344 s -> 12 s), 12 mutantų.
- [x] **P29 Krumpliaračių ašys ir centrų atstumas** ✅ 2026-11-27: `examples/gear_reduction` buvo 3 FAIL (CI žalias, niekas jo nepaleido) ir krumpliaračiai 0,345 mm per arti (38,5 vietoj BOSL2 `gear_dist` 38,845, 11T auto profile shift), langas 0,5–2,0 mm slėpė strigtį. `motion_sweep.py` `check_gear_axes()`: tikra ašis (masės centras + simetrija, inercijos ašies pasvirimas) vs driver `origin`; `gear_mesh` su `module` → `gear_dist()` (profile_shift, helical); be `module`/`teeth` = NOT CHECKED. P29b po šviežios peržiūros (7 skylės). Fixture'ai `p29_gear_axes`, `example_gear_reduction`; suite 120/0. Liko: pavyzdžio R-26 `limits.lock` laukia vartotojo citatos; RC `steering_reduction_gearbox` jau anksčiau krenta dėl ženklų (worm/bevel deklaruoti kaip gear_mesh).
- [ ] **P28 kandidatai:** `bounded_depth` (įtariama: plona plokštė giliai bloke matuojama storiu); `$fn/$fa/$fs` į `limits.lock`; HMAC kvitai; hook'o įrašymas iš `install.sh`; antras Fable auditas (DOF/ground, joint_graph `bridge`, `hole_radius`, printability, attachment, bores, subfeature, `--all` E2E); mutantų aprėpties vartai kiekvienam checker'iui; metamorfiniai ir analitiniai etalonai; pirktinių dalių biblioteka (MG996R, Z-S0398, INJORA); šarnyro kampas iš geometrijos, ne echo. **Rasta 2026-11-20 (vehicle_v4 kėbulas):** `check_behavior.py` `echo_values` kampų `echo` leidžia tik su viršutiniu `d["scad"]`, ne su sąnario kūnų `"scad"`; surinkimas, kuris pošakį įtraukia per `use`, gauna „printed no ECHO“ FAIL (garsus, ne klaidingas PASS). Projekte apeita echo eilute vehicle `assembly.scad`. **Rasta 2026-11-20 (vartotojas):** `check_behavior.py` HOLDS priima kelių atskirų apvalkalų kūną (`balls` = 4 rutuliai) kaip vieną: „balls ↔ upright“ PASS, kai viršutinis rutulys atitrauktas 5 mm (įrodyta paleidimu). Pataisa: FAIL, kai sąnario kūno mesh turi >1 komponentą be deklaruoto `multi_shell`; neigiamas testas su 2 rutuliais, kurių vienas toli. Projekte front_axle_v4/vehicle_v4 rutuliai jau išskaidyti.

### Toliau (atvira, 2026-11-14)
- [x] **Agentų eval po P15–P21** ✅ 2026-11-14: 5/5 PASS (Sonnet subagentai, ne mokamas API), vid. 75 549 subagent tokenų, 7,4 įrankių kvietimo, 47 s → `bench/AGENT_EVAL_2026-11-01.md` skyrius „2026-11-14“. n = 1.
- [x] **Host skylių inventorius (P20b)** ✅ 2026-11-14: `check_fasteners.py` `mounts` dabar randa host skyles po dalies kontaktiniu paviršiumi, kurių nenaudoja joks deklaruotas varžtas („covers host hole at (x, y, z)“), išimtys `covered_ok`. Fixture `fasteners_mount_covers_host_hole_fail` + mutantas. Ribotumas: tikrinama viena (didžiausia) kontakto plokštuma.
- [x] **Claude Code plugin** ✅ 2026-11-14: `.claude-plugin/` (plugin + vieno plugin'o marketplace, `"source": "./"`, be `version` = commit sha). Diegimas `/plugin marketplace add Altern92/openscad-cad-skills` + `/plugin install openscad-cad-skills@openscad-cad-skills`. `incidents.py` iš plugin cache rašo į `~/.local/share/scad-modeler/INCIDENTS.local.json`. Repo `scad-modeler/SKILL.md` nebeturi `disable-model-invocation` (kanonas jį gauna per `--manual-only`). Testas `scripts/test_plugin.sh`, AC `docs/superpowers/specs/2026-11-14-claude-code-plugin-ac.md`. claude.ai ZIP atsisakyta.
- [ ] **Plugin ikona** (`.claude-plugin/icon.png`, 512–2048 px) — reikia tik jei teiksi į oficialų plugin katalogą.
- [ ] **PETG tolerancijos** (§4.2) — tik išmatavus: išspausdinti `calibration_coupon()` (`openscad-cad/references/patterns.scad`, Pattern 5) PETG, pamatuoti, įrašyti į `openscad-cad/references/tolerances.md` § PETG pagal formatą (printeris, medžiaga, sluoksnis, ėminys, measured vs reported). Vartotojo darbas.
- [ ] **Exit kodų suvienodinimas** (§4.1) — 2026-11-14 sąmoningai nedaryta: `validate_scad.sh` ir fixture'ai remiasi esamais kodais, vartotojui nauda nulinė, rizika sulaužyti skriptus. Daryti tik kartu su `check_*.py` v2.

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

> **2026-09-12 papildymas: ketvirtas kelias — idiomų korpuso kasyba — ATMESTAS.** Recenzentas
> su arXiv/ACL prieiga rado: (1) jokio šaltinio, kuris pagrįstų teiginį, kad korpusas duoda
> geresnį kodą; (2) korpuso dydžio slenksčio **nėra**, o BENEVOL 2025 rodo, kad išgauti patternai
> negeneralizuojasi; (3) mūsų pačių keturių repozitorijų korpuse ieškoto patterno
> `jazwa/rackstack` neturi nė vieno atvejo; (4) **pavyzdžiai sotėja ties ~6**, o blogi
> pavyzdžiai **pablogina**. Likę trys keliai lentelėje lieka galioti.
>
> Taip pat: **vykdomi patikrinimai yra vienintelė išmatuota svirtis** (59 % teisingumo ir 89 %
> saugumo problemų ištaisoma gavus pranešimą). Detailai: `_wiki/scad/05_agentu_testai.md`.

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
   turi parašyti tas, kas žino, kur varžtas.
   **Generatoriaus NEBUS:** deklaracija išreiškia **ketinimą** („ši skylė turi būti praeinama"),
   o iš geometrijos galima sugeneruoti tik **spėjimą**. Sugeneruota deklaracija duotų klaidingą
   pasitikėjimą arba klaidingus FAIL'us. Sprendimas: palikti žmogui.
   **2026-09-12 patikrinta:** ant projekto, sukurto **su skill'u**, 5 iš 6 „niekada neįsijungiančių"
   taisyklių suveikia **PASS** (R-01, R-02, R-06, R-11, R-12). Ankstesnis radinys buvo matuotas
   neteisingame korpuse — 11 senų projektų. Žr. `_wiki/scad/06_zurnalas.md` klaidą E.
2. **`assembly.scad` MODE sutartis** (2026-11-14 patikrinta: `MODE = 1;` liko tik `server_rack_modular_v4/scad` ir `v4/v5/scad`, kuriuos pakeitė v6–v8; senų versijų netaisome, naujuose projektuose `templates/assembly.scad` jau apsaugotas) — 4-5 projektuose `MODE = 1;` vietoj
   apsaugoto. Šablonas `templates/assembly.scad` dabar yra. Kol nesutvarkyta,
   `collisions` ten nepasileidžia (teisingai — tripwire pagauna).
3. **bbox tolerancija** (2026-11-14 išplėsta: `scad_tessellation.py` saugiai (ast allow-list) sprendžia `d=`, pozicinį r, aritmetiką, include skaliarus, sferos `$fn/$fa/$fs`; modulio parametrai, funkcijos, `use<>` lieka praleidžiami; fixture `minkowski_radius_forms`; 48 realūs failai – tie patys deficitai) — `minkowski` narys pridėtas, bet sprendžiami tik
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

# ar testai žali? (turetų buti 45 passed)
bash scad-modeler/tests/run_all.sh

# ar irankiai tikrai pranesa visas patikras? (turetų buti 198 pries 89)
bash /tmp/ab.sh && python3 /tmp/ab_analyze.py

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

**2026-09-12 papildymas — kūno augimas deterministiškai** (žr. `golden_scad/KOSTAI_2026-09-12.md`):

| | Pradžia | Dabar | Δ |
|---|---:|---:|---:|
| **Agentui matoma** (SKILL.md + references) | — | — | **~+2 550 tok (~+5 %/žingsnis)** |
| `INCIDENTS.md` | 88 647 B | 142 661 B | +54 014 B (**agentui nepasiekiamas**) |
| Viso | 190 874 B | 253 432 B | +62 558 B (+32,8 %) |

**Skaidymas svarbus:** `INCIDENTS.md` sudaro 13 085 iš 15 639 pridėtų tokenų — ir jis agento
**nepasiekiamas** (runtime nuotėkis į `~/.dsh/skills/` pašalintas). Tad realus augimas ~**+5 %**
konteksto per žingsnį. Ankstesnis **+68 % cacheRead** augimas atėjo **ne nuo failų dydžio**, o nuo
to, kad agentai **skaitė daugiau failų** — ir tą turi matuoti evalas, ne failų sąrašas.
