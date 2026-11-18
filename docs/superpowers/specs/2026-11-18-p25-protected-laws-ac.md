# P25 Apsaugoti dėsniai: vartų neapeisi, ribų nesušvelninsi (AC, 2026-11-18)

Kilmė: vartotojas 2026-11-18 („šiuos principus pritaikytum scad skill“) po agent-bus tyrimo
„Making agent-bus safer with machine-checked laws“. Tas pats defektas, kurį tyrimas randa agent-bus
(`record(changes=...)` apeina `check_transition`), scad-modeler'yje yra štai toks:

- Stop hook'as saugo tik `.scad` failus. Pakeitus `behavior.json`, `loads.json`, `fasteners.json` ar
  `joints.json` po validacijos, niekas to nepastebi.
- Ribas (`max_gap`, `max_deg`, `clearance.min`, `expected_interference_mm`, `safety`,
  `EXPECTED_BBOX_TOL`) ir išimtis (`NO_JOINT`, `NO_RETENTION`, `MARGIN_EXCLUDES_OK`, `PREVIEW_FILE`)
  rašo tas pats agentas, kurį vartai tikrina. Taisyklė „niekada nesušvelnink ribos“ yra tik tekstas.
  2026-11-18 pavyzdys: rutulio kampo ribą 15° pasirinko agentas, o `params.scad` turi 25°.
  Vienu skaičiumi galima paversti FAIL į PASS.
- Mutantas tikrina tik `exit 0` stub'ą (ar fixture krenta, kai checkeris tyli). Jis nepatikrina, ar
  checkeris, kuris viską atmeta, būtų pagautas, ir ar fixture'as pagauna prasmingą logikos klaidą.

Tyrimas (2026-11-18): read-only testai ir hook'ai mažina agentų „reward hacking“, bet jo nepanaikina.
Struktūruotas eskalavimo kanalas sumažino jį nuo 23,6 % iki 5,3 % (arXiv 2608.29460, vienas preprintas ◇).
Mutantas užskaitomas tik tada, kai jį nužudo elgsenos assertion, o ne importo ar paleidimo klaida
(Stryker / PIT taksonomija). CAD ir mesh įrankiams invariantų ir metamorfinis testavimas yra pripažintas
metodas (arXiv 2509.00699; Chan, Ho, Tse, HKU TR-2007-04).

Tier: feature. Plečiami `validate_scad.sh` (kvitas), `hooks/scad_stop_gate.py`, naujas `check_limits.py`
(ribų užraktas; atskiras checkeris, kad jį dengtų mutantų taisyklė), `tests/mutants.tsv` + `mutant_coverage`; nauji fixture'ai. Naujų priklausomybių nėra
(Hypothesis neįdiegtas, metamorfiniai testai rašomi su numpy ir fiksuota sėkla).

## AC

**Kvitas (run receipt)**
- AC-1: Given `validate_scad.sh --all` baigė darbą, then `build/.validation_state.json` turi
  `declarations`: sha256 kiekvienam projekto šaknies deklaracijos failui (`*.json`, išskyrus `build/`)
  ir `skill`: įdiegto skill'o versija (git SHA iš install žymės arba `dev`).
- AC-2: Given deklaracijos failas pakeistas po paskutinio `--all`, when sesija baigiama, then stop
  hook'as blokuoja su pranešimu „`<failas>` changed after validate“, kaip ir `.scad` atveju.
  Neigiamas atvejis: nepakeistas failas neblokuoja.

**Ribų užraktas (limits.lock)**
- AC-3: Given `check_limits.py approve --quote "<vartotojo žodžiai>"`, then `limits.lock` užfiksuoja
  kiekvieną leidžiančią ribą ir išimtį su keliu (failas → raktas), reikšme ir citata.
- AC-4: Given užfiksuota riba sušvelninta (pvz. `max_deg` 15 → 25, `max_gap` 0.3 → 0.8,
  `clearance.min` 0.5 → 0.2, `safety` 2 → 1.5, nauja `NO_*` išimtis), when vyksta validacija, then
  `CHECK_RESULT limits=FAIL` su sąrašu „`<kelias>`: 15 → 25 (loosened, approved 15 by "<quote>")“.
  Sugriežtinta riba praeina (PASS su NOTE).
- AC-5: Given `limits.lock` nėra, then vartai `limits` nurodo SKIP ir parodo, kiek ribų neužfiksuota.
  Taisyklė R-26 jų reikalauja, kai yra `behavior.json` arba `loads.json`.
- AC-6: Given riba be šaltinio pažymėta „estimate“ ar „◇“, then ataskaitoje ji nurodoma kaip
  OPEN QUESTION (eskalavimo kanalas): klausimas vartotojui, ne leidimas keisti ribą.

**Abipusiai mutantai (positive + negative witness)**
- AC-7: `tests/mutants.tsv` turi trečią stulpelį: PASS fixture'ą. Given checkeris pakeistas stub'u, kuris
  visada grąžina FAIL (exit 3), then tas fixture'as krenta („viską atmetantis checkeris“ pagaunamas).
- AC-8: Semantiniai mutantai (naujas `tests/semantic_mutants.tsv`: checkeris, tikslus kodo fragmentas,
  pakeitimas, fixture'as, laukiamas tekstas). Iš pradžių bent 6: strength (sienelė, gylis, Z stiprumas),
  behavior (kampas, DOF), fasteners (įsukimas). Given fragmentas nerastas, then FAIL „mutant not
  applicable“. Given mutuotas checkeris nulūžta su Traceback, then FAIL „killed by crash, not by
  assertion“. Given fixture'as praeina su mutantu, then FAIL „survived“.

**Metamorfiniai testai (invariance)**
- AC-9: Given `strength_gates` ir `fasteners_pass` fixture'ai, when visa geometrija ir deklaracijų
  koordinatės pastumiamos ir pasukamos (3 fiksuotos sėklos), then kiekvieno atvejo verdiktas ir
  išmatuoti skaičiai sutampa (±0.05 mm, ±1 %). Neigiamas atvejis: transformavus tik geometriją be
  deklaracijų, verdiktas pasikeičia (testas gali kristi).
- AC-10: Given stačiakampio ir apskrito skerspjūvio sijos su atsitiktiniais matmenimis (fiksuota sėkla,
  20 atvejų), then `section_props` I ir σ sutampa su uždara formule (bh³/12, πd⁴/64) ±2 %.

**Dokumentai ir laidai**
- AC-11: SKILL.md §7 gauna eilutę: „riba yra vartotojo sprendimas: keičiama tik per
  `check_limits.py approve`; gate'ui kritus dėl ◇ ribos, užrašyk OPEN QUESTION“. `references/validation.md`
  skyrius „Protected limits“. `design_constraints.md` ir NEXT.md P25.
- AC-12: Visas suite žalias dev ir įdiegtoje kopijoje. RC projektai (front, rear, vehicle,
  calibration) gauna `limits.lock` tik po vartotojo citatos; iki tol `limits=SKIP` ir apie tai
  pranešama.

Ne apimtyje: Hypothesis/CrossHair priklausomybės, formalūs modeliai (TLA+), kvitų parašai (Sigstore),
viso kodo mutacijų įrankiai (mutmut). Jie lieka NEXT.md kaip „trial later“.

## Įgyvendinimo nukrypimai
- Ribų užraktas yra atskiras `check_limits.py`, ne `acceptance.py` poskomandis (mutant_coverage reikalauja fixture'o kiekvienam check_*.py).
- Viskas vienu commit'u: `mutants.tsv` ir stop hook'as keičiami keliuose žingsniuose, atskiri commit'ai būtų nežali.
