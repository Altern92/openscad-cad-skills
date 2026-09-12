// DEFECT 3 -- two named sub-features overlapping INSIDE one part's own
// union(). Uncatchable by any other check: union() of two overlapping solids
// is still one valid, watertight, single-body shell, so connectivity and
// dimensions both stay clean. Reproduces INCIDENTS.md 2026-08-19 (a bearing
// tower overlapped an unrelated motor cradle by 419mm3 and survived several
// rounds of "all green" validation).
include <../params.scad>
// SUBFEATURES: tower, cradle
// EXPECTED_BBOX: [20, 20, 20]
module tower() { cube([10, 10, 20], center = true); }
module cradle() { cube([16, 8, 8], center = true); }
module part_geometry() { union() { tower(); cradle(); } }
SUBFEATURE = is_undef(SUBFEATURE) ? "" : SUBFEATURE;
module sf(name) { if (name == "tower") tower(); else if (name == "cradle") cradle(); }
if (SUBFEATURE != "") sf(SUBFEATURE); else part_geometry();
