// kit/lib.scad — bendri pagalbiniai (P1, AC-05).
//
// Skylų lentelė yra VIENINTELIS šaltinis: generatorius (gen/emit_part.py)
// jos NEDUBLIUOJA — jis perduoda tik žymėjimą ("M4"), o skersmenį išsprendžia
// kit_hole_d(). Keisti lentelę draudžiama be sprendimo įrašo
// (docs/03_moduliu_api.md §Skylų lentelė).
//
// Šis failas geometrijos nekuria — tik funkcijas ir pagalbinius modulius.

// --- Skylų lentelė (ISO 273 medium clearance) -------------------------------

function kit_hole_lookup(hole) =
    hole == "M3" ? 3.4
  : hole == "M4" ? 4.5
  : hole == "M5" ? 5.5
  : hole == "M6" ? 6.6
  : -1;

// Grąžina skylės skersmenį mm: žymėjimas → lentelė, skaičius → kaip yra,
// nežinomas žymėjimas → -1 (modulis tada `assert`ina).
function kit_hole_d(hole) =
    is_string(hole) ? kit_hole_lookup(hole) : hole;

function kit_min2(a, b) = a < b ? a : b;
function kit_max2(a, b) = a > b ? a : b;

// Skaičius pranešimams: 1–2 skaitmenys po kablelio (docs/05 §Formatas).
// 1 -> "1.0", 1.2 -> "1.2", 1.75 -> "1.75".
function kit_fmt(x) =
    let (s = str(round(x * 100) / 100),
         dot = search(".", s))
    dot == [] ? str(s, ".0") : s;

// --- Geometrijos pagalbiniai (be „stebuklingų" skaičių) ---------------------

// Apvalintas 2D stačiakampis, centruotas (0,0). r = 0 → aštrūs kampai.
module kit_round2d(w, d, r = 0) {
    if (r > 0) {
        hull()
            for (x = [-1, 1], y = [-1, 1])
                translate([x * (w / 2 - r), y * (d / 2 - r)])
                    circle(r = r, $fn = 64);
    } else {
        square([w, d], center = true);
    }
}

// Apvalintas blokas: apatinis paviršius z = 0, centras (0,0).
module kit_round_block(w, d, h, r = 0) {
    linear_extrude(height = h, convexity = 4)
        kit_round2d(w, d, r);
}

// 4 kampų skylių centrai (inset — nuo krašto iki skylės centro).
function kit_corner_points(w, d, inset) =
    [ [ w / 2 - inset,  d / 2 - inset],
      [-w / 2 + inset,  d / 2 - inset],
      [-w / 2 + inset, -d / 2 + inset],
      [ w / 2 - inset, -d / 2 + inset] ];
