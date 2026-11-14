// kit/lib.scad — shared helpers (P1, AC-05).
//
// The hole table is the ONLY source: the generator (gen/emit_part.py) does
// NOT duplicate it — it passes only the designation ("M4"), and kit_hole_d()
// resolves the diameter. Changing the table requires a decision record
// (docs/03_module_api.md §Hole table).
//
// This file creates no geometry — only functions and helper modules.

// --- Hole table (ISO 273 medium clearance) ----------------------------------

function kit_hole_lookup(hole) =
    hole == "M3" ? 3.4
  : hole == "M4" ? 4.5
  : hole == "M5" ? 5.5
  : hole == "M6" ? 6.6
  : -1;

// Returns the hole diameter in mm: designation → table, number → as is,
// unknown designation → -1 (the module then `assert`s).
function kit_hole_d(hole) =
    is_string(hole) ? kit_hole_lookup(hole) : hole;

function kit_min2(a, b) = a < b ? a : b;
function kit_max2(a, b) = a > b ? a : b;

// Number for messages: 1–2 decimal places (docs/05 §Format).
// 1 -> "1.0", 1.2 -> "1.2", 1.75 -> "1.75".
function kit_fmt(x) =
    let (s = str(round(x * 100) / 100),
         dot = search(".", s))
    dot == [] ? str(s, ".0") : s;

// --- Geometry helpers (no "magic" numbers) ----------------------------------

// Rounded 2D rectangle, centred on (0,0). r = 0 → sharp corners.
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

// Rounded block: bottom face z = 0, centre (0,0).
module kit_round_block(w, d, h, r = 0) {
    linear_extrude(height = h, convexity = 4)
        kit_round2d(w, d, r);
}

// Hole centres at the 4 corners (inset — from edge to hole centre).
function kit_corner_points(w, d, inset) =
    [ [ w / 2 - inset,  d / 2 - inset],
      [-w / 2 + inset,  d / 2 - inset],
      [-w / 2 + inset, -d / 2 + inset],
      [ w / 2 - inset, -d / 2 + inset] ];
