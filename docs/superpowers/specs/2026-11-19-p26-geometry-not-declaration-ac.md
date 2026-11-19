# P26 Geometrija, ne deklaracija (AC, 2026-11-19)

Kilmė: nepriklausomas Fable auditas 2026-11-19 (bandymai `scratchpad/fable_audit/e1..e10`).
Gytis 2026-11-19: „sudeliok visus taisymo zingsnius i ac ir pradek taisyma!“.
Pagrindinė klaida: „sujungta“ ir „laikoma“ įrodoma deklaracija ir tašku dalies viduje, ne tinkleliais.
Dalis, pakibusi 110 mm ore, gauna rc=0 (patvirtinta pakartotinai, e8).

Tier: feature. Keičiami `validate_scad.sh`, `check_joint_graph.py`, `check_behavior.py`, `check_collisions.py`,
`check_fasteners.py`, `check_strength.py`, `check_limits.py`, `check_dimensions.py`, `check_topology.py`,
`check_rules.py`, `hooks/scad_stop_gate.py`, `install.sh`. Kiekvienas AC turi fixture'ą, kuris krenta senu kodu.

## AC

**Geometrija (svarbiausia)**
- AC-1 (#1): Given `joints.json` kontaktas ar `attachments.json` pora `part`→`to`, when `--all` turi pozicionuotus
  STL, then naujas vartas `contact_geometry` matuoja tikrą mažiausią atstumą tarp tinklelių; > 1.0 mm = FAIL
  „`a` and `b` are declared joined but are N mm apart“. Deklaruotas vardas be STL = FAIL. Neigiamas: besiliečiančios
  dalys PASS.
- AC-2 (#2): Given 2+ spausdinamos dalys ir `assembly.scad`, then `behavior.json` nebuvimas = `behavior=FAIL`;
  given `behavior.json`, then kiekviena spausdinama dalis turi būti kurio nors kūno `render` (PART), kitaip FAIL
  „part `x` is in no body“. Neigiamas: pilnas sąrašas PASS.
- AC-3 (#12): kontakto ir prisirišimo vardai lyginami tiksliai su dalies vardu (ne fragmentu), `check_joint_graph.py`
  ir `check_collisions.py`. Neigiamas: `["s","l"]` nebeatitinka `shelf`/`base`.
- AC-4 (#13): MODE/PART tripwire suveikia tik kai 2+ dalys turi surinkimo gabaritus. Viena dėžė, kurios gabaritai
  lygūs surinkimui, nebe FAIL. Neigiamas: visos dalys = surinkimas -> vis dar FAIL.
- AC-5 (#10): Given dalis, kuri nieko neatvaizduoja (tuščias top-level), then `render=FAIL`
  („renders nothing“). Bibliotekos failas `parts/` aplanke žymimas `// LIBRARY_FILE: <reason>`.
- AC-6 (#9): vieno failo režimas tikrai paleidžia connectivity; dvi atskiros dėžės = FAIL.
- AC-7 (#11): varžtas: galvos atrama ir kotas turi kirsti medžiagą (bent viena pozicionuota dalis aplink
  kotą). Varžtas tuščioje erdvėje = FAIL.
- AC-8 (#8): stiprumas: pjūvyje imamas tik daugiakampis, kurį kerta atramos-apkrovos linija (ar artimiausias jai);
  stotys apima galus (0–100 %, 0.2 mm įtrauka). Neigiamas: strypas su nepakrauta gretima atšaka FAIL kaip ir be jos;
  strypas, nepasiekiantis atramos, FAIL.
- AC-9 (#14): `check_strength.py` priima `fasteners.json` sąrašo formą (nebelūžta).

- AC-21 (rasta pervalidinant RC galinę ašį): kiekviena `LAYOUT` eilutė (ir kopija, naudojanti tą patį dalies failą,
  pvz. `axle_tube_l`) gauna pozicionuotą STL. Neigiamas: kopija, įlindusi į pagrindą, = collisions FAIL; kopija su
  1 mm tarpu = PASS (`layout_instances`).
- AC-3b: tikslūs vardai ir `motion_sweep.py` (`static`, driver), `check_strength.py` (`insert_in`, `part`),
  `check_fasteners.py` (`into`, `mounts`), `check_bore_reachability.py`: `peg` nebeatitinka `peg_l`, `bloc` nebe `block`.
- AC-7b: `fasteners.json` `"seat_external": "<priežastis>"` atleidžia tik nuo galvos atramos (kito modulio plokštė);
  tuščia priežastis = FAIL; kotas tuščioje erdvėje vis tiek FAIL.

**Kvitas ir hook'as**
- AC-10 (#3): vienos dalies validacija išsaugo ankstesnio kvito `mode` (`--all`), `declarations` ir `skill`.
  Neigiamas: `--all`, pakeistas `loads.json`, `validate_scad.sh a` -> hook vis dar blokuoja.
- AC-11 (#4): `limits.lock` / `acceptance.lock`, sukurti ar pakeisti per sesiją (bet kuriuo būdu: Write, `cd && approve`,
  tęsinio eilutė), tikrinami pagal failą, ne pagal komandą. Citata turi būti visa žmogaus žinutė arba visa jos eilutė
  (≥ 8 simboliai); sistemos priminimai, skill tekstai ir santraukos nėra žmogaus žinutės. `--quote "a"` = blokuoja.
- AC-12 (#5): hook'as blokuoja, kai sesija ranka rašė `build/.validation_state.json`. `install.sh` įspėja, jei hook'as
  neregistruotas; dokumentai sako „kai hook'as registruotas“.

**Ribų užraktas**
- AC-13 (#6): žymių regex bendras vartams ir užraktui (`PREVIEW_FILE` su dvitaškiu ar be);
  inventoriuje yra `EXPECTED_BODIES` (daugiau = švelniau), `loads.json` `reach` (daugiau = švelniau) ir
  pakeitimui jautrūs `material`, `print_up`, `support`, `at`. Kvitas žymi, kad užraktas buvo; jo nebuvimas po to = FAIL.
- AC-14 (#15): užraktas fiksuoja `motion[].min_clearance_mm` (tai skaito `motion_sweep.py`);
  `EXPECTED_BBOX_TOL` padidinimas nebėra „loosened“ (tolerancija tik griežtinanti).

**Deklaracijų skaitymas**
- AC-15 (#7): Given deklaracijos eilutė yra, bet neperskaitoma (`EXPECTED_BBOX: [L, W, H]`,
  `EXPECTED_THROUGH_HOLES: none`, blogas `EXPECTED_HOLE`), then checkeris grąžina FAIL, ne „skipping“.

**Smulkūs (#15)**
- AC-16: `ground.at` / DOF poza parenkama pagal poaibį, kaip `ground.at`.
- AC-17: `build/positioned/` išvalomas prieš pozicionuotą render'į.
- AC-18: `check_rules.py` sėkmės šablonas tikrinamas tik `CHECK_RESULT` eilutėse eilutės pradžioje.
- AC-19: `printability_overhang_fail` ir `bore_reachability_sealed_fail` fixture'ai tikrina priežasties tekstą.

**Laidai**
- AC-20: SKILL.md, validation.md, design_constraints, NEXT.md P26, INCIDENTS. Visas suite žalias dev ir kanone; RC
  projektai pervalidinti įdiegtu skill'u, rezultatai pranešti (nauji FAIL taisomi modelyje arba pranešami).

Ne apimtyje: HMAC kvitų parašas (AC-12 gaudo rankinį rašymą įrankiais), hook'o įrašymas į vartotojo
`settings.json` iš `install.sh` (tik įspėjimas).
