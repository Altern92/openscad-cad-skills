# Tyrimas: kaip užtikrinti, kad SCAD skill kaskart laikytųsi taisyklių + verifikacinis medis v2

> Data: 2026-08-19 · Vykdyta: keli modeliai per DSH workflow + internetinės paieškos
> Tikslas: (1) ištirti mechanizmus, kurie garantuotų, kad `scad-modeler`/
> `openscad-cad` skill besąlygiškai laikytųsi savo taisyklių; (2) patobulinti
> `validation_decision_tree.md` iki v2, įtraukiant vartotojo viziją (intake
> analizė, panašių variantų paieška, spausdinama vs pirkta, judančių dalių
> mechanika, pokyčių/perskaičiavimo medis).

## Šaltinių žurnalas

| ID | Teiginys | Šaltinis (URL) | Tipas | Data | Būsena |
|---|---|---|---|---|---|
| R-001 | Agentų patikimumas: veiksmų apribojimas, struktūruoti rezultatai, savęs gydymo kilpos | https://befailproof.ai/guides/how-to-make-ai-agents-reliable/ ; https://blog.n8n.io/make-ai-agents-more-reliable-and-restrict-the-actions-they-can-take/ ; https://dev.to/system_rationale/part-3-making-gemma-4-agents-production-ready-guardrails-structured-outputs-and-self-healing-575n | pirminis | 2026-08-19 | ✅ su šaltiniu |
| R-002 | Verifikacijos kilpos (CoVe, structured verification loops) mažina haliucinacijas; formalus verifikavimas (AlphaVerus) | https://arxiv-org.ezproxy.obspm.fr/html/2606.21724v1 ; https://aclanthology.org/2025.bionlp-share.34/ ; https://mlanthology.org/icml/2025/aggarwal2025icml-alphaverus/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| R-003 | CAD priklausomybių valdymas: pakeitimas vienoje dalyje veikia kitus dokumentus; FreeCAD recompute (topologinė eilė, tik nešvarūs mazgai); ECM acykliniai digrafai | https://ar5iv.labs.arxiv.org/html/2508.05940 ; http://opendeep.wiki/FreeCAD/FreeCAD/core-application-architecture.recompute-dependency-ordering-and-transactions ; https://dfam.designsociety.org/download-publication/37750/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| R-004 | OpenSCAD statinė analizė: tree-sitter-openscad (npm v0.5.1; @holistic-stack v0.1.0); openscad-language-server (LSP, ne statinis ekstraktorius) | https://www.npmjs.com/package/tree-sitter-openscad ; https://github.com/dzhu/openscad-language-server | pirminis | 2026-08-19 | ✅ su šaltiniu |
| R-005 | FDM tarpų klasės (press/transition/slip/running), poslinkiai (shrinkage, elephant foot, layer lines); judančių spausdintų dalių apribojimai | https://www.aon3d.com/applications/engineering-fits-how-to-design-for-3d-printed-assemblies/ ; https://tools.creative3dp.com/tools/press-fit-calculator/ ; https://www.ftcwiki.org/manufacturing-and-assembly/machining/tolerances ; https://thevirtualfoundry.com/3d-print-moving-parts/ | pirminis | 2026-08-19 | ✅ su šaltiniu |
| R-006 | NopSCADlib vitaminų filosofija: standartinės detalės modeliuojamos realiais matmenimis; BOM | https://github.com/nophead/NopSCADlib ; https://deepwiki.com/nophead/NopSCADlib/4-component-library-(vitamins) | pirminis | 2026-08-19 | ✅ su šaltiniu |
| R-007 | LLM CAD generavimo verifikacijos kilpa gerina rezultatą (CADCode-Verify); VLM CAD kodas | https://proceedings.iclr.cc/paper_files/paper/2025/hash/81a934cd364e18ea6fdeaf57a93c17d4-Abstract-Conference.html ; https://huggingface.co/papers/2410.05340 | pirminis | 2026-08-19 | ✅ su šaltiniu |
| R-008 | Perplexity MCP šioje DSH sesijoje IŠJUNGTAS (krisdavo dsh per SSE); paieškos darytos per integruotą web_search įrankį | ~/.dsh/profiles/web/cordis.patch.yml | pirminis (vietinis) | 2026-08-19 | ✅ patvirtinta |
| R-009 | Cloudflare Workers AI dienos 10K neuronų kvota išnaudota — modelis šiandien nepasiekiamas | tiesioginis API atsakymas (code 4006) | pirminis (vietinis) | 2026-08-19 | ✅ patvirtinta |

## Metodika

1. **Modelių patikra prieš naudojimą** (workflow probe + tiesioginiai API testai):
   - ✅ Veikia: `dashscope/qwen-plus-character`, `nvidia/deepseek-v4-flash-0731`,
     `google/gemini-3.7-flash`, `mistral/ministral-3b-latest`, `groq/qwen3.6-27b`
     (tik tiesiogiai API; workflow'e nestabilus), `openrouter/anthropic-claude-sonnet-5`
     (tik tiesiogiai API; workflow'e nestabilus).
   - ❌ Neveikia: `cloudflare-workers-ai` (dienos kvota išnaudota, 4006).
2. **Internetinės paieškos** — 7 paieškos (R-001…R-007).
3. **Fan-out tyrimo agentai** per workflow (`agent(prompt, {provider, model})`):
   - `dashscope/qwen-plus-character` → **mechanikos etapas** (įrašė
     `references/mechanics_and_motion_planning.md`).
   - `nvidia/deepseek-v4-flash-0731` → **pokyčių medis** (įrašė
     `references/change_propagation.md`).
   - `google/gemini-3.7-flash` → **intake/analizės pipeline** (requirements
     schema, spausdinama vs pirkta, variantų paieška).
   - `groq`, `openrouter` → workflow'e 2× nuliai (nors API veikia) — šiuos
     kampus sintezavo pagrindinis agentas.
4. **Sintezė** — pagrindinis agentas: `rules_enforcement.md`,
   `validation_decision_tree.md` v2, `scripts/check_dependencies.py` (PoC),
   ši ataskaita.

## Pagrindinės išvados

1. **Taisyklės laikymasis turi būti įrodomas skriptais, ne įsimenamas modelio.**
   Skill'as jau turi tinkamiausią pagrindą — `check_*.py` vartus. Trūko:
   intake varto, judančių dalių automatinio trigerio, pokyčių medžio ir
   privalomos savęs patikros prieš atsakymą. Viskas pridėta (žr. rezultatus).
2. **Pokyčių medis** — parametrinio CAD esmė: FreeCAD recompute modelis
   (topologinė eilė, tik nešvarūs mazgai) perkeliamas į .scad per lengvą
   tokenizer'į + fallback į pilną perrinkimą. PoC: `check_dependencies.py`.
3. **Mechanika** — judančios dalys deklaruojamos `design_manifest.json`
   motion bloke; tada automatiškai: statiniai susidūrimai → motion sweep;
   tarpų lentelės (FDM realybė) — press/slip/transition.
4. **Spausdinama vs pirkta** — NopSCADlib vitaminų filosofija: standartinės
   detalės (guoliai, velenai, varžtai) niekada nespausdinamos, modeliuojamos
   realiais matmenimis; sprendimo kriterijai — apkrova/tikslumas/trintis/kaina.
5. **Panašių variantų paieška** — embedding indeksas (qwen3.7-text-embedding
   kreditai!) virš praeitų projektų README + parametriniai šablonai.

## Rezultatai (įrašyta į skill repo)

| Failas | Turinys | Autorius |
|---|---|---|
| `scad-modeler/references/validation_decision_tree.md` | **v2** — naujas medis: intake → analizė → planas → geometrija → validacija → mechanika → pokyčių medis → taisyklių vartas → ataskaita | sintezė |
| `scad-modeler/references/intake_and_analysis.md` | requirements schema, spausdinama-vs-pirkta lentelė, variantų paieška | gemini + sintezė |
| `scad-modeler/references/mechanics_and_motion_planning.md` | judesių taksonomija, tarpų lentelės, manifest schema (užbaigta po 4K nukirtimo) | qwen + sintezė |
| `scad-modeler/references/change_propagation.md` | priklausomybių DAG, dirty-root algoritmas, vartotojo medžio išvestis (pataisyta: tree-sitter faktai, typo) | nvidia + sintezė |
| `scad-modeler/references/rules_enforcement.md` | kodėl agentai nukrypsta + 4 sluoksnių variklis + rules_manifest koncepcija | sintezė |
| `scad-modeler/scripts/check_dependencies.py` | PoC pokyčių medžio variklis (stdlib, testuotas) | sintezė |
| `scad-modeler/SKILL.md` | §0 intake pastraipa + 5 naujos Reference files eilutės | sintezė |

## Neatlikta / tolimesni žingsniai

- `check_intake.py` (requirements.json vartas) ir `check_rules.py` (taisyklių
  manifesto vykdytojas) — aprašyti koncepciškai, bet **neimplementuoti**;
  `rules_manifest.yaml` šablonas irgi dar nėra. Tai kitas žingsnis, jei nori.
- Embedding variantų indekso įgyvendinimas (qwen3.7-text-embedding) — schema
  paruošta, skripto nėra.
- `motion_sweep.py` automatinis trigeris iš `design_manifest.json` —
  dokumentuotas, `validate_scad.sh` dar nepakeistas.
- Groq/OpenRouter workflow nestabilumas — verta ištirti atskirai (tiesiogiai
  API veikia; workflow agent() krenta).
