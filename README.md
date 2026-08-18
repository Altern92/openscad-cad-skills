# claude_skills

„Claude Code" skills rinkinys parametriniam OpenSCAD projektavimui — nuo vienos
detalės iki daugiadalio mechaninio mazgo, su automatiniu geometrijos
patikrinimu prieš eksportą.

## Skills

| Skill | Kam |
|-------|-----|
| `openscad-cad` | Viena detalė: įdėklas, laikiklis, dangtis, korpusas, Gridfinity dėžutė. Rašymas, renderis, eksportas, matmenų tikrinimas. |
| `scad-modeler` | Daugiadaliai mazgai: krumpliaračiai, guoliai, velenai. Prideda privalomus skaičiavimus prieš geometriją, centralizuotus parametrus ir pozicijas, kolizijų bei tarpų tikrinimą. |

`scad-modeler` remiasi `openscad-cad` — renderio/eksporto komandos ir tolerancijų
duomenys gyvena ten. Vienai detalei naudok `openscad-cad` tiesiogiai; jo
validacijos skriptai yra `scad-modeler/scripts/`, bet veikia ir su viena detale.

## Instaliacija

```bash
ln -s "$PWD/openscad-cad"  ~/.claude/skills/openscad-cad
ln -s "$PWD/scad-modeler"  ~/.claude/skills/scad-modeler
```

Abu verta įdiegti kartu: `openscad-cad` nurodo `scad-modeler` skriptus, o tie
savo ruožtu naudoja `openscad-cad/references/patterns.scad`.

### Priklausomybės

OpenSCAD (macOS: `brew install --cask openscad@snapshot` — ne paprastas
`openscad` cask, jis per senas), headless Linux dar `xvfb`.

Python patikrinimams:

```bash
pip install -r requirements.txt
```

Ne visi būtini: `trimesh` reikalingas viskam, `shapely` — gręžinių matavimui,
`python-fcl` + `scipy` — kolizijoms, `manifold3d` — deklaruotų priveržimų
matavimui. Ko trūksta, tas patikrinimas tiesiog nepasiekiamas, ir įrankiai tai
pasako.

## Patikrinimas prieš naudojant

```bash
python3 scad-modeler/scripts/doctor.py      # ką ši mašina apskritai gali
python3 scad-modeler/scripts/selftest.py    # ar visa grandinė realiai veikia
```

`doctor.py` aptinka OpenSCAD, bibliotekas (pagal jų įėjimo failą, ne pagal
aplanko vardą), Python paketus ir kalibracijos profilį, ir pasako aukščiausią
pasiekiamą pasitikėjimo lygį.

`selftest.py` sukuria detalę su iš anksto žinomais atsakymais, paleidžia visą
grandinę ir tikrina, ar kiekvienas įrankis prieina teisingą verdiktą — įskaitant
tai, kad gręžinio patikra **privalo kristi** ant nekompensuoto gręžinio.
Patikrinimas, kuris niekada nekrenta, nieko neįrodo.

## Ką šie skills tikrina

| Įrankis | Ką pagauna |
|---|---|
| `assert()` faile `params.scad` | konstrukcijos invariantus — sustabdo renderį |
| `check_dimensions.py` | išorinį gabaritą prieš deklaruotą `EXPECTED_BBOX` |
| `check_features.py` | gręžinio matmenį per briaunas — tai, į ką atsiremia velenas |
| `check_collisions.py` | netyčinę interferenciją, per mažą tarpą, deklaruotus priveržimus |
| `motion_sweep.py` | kirtimusi ir tarpus **per visą judesio ciklą**, ne vienoje pozoje |

Gabaritų tolerancija išvedama iš `$fa`/`$fs`, ne fiksuota. Kodėl tai svarbu ir
kodėl gabaritas nemato per siauro gręžinio — `openscad-cad/references/tolerances.md`.

## Ribos

Pasitikėjimo lygiai aprašyti `openscad-cad/references/confidence-tiers.md`.
Skills siekia **Tier 5** — judesiu patikrinto mazgo.

Judesio tikrinimas yra **mėginiavimas, ne įrodymas**: tarp dviejų mėginių
niekas netikrinama. Adaptyvus tankinimas pagauna siaurus kirtimusis prie
minimumo, bet siauras ir toli nuo minimumo esantis gali prasprūsti. Deklaruok
žingsnį, kai remiesi rezultatu.

Visiškai neįgyvendinta:

- **surinkimo sekos tikrinimas** — mechanizmas gali praeiti Tier 5 ir vis tiek
  būti nesurenkamas;
- **apkrovos skaičiavimai** — be medžiagos duomenų tai būtų aritmetika,
  apsimetanti inžinerija;
- **slicer printability vartai** — nė vienas iš trijų slicerių nedokumentuoja
  thin-wall / non-manifold įspėjimų kaip pasiekiamų per CLI.

Tier 3 ir aukščiau reikalauja kalibracijos profilio: išmatuoti tavo printerio ir
medžiagos nuokrypiai. Be jo galima pažadėti geometriją, bet ne suderinimą.

## `research/`

Tyrimo promptai ir jų kontekstas — kaip prieita prie sprendimų. Ne skill'o
dalis, į `~/.claude/skills/` nediegiama.
